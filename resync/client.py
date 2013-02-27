"""ResourceSync client implementation"""

import sys
import urllib
import os.path
import datetime
import distutils.dir_util 
import re
import time
import logging
import ConfigParser

from resync.resource_list_builder import ResourceListBuilder
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.capability_list import CapabilityList
from resync.capability_list_index import CapabilityListIndex
from resync.mapper import Mapper
from resync.sitemap import Sitemap
from resync.dump import Dump
from resync.resource import Resource
from resync.url_authority import UrlAuthority

class ClientFatalError(Exception):
    """Non-recoverable error in client, should include message to user"""
    pass

class Client(object):
    """Implementation of a ResourceSync client

    Logging is used for both console output and for detailed logs for
    automated analysis. Levels used:
      warning - usually shown to user
      info    - verbose output
      debug   - very verbose for automated analysis
    """

    def __init__(self, checksum=False, verbose=False, dryrun=False):
        super(Client, self).__init__()
        self.checksum = checksum
        self.verbose = verbose
        self.dryrun = dryrun
        self.logger = logging.getLogger('client')
        self.mapper = None
        self.resource_list_name = 'resourcelist.xml'
        self.change_list_name = 'changelist.xml'
        self.dump_format = None
        self.exclude_patterns = []
        self.sitemap_name = None
        self.allow_multifile = True
        self.noauth = False
        self.max_sitemap_entries = None
        self.ignore_failures = False
        self.status_file = '.resync-client-status.cfg'

    @property
    def mappings(self):
        """Provide access to mappings list within Mapper object"""
        if (self.mapper is None):
            raise ClientFatalError("No mappings specified")
        return(self.mapper.mappings)

    def set_mappings(self,mappings):
        """Build and set Mapper object based on input mappings"""
        self.mapper = Mapper(mappings)

    def sitemap_uri(self,basename):
        """Get full URI (filepath) for sitemap based on basename"""
        if (re.match(r"\w+:",basename)):
            # looks like URI
            return(basename)
        elif (re.match(r"/",basename)):
            # looks like full path
            return(basename)
        else:
            # build from mapping with name appended
            return(self.mappings[0].src_uri + '/' + basename)

    @property
    def sitemap(self):
        """Return the sitemap URI based on maps or explicit settings"""
        if (self.sitemap_name is not None):
            return(self.sitemap_name)
        return(self.sitemap_uri(self.resource_list_name))

    @property
    def resource_list(self):
        """Return resource_list on disk based on current mappings

        Return resource_list. Uses existing self.mapper settings.
        """
        ### 0. Sanity checks
        if (len(self.mappings)<1):
            raise ClientFatalError("No source to destination mapping specified")
        ### 1. Build from disk
        rlb = ResourceListBuilder(do_md5=self.checksum,mapper=self.mapper)
        rlb.add_exclude_files(self.exclude_patterns)
        return( rlb.from_disk() )

    def log_event(self, change):
        """Log a Resource object as an event for automated analysis"""
        self.logger.debug( "Event: "+repr(change) )

    def baseline_or_audit(self, allow_deletion=False, audit_only=False):
        """Baseline synchonization or audit

	Both functions implemented in this routine because audit is a prerequisite
	for a baseline sync.
	"""
        action = ( 'audit' if (audit_only) else 'baseline sync' ) 
        self.logger.debug("Starting "+action)
        ### 0. Sanity checks
        if (len(self.mappings)<1):
            raise ClientFatalError("No source to destination mapping specified")
        ### 1. Get inventories from both src and dst 
        # 1.a source resource_list
        try:
            self.logger.info("Reading sitemap %s" % (self.sitemap))
            src_resource_list = ResourceList(allow_multifile=self.allow_multifile, mapper=self.mapper)
            src_resource_list.read(uri=self.sitemap)
            self.logger.debug("Finished reading sitemap")
        except Exception as e:
            raise ClientFatalError("Can't read source resource_list from %s (%s)" % (self.sitemap,str(e)))
        self.logger.info("Read source resource_list, %d resources listed" % (len(src_resource_list)))
        if (len(src_resource_list)==0):
            raise ClientFatalError("Aborting as there are no resources to sync")
        if (self.checksum and not src_resource_list.has_md5()):
            self.checksum=False
            self.logger.info("Not calculating checksums on destination as not present in source resource_list")
        # 1.b destination resource_list mapped back to source URIs
        rlb = ResourceListBuilder(mapper=self.mapper)
        rlb.do_md5=self.checksum
        dst_resource_list = rlb.from_disk()
        ### 2. Compare these resource_lists respecting any comparison options
        (same,updated,deleted,created)=dst_resource_list.compare(src_resource_list)   
        ### 3. Report status and planned actions
        status = "  IN SYNC  "
        if (len(updated)>0 or len(deleted)>0 or len(created)>0):
            status = "NOT IN SYNC"
        self.logger.warning("Status: %s (same=%d, updated=%d, deleted=%d, created=%d)" %\
              (status,len(same),len(updated),len(deleted),len(created)))
        if (audit_only):
            self.logger.debug("Completed "+action)
            return
        ### 4. Check that sitemap has authority over URIs listed
        uauth = UrlAuthority(self.sitemap)
        for resource in src_resource_list:
            if (not uauth.has_authority_over(resource.uri)):
                if (self.noauth):
                    #self.logger.info("Sitemap (%s) mentions resource at a location it does not have authority over (%s)" % (self.sitemap,resource.uri))
                    pass
                else:
                    raise ClientFatalError("Aborting as sitemap (%s) mentions resource at a location it does not have authority over (%s), override with --noauth" % (self.sitemap,resource.uri))
        ### 5. Grab files to do sync
        for resource in updated:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            self.logger.info("updated: %s -> %s" % (uri,file))
            self.update_resource(resource,file,'updated')
        for resource in created:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            self.logger.info("created: %s -> %s" % (uri,file))
            self.update_resource(resource,file,'created')
        for resource in deleted:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            self.delete_resource(resource,file,allow_deletion)
        ### 6. For sync reset any incremental status for site
        if (not audit_only):
            #links = self.extract_links(src_resource_list)
            #if ('next' in links):
            #    self.write_incremental_status(self.sitemap,links['next'])
            #    self.logger.info("Written config with next incremental at %s" % (links['next']))
            #else:
                self.write_incremental_status(self.sitemap)
        self.logger.debug("Completed "+action)

    def incremental(self, allow_deletion=False, change_list_uri=None):
	"""Incremental synchronization"""
        self.logger.debug("Starting incremental sync")
        ### 0. Sanity checks
        if (len(self.mappings)<1):
            raise ClientFatalError("No source to destination mapping specified")
        # Get current config
        inc_config_next=self.read_incremental_status(self.sitemap)
        ### 1. Get URI of change_list, from sitemap or explicit
        if (inc_config_next is not None):
            # We have config from last run for this site
            change_list = inc_config_next
            self.logger.info("ChangeList location from last incremental run %s" % (change_list))
        elif (change_list_uri):
            # Translate as necessary using maps
            change_list = self.sitemap_uri(change_list_uri)
        else:
            # Get sitemap
            try:
                self.logger.info("Reading sitemap %s" % (self.sitemap))
                src_resource_list = ResourceList(allow_multifile=self.allow_multifile, mapper=self.mapper)
                src_resource_list.read(uri=self.sitemap, index_only=True)
                self.logger.debug("Finished reading sitemap/sitemapindex")
            except Exception as e:
                raise ClientFatalError("Can't read source sitemap from %s (%s)" % (self.sitemap,str(e)))
            # Extract change_list location
            # FIXME - need to completely rework the way we handle/store links
            #links = self.extract_links(src_resource_list)
            #if ('current' not in links):
            #    raise ClientFatalError("Failed to extract change_list location from sitemap %s" % (self.sitemap))
            #change_list = links['current']
        ### 2. Read change_list from source
        try:
            self.logger.info("Reading change_list %s" % (change_list))
            src_change_list = ChangeList()
            src_change_list.read(uri=change_list)
            self.logger.debug("Finished reading change_list")
        except Exception as e:
            raise ClientFatalError("Can't read source change_list from %s (%s)" % (change_list,str(e)))
        self.logger.info("Read source change_list, %d resources listed" % (len(src_change_list)))
        #if (len(src_change_list)==0):
        #    raise ClientFatalError("Aborting as there are no resources to sync")
        if (self.checksum and not src_change_list.has_md5()):
            self.checksum=False
            self.logger.info("Not calculating checksums on destination as not present in source resource_list")
        ### 3. Check that sitemap has authority over URIs listed
        # FIXME - What does authority mean for change_list? Here use both the
        # change_list URI and, if we used it, the sitemap URI
        uauth_cs = UrlAuthority(change_list)
        if (not change_list_uri):
            uauth_sm = UrlAuthority(self.sitemap)
        for resource in src_change_list:
            if (not uauth_cs.has_authority_over(resource.uri) and 
                (change_list_uri or not uauth_sm.has_authority_over(resource.uri))):
                if (self.noauth):
                    #self.logger.info("ChangeList (%s) mentions resource at a location it does not have authority over (%s)" % (change_list,resource.uri))
                    pass
                else:
                    raise ClientFatalError("Aborting as change_list (%s) mentions resource at a location it does not have authority over (%s), override with --noauth" % (change_list,resource.uri))
        ### 3. Apply changes
        num_updated = 0
        num_deleted = 0
        num_created = 0
        for resource in src_change_list:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            if (resource.change == 'updated'):
                self.logger.info("updated: %s -> %s" % (uri,file))
                self.update_resource(resource,file,'updated')
                num_updated+=1
            elif (resource.change == 'created'):
                self.logger.info("created: %s -> %s" % (uri,file))
                self.update_resource(resource,file,'created')
                num_created+=1
            elif (resource.change == 'deleted'):
                self.delete_resource(resource,file,allow_deletion)
                num_deleted+=1
            else:
                raise ClientError("Unknown change type %s" % (resource.change) )
        # 4. Report status and planned actions
        status = "NO CHANGES"
        if ((num_updated+num_deleted+num_created)>0):
            status = " CHANGES  "
        self.logger.warning("Status: %s (updated=%d, deleted=%d, created=%d)" %\
              (status,num_updated,num_deleted,num_created))
        # 5. Store next link if available
        if ((num_updated+num_deleted+num_created)>0):
            pass
            #links = self.extract_links(src_change_list)
            #if ('next' in links):
            #    self.write_incremental_status(self.sitemap,links['next'])
            #    self.logger.info("Written config with next incremental at %s" % (links['next']))
            #else:
            #    self.logger.warning("Failed to extract next change_list location from change_list %s" % (change_list))
        # 6. Done
        self.logger.debug("Completed incremental sync")

    def update_resource(self, resource, file, change=None):
        """Update resource from uri to file on local system

        Update means two things:
        1. GET resources
        2. set mtime in local time to be equal to timestamp in UTC (should perhaps
        or at least warn if different from LastModified from the GET response instead 
        but maybe warn if different (or just earlier than) the lastmod we expected 
        from the resource_list
        """
        path = os.path.dirname(file)
        distutils.dir_util.mkpath(path)
        if (self.dryrun):
            self.logger.info("dryrun: would GET %s --> %s" % (resource.uri,file))
        else:
            try:
                urllib.urlretrieve(resource.uri,file)
            except IOError as e:
                msg = "Failed to GET %s -- %s" % (resource.uri,str(e))
                if (self.ignore_failures):
                    self.logger.warning(msg)
                    return
                else:
                    raise ClientFatalError(msg)
            # sanity check
            length = os.stat(file).st_size
            if (resource.length != length):
                self.logger.info("Downloaded size for %s of %d bytes does not match expected %d bytes" % (resource.uri,length,resource.length))
            # set timestamp if we have one
            if (resource.timestamp is not None):
                unixtime = int(resource.timestamp) #no fractional
                os.utime(file,(unixtime,unixtime))
            self.log_event(Resource(resource=resource, change=change))

    def delete_resource(self, resource, file, allow_deletion=False):
        """Delete copy of resource in file on local system
        """
        uri = resource.uri
        if (allow_deletion):
            if (self.dryrun):
                self.logger.info("dryrun: would delete %s -> %s" % (uri,file))
            else:
                try:
                    os.unlink(file)
                except OSError as e:
                    msg = "Failed to DELETE %s -> %s : %s" % (uri,file,str(e))
                    if (self.ignore_failures):
                        self.logger.warning(msg)
                        return
                    else:
                        raise ClientFatalError(msg)
                self.logger.info("deleted: %s -> %s" % (uri,file))
                self.log_event(Resource(resource=resource, change="deleted"))
        else:
            self.logger.info("nodelete: would delete %s (--delete to enable)" % uri)

    def parse_document(self):
        """Parse any ResourceSync document and show information
        
        Will use sitemap URI taken either from explicit self.sitemap_name
        or derived from the mappings supplied.
        """
        s=Sitemap()
        self.logger.info("Reading sitemap(s) from %s ..." % (self.sitemap))
        try:
            list = s.parse_xml(urllib.urlopen(self.sitemap))
        except IOError as e:
            raise ClientFatalError("Cannot read document (%s)" % str(e))
        num_entries = len(list.resources)
        capability = '(unknown capability)'
        if ('capability' in list.md):
            capability = list.md['capability']
        print "Parsed %s document with %d entries" % (capability,num_entries)
        if (self.verbose):
            to_show = 100
            override_str = ' (override with --max-sitemap-entries)'
            if (self.max_sitemap_entries):
                to_show = self.max_sitemap_entries
                override_str = ''
            if (num_entries>to_show):
                print "Showing first %d entries sorted by URI%s..." % (to_show,override_str)
            n=0
            for resource in list:
                print '[%d] %s' % (n,str(resource))
                n+=1
                if ( n >= to_show ):
                    break


    def write_resource_list(self,outfile=None,links=None,dump=None):
        """Write a resource list sitemap for files on local disk
        based on the base_path->base_uri mappings.
        """
        rl = self.resource_list
        rl.ln = links
        kwargs = { 'pretty_xml': True,
                   'allow_multifile': self.allow_multifile,
                   'mapper' : self.mapper }
        if (self.max_sitemap_entries is not None):
            kwargs['max_sitemap_entries'] = self.max_sitemap_entries
        if (outfile is None):
            print rl.as_xml(**kwargs)
        else:
            rl.write(basename=outfile,**kwargs)
        self.write_dump_if_requested(rl,dump)

    def write_change_list(self,outfile=None,ref_sitemap=None,newref_sitemap=None,
                          empty=None,links=None,dump=None):
        cl = ChangeList(ln=links)
        if (not empty):
            # 1. Get and parse reference sitemap
            old_rl = self.read_reference_resource_list(ref_sitemap)
            # 2. Depending on whether a newref_sitemap was specified, either read that 
            # or build resource_list from files on disk
            if (newref_sitemap is None):
                # Get resource list from disk
                new_rl = self.resource_list
            else:
                new_rl = self.read_reference_resource_list(newref_sitemap,name='new reference')
            # 3. Calculate change list
            (same,updated,deleted,created)=old_rl.compare(new_rl)   
            cl.add_changed_resources( updated, change='updated' )
            cl.add_changed_resources( deleted, change='deleted' )
            cl.add_changed_resources( created, change='created' )
        # 4. Write out change list
        kwargs = { 'pretty_xml': True,
                   'mapper' : self.mapper }
        if (self.max_sitemap_entries is not None):
            kwargs['max_sitemap_entries'] = self.max_sitemap_entries
        if (outfile is None):
            print cl.as_xml(**kwargs)
        else:
            cl.write(basename=outfile,**kwargs)
        self.write_dump_if_requested(cl,dump)


    def write_capability_list(self,capabilities=None,outfile=None,links=None):
        """Write a Capability List to outfile or STDOUT"""
        capl = CapabilityList(ln=links)
        if (capabilities is not None):
            for name in capabilities.keys():
                capl.add_capability(name=name, uri=capabilities[name])
        kwargs = { 'pretty_xml': True }
        if (outfile is None):
            print capl.as_xml(**kwargs)
        else:
            capl.write(basename=outfile,**kwargs)


    def write_capability_list_index(self,capability_lists=None,outfile=None,links=None):
        """Write a Capability List to outfile or STDOUT"""
        capli = CapabilityListIndex(ln=links)
        if (capability_lists is not None):
            for uri in capability_lists:
                capli.add_capability_list(uri)
        kwargs = { 'pretty_xml': True }
        if (outfile is None):
            print capli.as_xml(**kwargs)
        else:
            capli.write(basename=outfile,**kwargs)


    def write_dump_if_requested(self,resource_list,dump):
        if (dump is None):
            return
        self.logger.info("Writing dump to %s..." % (dump))
        d = Dump(format=self.dump_format)
        d.write(resource_list=resource_list,dumpfile=dump)


    def read_reference_resource_list(self,ref_sitemap,name='reference'):
        """Read reference resource list and return the ResourceList object

        name parameter just uses in output messages to say what type
        of resource list is being read.
        """
        rl = ResourceList()
        self.logger.info("Reading %s sitemap(s) from %s ..." % (name,ref_sitemap))
        rl.read(uri=ref_sitemap,allow_multifile=self.allow_multifile, mapper=self.mapper)
        num_entries = len(rl.resources)
        self.logger.info("Read %s resource list with %d entries in %d sitemaps" % (name,num_entries,rl.num_files))
        if (self.verbose):
            to_show = 100
            override_str = ' (override with --max-sitemap-entries)'
            if (self.max_sitemap_entries):
                to_show = self.max_sitemap_entries
                override_str = ''
            if (num_entries>to_show):
                print "Showing first %d entries sorted by URI%s..." % (to_show,override_str)
            n=0
            for r in rl.resources:
                print r
                n+=1
                if ( n >= to_show ):
                    break
        return(rl)


    def write_incremental_status(self,site,next=None):
        """Write status dict to client status file
        
        FIXME - should have some file lock to avoid race
        """
        parser = ConfigParser.SafeConfigParser()
        parser.read(self.status_file)
        status_section = 'incremental'
        if (not parser.has_section(status_section)):
            parser.add_section(status_section)
        if (next is None):
            parser.remove_option(status_section, self.config_site_to_name(site))
        else:
            parser.set(status_section, self.config_site_to_name(site), next)
        with open(self.status_file, 'wb') as configfile:
            parser.write(configfile)
            configfile.close()

    def read_incremental_status(self,site):
        """Read client status file and return dict"""
        parser = ConfigParser.SafeConfigParser()
        status_section = 'incremental'
        parser.read(self.status_file)
        next = None
        try:
            next = parser.get(status_section,self.config_site_to_name(site))
        except ConfigParser.NoSectionError as e:
            pass
        except ConfigParser.NoOptionError as e:
            pass
        return(next)

    def config_site_to_name(self, name):
        return( re.sub(r"[^\w]",'_',name) )

if __name__ == '__main__':
    main()
