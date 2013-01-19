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

from resync.resourcelist_builder import ResourceListBuilder
from resync.resourcelist import ResourceList
from resync.changelist import ChangeList
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
        self.resourcelist_name = 'resourcelist.xml'
        self.dump_format = None
        self.exclude_patterns = []
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

    def sitemap_changelist_uri(self,basename):
        """Get full URI (filepath) for sitemap/changelist based on basename"""
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
        return(self.sitemap_changelist_uri(self.resourcelist_name))

    @property
    def resourcelist(self):
        """Return resourcelist on disk based on current mappings

        Return resourcelist. Uses existing self.mapper settings.
        """
        ### 0. Sanity checks
        if (len(self.mappings)<1):
            raise ClientFatalError("No source to destination mapping specified")
        ### 1. Build from disk
        ib = ResourceListBuilder(do_md5=self.checksum,mapper=self.mapper)
        ib.add_exclude_files(self.exclude_patterns)
        return( ib.from_disk() )

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
        # 1.a source resourcelist
        ib = ResourceListBuilder(mapper=self.mapper)
        try:
            self.logger.info("Reading sitemap %s" % (self.sitemap))
            src_sitemap = Sitemap(allow_multifile=self.allow_multifile, mapper=self.mapper)
            src_resourcelist = src_sitemap.read(uri=self.sitemap)
            self.logger.debug("Finished reading sitemap")
        except Exception as e:
            raise ClientFatalError("Can't read source resourcelist from %s (%s)" % (self.sitemap,str(e)))
        self.logger.info("Read source resourcelist, %d resources listed" % (len(src_resourcelist)))
        if (len(src_resourcelist)==0):
            raise ClientFatalError("Aborting as there are no resources to sync")
        if (self.checksum and not src_resourcelist.has_md5()):
            self.checksum=False
            self.logger.info("Not calculating checksums on destination as not present in source resourcelist")
        # 1.b destination resourcelist mapped back to source URIs
        ib.do_md5=self.checksum
        dst_resourcelist = ib.from_disk()
        ### 2. Compare these resourcelists respecting any comparison options
        (same,updated,deleted,created)=dst_resourcelist.compare(src_resourcelist)   
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
        for resource in src_resourcelist:
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
            links = self.extract_links(src_resourcelist)
            if ('next' in links):
                self.write_incremental_status(self.sitemap,links['next'])
                self.logger.info("Written config with next incremental at %s" % (links['next']))
            else:
                self.write_incremental_status(self.sitemap)
        self.logger.debug("Completed "+action)

    def incremental(self, allow_deletion=False, changelist_uri=None):
	"""Incremental synchronization"""
        self.logger.debug("Starting incremental sync")
        ### 0. Sanity checks
        if (len(self.mappings)<1):
            raise ClientFatalError("No source to destination mapping specified")
        # Get current config
        inc_config_next=self.read_incremental_status(self.sitemap)
        ### 1. Get URI of changelist, from sitemap or explicit
        if (inc_config_next is not None):
            # We have config from last run for this site
            changelist = inc_config_next
            self.logger.info("ChangeList location from last incremental run %s" % (changelist))
        elif (changelist_uri):
            # Translate as necessary using maps
            changelist = self.sitemap_changelist_uri(changelist_uri)
        else:
            # Get sitemap
            try:
                self.logger.info("Reading sitemap %s" % (self.sitemap))
                src_sitemap = Sitemap(allow_multifile=self.allow_multifile, mapper=self.mapper)
                src_resourcelist = src_sitemap.read(uri=self.sitemap, index_only=True)
                self.logger.debug("Finished reading sitemap/sitemapindex")
            except Exception as e:
                raise ClientFatalError("Can't read source sitemap from %s (%s)" % (self.sitemap,str(e)))
            # Extract changelist location
            # FIXME - need to completely rework the way we handle/store capabilities
            links = self.extract_links(src_resourcelist)
            if ('current' not in links):
                raise ClientFatalError("Failed to extract changelist location from sitemap %s" % (self.sitemap))
            changelist = links['current']
        ### 2. Read changelist from source
        ib = ResourceListBuilder(mapper=self.mapper)
        try:
            self.logger.info("Reading changelist %s" % (changelist))
            src_sitemap = Sitemap(allow_multifile=self.allow_multifile, mapper=self.mapper)
            src_changelist = src_sitemap.read(uri=changelist, changelist=True)
            self.logger.debug("Finished reading changelist")
        except Exception as e:
            raise ClientFatalError("Can't read source changelist from %s (%s)" % (changelist,str(e)))
        self.logger.info("Read source changelist, %d resources listed" % (len(src_changelist)))
        #if (len(src_changelist)==0):
        #    raise ClientFatalError("Aborting as there are no resources to sync")
        if (self.checksum and not src_changelist.has_md5()):
            self.checksum=False
            self.logger.info("Not calculating checksums on destination as not present in source resourcelist")
        ### 3. Check that sitemap has authority over URIs listed
        # FIXME - What does authority mean for changelist? Here use both the
        # changelist URI and, if we used it, the sitemap URI
        uauth_cs = UrlAuthority(changelist)
        if (not changelist_uri):
            uauth_sm = UrlAuthority(self.sitemap)
        for resource in src_changelist:
            if (not uauth_cs.has_authority_over(resource.uri) and 
                (changelist_uri or not uauth_sm.has_authority_over(resource.uri))):
                if (self.noauth):
                    #self.logger.info("ChangeList (%s) mentions resource at a location it does not have authority over (%s)" % (changelist,resource.uri))
                    pass
                else:
                    raise ClientFatalError("Aborting as changelist (%s) mentions resource at a location it does not have authority over (%s), override with --noauth" % (changelist,resource.uri))
        ### 3. Apply changes
        num_updated = 0
        num_deleted = 0
        num_created = 0
        for resource in src_changelist:
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
            links = self.extract_links(src_changelist)
            if ('next' in links):
                self.write_incremental_status(self.sitemap,links['next'])
                self.logger.info("Written config with next incremental at %s" % (links['next']))
            else:
                self.logger.warning("Failed to extract next changelist location from changelist %s" % (changelist))
        # 6. Done
        self.logger.debug("Completed incremental sync")

    def update_resource(self, resource, file, change=None):
        """Update resource from uri to file on local system

        Update means two things:
        1. GET resources
        2. set mtime in local time to be equal to timestamp in UTC (should perhaps
        or at least warn if different from LastModified from the GET response instead 
        but maybe warn if different (or just earlier than) the lastmod we expected 
        from the resourcelist
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
            size = os.stat(file).st_size
            if (resource.size != size):
                self.logger.info("Downloaded size for %s of %d bytes does not match expected %d bytes" % (resource.uri,size,resource.size))
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

    def parse_sitemap(self):
        s=Sitemap(allow_multifile=self.allow_multifile)
        self.logger.info("Reading sitemap(s) from %s ..." % (self.sitemap))
        i = s.read(self.sitemap)
        num_entries = len(i)
        self.logger.warning("Read sitemap with %d entries in %d sitemaps" % (num_entries,s.sitemaps_created))
        if (self.verbose):
            to_show = 100
            override_str = ' (override with --max-sitemap-entries)'
            if (self.max_sitemap_entries):
                to_show = self.max_sitemap_entries
                override_str = ''
            if (num_entries>to_show):
                print "Showing first %d entries sorted by URI%s..." % (to_show,override_str)
            n=0
            for r in i:
                print r
                n+=1
                if ( n >= to_show ):
                    break

    def explore_links(self):
        """Explore links from sitemap and between changelists"""
        seen = dict()
        is_changelist,links = self.explore_links_get(self.sitemap, seen=seen)
        starting_changelist = self.sitemap
        if (not is_changelist):
            if ('current' in links):
                starting_changelist = links['current']
                is_changelist,links = self.explore_links_get(links['current'], seen=seen)
        # Can we go backward?
        if ('prev' in links and not links['prev'] in seen):
            self.logger.warning("Will follow links backwards...")
            while ('prev' in links and not links['prev'] in seen):
                self.logger.warning("Following \"prev\" link")
                is_changelist,links = self.explore_links_get(links['prev'], seen=seen)
        else:
            self.logger.warning("No links backwards")
        # Can we go forward?
        links = seen[starting_changelist]
        if ('next' in links and not links['next'] in seen):
            self.logger.warning("Will follow links forwards...")
            while ('next' in links and not links['next'] in seen):
                self.logger.warning("Following \"next\" link")
                is_changelist,links = self.explore_links_get(links['next'], seen=seen)
        else:
            self.logger.warning("No links forwards")

    def explore_links_get(self, uri, seen=[]):
        # Check we haven't been here before
        if (uri in seen):
            self.logger.warning("Already see %s, skipping" % (uri))
        s=Sitemap(allow_multifile=self.allow_multifile)
        self.logger.info("Reading sitemap from %s ..." % (uri))
        i = s.read(uri, index_only=True)
        self.logger.warning("Read %s from %s" % (s.read_type,uri))
        links = self.extract_links(i, verbose=True)
        if ('next' in links and links['next']==uri):
            self.logger.warning("- self reference \"next\" link")
        seen[uri]=links
        return(s.changelist_read,links)

    def write_sitemap(self,outfile=None,capabilities=None,dump=None):
        # Set up base_path->base_uri mappings, get resourcelist from disk
        i = self.resourcelist
        i.capabilities = capabilities
        s=Sitemap(pretty_xml=True, allow_multifile=self.allow_multifile, mapper=self.mapper)
        if (self.max_sitemap_entries is not None):
            s.max_sitemap_entries = self.max_sitemap_entries
        if (outfile is None):
            print s.resources_as_xml(i,capabilities=i.capabilities)
        else:
            s.write(i,basename=outfile)
        self.write_dump_if_requested(i,dump)

    def changelist_sitemap(self,outfile=None,ref_sitemap=None,newref_sitemap=None,
                          empty=None,capabilities=None,dump=None):
        changelist = ChangeList()
        changelist.capabilities = capabilities
        if (not empty):
            # 1. Get and parse reference sitemap
            old_inv = self.read_reference_sitemap(ref_sitemap)
            # 2. Depending on whether a newref_sitemap was specified, either read that 
            # or build resourcelist from files on disk
            if (newref_sitemap is None):
                # Get resourcelist from disk
                new_inv = self.resourcelist
            else:
                new_inv = self.read_reference_sitemap(newref_sitemap,name='new reference')
            # 3. Calculate changelist
            (same,updated,deleted,created)=old_inv.compare(new_inv)   
            changelist.add_changed_resources( updated, change='updated' )
            changelist.add_changed_resources( deleted, change='deleted' )
            changelist.add_changed_resources( created, change='created' )
        # 4. Write out changelist
        s = Sitemap(pretty_xml=True, allow_multifile=self.allow_multifile, mapper=self.mapper)
        if (self.max_sitemap_entries is not None):
            s.max_sitemap_entries = self.max_sitemap_entries
        if (outfile is None):
            print s.resources_as_xml(changelist,changelist=True)
        else:
            s.write(changelist,basename=outfile,changelist=True)
        self.write_dump_if_requested(changelist,dump)

    def write_dump_if_requested(self,resourcelist,dump):
        if (dump is None):
            return
        self.logger.info("Writing dump to %s..." % (dump))
        d = Dump(format=self.dump_format)
        d.write(resourcelist=resourcelist,dumpfile=dump)

    def read_reference_sitemap(self,ref_sitemap,name='reference'):
        """Read reference sitemap and return the resourcelist

        name parameter just uses in output messages to say what type
        of sitemap is being read.
        """
        sitemap = Sitemap(allow_multifile=self.allow_multifile, mapper=self.mapper)
        self.logger.info("Reading %s sitemap(s) from %s ..." % (name,ref_sitemap))
        i = sitemap.read(ref_sitemap)
        num_entries = len(i)
        self.logger.warning("Read %s sitemap with %d entries in %d sitemaps" % (name,num_entries,sitemap.sitemaps_created))
        if (self.verbose):
            to_show = 100
            override_str = ' (override with --max-sitemap-entries)'
            if (self.max_sitemap_entries):
                to_show = self.max_sitemap_entries
                override_str = ''
            if (num_entries>to_show):
                print "Showing first %d entries sorted by URI%s..." % (to_show,override_str)
            n=0
            for r in i:
                print r
                n+=1
                if ( n >= to_show ):
                    break
        return(i)

    def extract_links(self, rc, verbose=False):
        """Extract links from capabilities resourcelist or changelist

        FIXME - when we finalize the form of links this should probably
        go along with other capabilities functions somewhere general.
        """
        links = dict()
        for href in rc.capabilities.keys():
            atts = rc.capabilities[href].get('attributes')
            self.logger.debug("Capability: %s" % (str(rc.capabilities[href])))
            if (atts is not None):
                # split on spaces, check is changelist rel and diraction
                if ('http://www.openarchives.org/rs/changelist' in atts):
                    for linktype in ['next','prev','current']:
                        if (linktype in atts):
                            if (linktype in links):
                                raise ClientFatalError("Duplicate link type %s, links to %s and %s" % (linktype,links[linktype],href))
                            links[linktype] = href;
                            if (verbose):
                                self.logger.warning("- got \"%s\" link to %s" % (linktype,href))
        return(links) 

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
