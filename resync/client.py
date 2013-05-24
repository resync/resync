"""ResourceSync client implementation"""

import sys
import urllib
import urlparse
import os.path
import datetime
import distutils.dir_util 
import re
import time
import logging
import requests

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
from resync.utils import compute_md5_for_file
from resync.client_state import ClientState
from w3c_datetime import str_to_datetime,datetime_to_str

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
        self.mapper = Mapper()
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
        self.pretty_xml = True

    def set_mappings(self,mappings):
        """Build and set Mapper object based on input mappings"""
        self.mapper = Mapper(mappings, use_default_path=True)

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
            return(self.mapper.default_src_uri() + '/' + basename)

    @property
    def sitemap(self):
        """Return the sitemap URI based on maps or explicit settings"""
        if (self.sitemap_name is not None):
            return(self.sitemap_name)
        return(self.sitemap_uri(self.resource_list_name))

    def build_resource_list(self, paths=None):
        """Return a resource list for files on local disk

        The set of files is taken by disk scan from the paths specified or
        else defaults to the paths specified in the current mappings

        Return resource_list. Uses existing self.mapper settings.
        """
        # 0. Sanity checks, parse paths is specified
        if (len(self.mapper)<1):
            raise ClientFatalError("No source to destination mapping specified")
        if (paths is not None):
            # Expect comma separated list of paths
            paths=paths.split(',')
        # 1. Build from disk
        rlb = ResourceListBuilder(set_md5=self.checksum,mapper=self.mapper)
        rlb.add_exclude_files(self.exclude_patterns)
        rl = rlb.from_disk(paths=paths)
        # 2. Set defaults and overrides
        rl.allow_multifile = self.allow_multifile
        rl.pretty_xml = self.pretty_xml
        rl.mapper = self.mapper
        if (self.max_sitemap_entries is not None):
            rl.max_sitemap_entries = self.max_sitemap_entries
        return(rl)

    def log_event(self, change):
        """Log a Resource object as an event for automated analysis"""
        self.logger.debug( "Event: "+repr(change) )

    def baseline_or_audit(self, allow_deletion=False, audit_only=False):
        """Baseline synchonization or audit

	Both functions implemented in this routine because audit is a prerequisite
	for a baseline sync. In the case of baseline sync the last timestamp seen
        is recorded as client state.
	"""
        action = ( 'audit' if (audit_only) else 'baseline sync' ) 
        self.logger.debug("Starting "+action)
        ### 0. Sanity checks
        if (len(self.mapper)<1):
            raise ClientFatalError("No source to destination mapping specified")
        if (not audit_only and self.mapper.unsafe()):
            raise ClientFatalError("Source to destination mappings unsafe: %s" % str(self.mapper))
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
        rlb = ResourceListBuilder(set_md5=self.checksum, mapper=self.mapper)
        dst_resource_list = rlb.from_disk()
        ### 2. Compare these resource_lists respecting any comparison options
        (same,updated,deleted,created)=dst_resource_list.compare(src_resource_list)   
        ### 3. Report status and planned actions
        self.log_status(in_sync=(len(updated)+len(deleted)+len(created)==0),
                        audit=True,same=len(same),created=len(created),
                        updated=len(updated),deleted=len(deleted))
        if (audit_only or len(created)+len(updated)+len(deleted)==0):
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
        delete_msg = (", and delete %d resources" % len(deleted)) if (allow_deletion) else ''
        self.logger.warning("Will GET %d resources%s" % (len(created)+len(updated),delete_msg))
        self.last_timestamp = 0
        num_created=0
        num_updated=0
        num_deleted=0
        for resource in created:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            self.logger.info("created: %s -> %s" % (uri,file))
            num_created+=self.update_resource(resource,file,'created')
        for resource in updated:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            self.logger.info("updated: %s -> %s" % (uri,file))
            num_updated+=self.update_resource(resource,file,'updated')
        for resource in deleted:
            uri = resource.uri
            file = self.mapper.src_to_dst(uri)
            num_deleted+=self.delete_resource(resource,file,allow_deletion)
        ### 6. Store last timestamp to allow incremental sync
        if (not audit_only and self.last_timestamp>0):
            ClientState().set_state(self.sitemap,self.last_timestamp)
            self.logger.info("Written last timestamp %s for incremental sync" % (datetime_to_str(self.last_timestamp)))
        ### 7. Done
        self.log_status(in_sync=(len(updated)+len(deleted)+len(created)==0),
                        same=len(same),created=num_created,
                        updated=num_updated,deleted=num_deleted)
        self.logger.debug("Completed %s" % (action))

    def incremental(self, allow_deletion=False, change_list_uri=None, from_datetime=None):
	"""Incremental synchronization

        """
        self.logger.debug("Starting incremental sync")
        ### 0. Sanity checks
        if (len(self.mapper)<1):
            raise ClientFatalError("No source to destination mapping specified")
        if (self.mapper.unsafe()):
            raise ClientFatalError("Source to destination mappings unsafe: %s" % str(self.mapper))
        from_timestamp = None
        if (from_datetime is not None):
            try:
                from_timestamp = str_to_datetime(from_datetime)
            except ValueError:
                raise ClientFatalError("Bad datetime in --from (%s)" % from_datetime)
        ### 1. Work out where to start from
        if (from_timestamp is None):
            from_timestamp=ClientState().get_state(self.sitemap)
            if (from_timestamp is None):
                raise ClientFatalError("No stored timestamp for this site, and no explicit --from")
        ### 2. Get URI of change list, from sitemap or explicit
        if (change_list_uri):
            # Translate as necessary using maps
            change_list = self.sitemap_uri(change_list_uri)
        else:
            # Try default name
            change_list = self.sitemap_uri(self.change_list_name)
        ### 3. Read change list from source
        try:
            self.logger.info("Reading change list %s" % (change_list))
            src_change_list = ChangeList()
            src_change_list.read(uri=change_list)
            self.logger.debug("Finished reading change list")
        except Exception as e:
            raise ClientFatalError("Can't read source change list from %s (%s)" % (change_list,str(e)))
        self.logger.info("Read source change list, %d changes listed" % (len(src_change_list)))
        #if (len(src_change_list)==0):
        #    raise ClientFatalError("Aborting as there are no resources to sync")
        if (self.checksum and not src_change_list.has_md5()):
            self.checksum=False
            self.logger.info("Not calculating checksums on destination as not present in source change list")
        # Check all changes have timestamp and record last
        self.last_timestamp = 0
        for resource in src_change_list:
            if (resource.timestamp is None):
                raise ClientFatalError("Aborting - missing timestamp for change in %s" % (uri))
            if (resource.timestamp > self.last_timestamp):
                self.last_timestamp = resource.timestamp
        ### 4. Check that the change list has authority over URIs listed
        # FIXME - What does authority mean for change list? Here use both the
        # change list URI and, if we used it, the sitemap URI
        uauth_cs = UrlAuthority(change_list)
        if (not change_list_uri):
            uauth_sm = UrlAuthority(self.sitemap)
        for resource in src_change_list:
            if (not uauth_cs.has_authority_over(resource.uri) and 
                (change_list_uri or not uauth_sm.has_authority_over(resource.uri))):
                if (self.noauth):
                    #self.logger.info("Change list (%s) mentions resource at a location it does not have authority over (%s)" % (change_list,resource.uri))
                    pass
                else:
                    raise ClientFatalError("Aborting as change list (%s) mentions resource at a location it does not have authority over (%s), override with --noauth" % (change_list,resource.uri))
        ### 5. Prune entries before starting timestamp and dupe changes for a resource
        num_skipped = src_change_list.prune_before(from_timestamp)
        if (num_skipped>0):
            self.logger.info("Skipped %d changes before %s" % (num_skipped,datetime_to_str(from_timestamp)))
        num_dupes = src_change_list.prune_dupes()
        if (num_dupes>0):
            self.logger.info("Removed %d prior changes" % (num_dupes))
        ### 6. Apply changes at same time or after from_timestamp
        self.logger.info("Applying %d changes" % (len(src_change_list)))
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
        ### 7. Report status and planned actions
        self.log_status(in_sync=((num_updated+num_deleted+num_created)==0),
                        incremental=True,created=num_created, updated=num_updated, 
                        deleted=num_deleted)
        ### 8. Record last timestamp we have seen
        if (self.last_timestamp>0):
            ClientState().set_state(self.sitemap,self.last_timestamp)
            self.logger.info("Written last timestamp %s for incremental sync" % (datetime_to_str(self.last_timestamp)))
        ### 9. Done
        self.logger.debug("Completed incremental sync")

    def update_resource(self, resource, file, change=None):
        """Update resource from uri to file on local system

        Update means three things:
        1. GET resources
        2. set mtime in local time to be equal to timestamp in UTC (should perhaps
        or at least warn if different from LastModified from the GET response instead 
        but maybe warn if different (or just earlier than) the lastmod we expected 
        from the resource_list
        3. check that resource matches expected information

        Also update self.last_timestamp if the timestamp (in source frame) of this
        resource is later and the current value.

        Returns the number of resources updated/created (0 or 1)
        """
        path = os.path.dirname(file)
        distutils.dir_util.mkpath(path)
        num_updated=0
        if (self.dryrun):
            self.logger.info("dryrun: would GET %s --> %s" % (resource.uri,file))
        else:
            # 1. GET
            try:
                urllib.urlretrieve(resource.uri,file)
                num_updated+=1
            except IOError as e:
                msg = "Failed to GET %s -- %s" % (resource.uri,str(e))
                if (self.ignore_failures):
                    self.logger.warning(msg)
                    return
                else:
                    raise ClientFatalError(msg)
            # 2. set timestamp if we have one
            if (resource.timestamp is not None):
                unixtime = int(resource.timestamp) #no fractional
                os.utime(file,(unixtime,unixtime))
                if (resource.timestamp > self.last_timestamp):
                    self.last_timestamp = resource.timestamp
            self.log_event(Resource(resource=resource, change=change))
            # 3. sanity check
            length = os.stat(file).st_size
            if (resource.length != length):
                self.logger.info("Downloaded size for %s of %d bytes does not match expected %d bytes" % (resource.uri,length,resource.length))
            if (self.checksum and resource.md5 is not None):
                file_md5 = compute_md5_for_file(file)
                if (resource.md5 != file_md5):
                    self.logger.info("MD5 mismatch for %s, got %s but expected %s bytes" % (resource.uri,file_md5,resource.md5))
        return(num_updated)

    def delete_resource(self, resource, file, allow_deletion=False):
        """Delete copy of resource in file on local system

        Will only actually do the deletion if allow_deletion is True. Regardless 
        of whether the deletion occurs, self.last_timestamp will be updated 
        if the resource.timestamp is later than the current value.

        Returns the number of files actually deleted (0 or 1).
        """
        num_deleted=0
        uri = resource.uri
        if (resource.timestamp is not None and
            resource.timestamp > self.last_timestamp):
            self.last_timestamp = resource.timestamp
        if (allow_deletion):
            if (self.dryrun):
                self.logger.info("dryrun: would delete %s -> %s" % (uri,file))
            else:
                try:
                    os.unlink(file)
                    num_deleted+=1
                except OSError as e:
                    msg = "Failed to DELETE %s -> %s : %s" % (uri,file,str(e))
                    #if (self.ignore_failures):
                    self.logger.warning(msg)
                    #    return
                    #else:
                    #    raise ClientFatalError(msg)
                self.logger.info("deleted: %s -> %s" % (uri,file))
                self.log_event(Resource(resource=resource, change="deleted"))
        else:
            self.logger.info("nodelete: would delete %s (--delete to enable)" % uri)
        return(num_deleted)

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

    def explore(self):
        """Explore capabilities of a server interactvely
        
        Will use sitemap URI taken either from explicit self.sitemap_name
        or derived from the mappings supplied.
        """
        uri = None
        if (self.sitemap_name is not None):
            uri = self.sitemap
            print "Taking location from --sitemap option"
            acceptable_capabilities = None #ie. any
        elif (len(self.mapper)>0):
            pu = urlparse.urlparse(self.mapper.default_src_uri())
            uri = urlparse.urlunparse( [ pu[0], pu[1], '/.well-known/resourcesync', '', '', '' ] )
            print "Will look for discovery information based on mappings"
            acceptable_capabilities = [ 'capabilitylist', 'capabilitylistindex' ]
        else:
            raise ClientFatalError("Neither explicit sitemap nor mapping specified")
        history = []
        inp = None
        checks = None
        while (inp!='q'):
            print
            if (inp=='b'):
                if (len(history)<2):
                    break #can't do this, exit
                history.pop() #throw away current
                uri=history.pop()
                acceptable_capabilities=None
            history.append(uri)
            (uri,checks,acceptable_capabilities,inp) = self.explore_uri(uri,checks,acceptable_capabilities,len(history)>1)
        print "--explore done, bye..."

    def explore_uri(self, uri, checks, caps, show_back=True):
        """Interactive exploration of document at uri

        Will flag warnings if the document is not of type listed in caps
        """
        s=Sitemap()
        print "Reading %s" % (uri)
        options={}
        capability=None
        try:
            if (caps=='resource'):
                self.explore_show_head(uri,check_headers=checks)
            else: 
                list = s.parse_xml(urllib.urlopen(uri))
                (options,capability)=self.explore_show_summary(list,s.parsed_index,caps)
        except IOError as e:
            print "Cannot read %s (%s)\nGoing back" % (uri,str(e))
            return('','','','b')
        except Exception as e:
            print "Cannot parse %s (%s)\nGoing back" % (uri,str(e))
            return('','','','b')
        while (True):
            # don't offer number option for no resources/capabilities
            num_prompt = '' if (len(options)==0) else 'number, '
            up_prompt = 'b(ack), ' if (show_back) else ''
            inp = raw_input( "Follow [%s%sq(uit)]?" % (num_prompt,up_prompt) )
            if (inp in options.keys()):
                break
            if (inp == 'q' or inp == 'b'):
                return('','','',inp)
        checks = {}
        if ( options[inp].capability is None ):
            if (capability == 'capabilitylistindex'):
                # all links should be to capabilitylist documents
                caps = ['capabilitylist']
            elif (capability in ['resourcelist','changelist',
                                 'resourcedump','changedump']):
                caps = 'resource'
        else:
            r = options[inp]
            caps = [r.capability]
            if (r.length is not None):
                checks['content-length']=r.length
            if (r.lastmod is not None):
                checks['last-modified']=r.lastmod
            # FIXME - could do sanity check here and issue warnings if odd
        return( options[inp].uri, checks, caps, inp )

    def explore_show_summary(self,list,parsed_index,caps):
        """Show summary of one capability document

        Used as part of --explore.
        FIXME - should look for <rs:ln rel="up"...> link and show that
        """
        num_entries = len(list.resources)
        capability = '(unknown capability)'
        if ('capability' in list.md):
            capability = list.md['capability']
        if (parsed_index):
            capability += 'index'
        print "Parsed %s document with %d entries:" % (capability,num_entries)
        if (caps is not None and capability not in caps):
            print "WARNING - expected a %s document" % (','.join(caps))
        to_show = num_entries
        if (num_entries>21):
            to_show = 20
        # What entries are allowed? 
        # FIXME - not complete
        entry_caps = []
        if (capability == 'capabilitylistindex'):
            entry_caps = ['capabilitylist']
        elif (capability == 'capabilitylist'):
            entry_caps = ['resourcelist','changelist','resourcedump','changedump','changelistindex']
        elif (capability == 'changelistindex'):
            entry_caps = ['changelist']
        options = {}
        n=0
        if ('up' in list.ln):
            options['up']=list.ln['up']
            print "[%s] %s" % ('up',list.ln['up'].uri)
        for r in list.resources:
            if (n>=to_show):
                print "(not showing remaining %d entries)" % (num_entries-n)
                break
            n+=1
            options[str(n)]=r
            print "[%d] %s" % (n,r.uri)
            if (r.capability is not None):
                warning = ''
                if (r.capability not in entry_caps):
                    warning = " (EXPECTED %s)" % (' or '.join(entry_caps))
                print "  %s%s" % (r.capability,warning)
            elif (len(entry_caps)==1):
                r.capability=entry_caps[0]
                print "  capability not specified, should be %s" % (r.capability)
        return(options,capability)

    def explore_show_head(self,uri,check_headers=None):
        """Do HEAD on uri and show infomation

        Will also check headers against any values specified in 
        check_headers.
        """
        print "HEAD %s" % (uri)
        response = requests.head(uri)
        print "  status: %s" % (response.status_code)
        # generate normalized lastmod
#        if ('last-modified' in response.headers):
#            response.headers.add['lastmod'] = datetime_to_str(str_to_datetime(response.headers['last-modified']))
        # print some of the headers
        for header in ['content-length','last-modified','lastmod','content-type','etag']:
            if header in response.headers:
                check_str=''
                if (check_headers is not None and
                    header in check_headers):
                    if (response.headers[header] == check_headers[header]):
                        check_str=' MATCHES EXPECTED VALUE'
                    else:
                        check_STR=' EXPECTED %s' % (check_headers[header])
                print "  %s: %s%s" % (header, response.headers[header], check_str)

    def write_resource_list(self,paths=None,outfile=None,links=None,dump=None):
        """Write a resource list sitemap for files on local disk

        Set of resources included is based on paths setting or else the mappings. 
        Optionally links can be added. Output will be to stdout unless outfile
        is specified.
        """
        rl = self.build_resource_list(paths=paths)
        if (links is not None):
            rl.ln = links
        if (outfile is None):
            print rl.as_xml()
        else:
            rl.write(basename=outfile)
        self.write_dump_if_requested(rl,dump)

    def write_change_list(self,paths=None,outfile=None,ref_sitemap=None,newref_sitemap=None,
                          empty=None,links=None,dump=None):
        """Write a change list
        
        Unless the both ref_sitemap and newref_sitemap are specified then the Change 
        List is calculated between the reference an the current state of files on
        disk. The files on disk are scanned based either on the paths setting or
        else on the mappings.
        """
        cl = ChangeList(ln=links)
        if (not empty):
            # 1. Get and parse reference sitemap
            old_rl = self.read_reference_resource_list(ref_sitemap)
            # 2. Depending on whether a newref_sitemap was specified, either read that 
            # or build resource_list from files on disk
            if (newref_sitemap is None):
                # Get resource list from disk
                new_rl = self.build_resource_list(paths=paths)
            else:
                new_rl = self.read_reference_resource_list(newref_sitemap,name='new reference')
            # 3. Calculate change list
            (same,updated,deleted,created)=old_rl.compare(new_rl)   
            cl.add_changed_resources( updated, change='updated' )
            cl.add_changed_resources( deleted, change='deleted' )
            cl.add_changed_resources( created, change='created' )
        # 4. Write out change list
        cl.mapper = self.mapper
        cl.pretty_xml = self.pretty_xml
        if (self.max_sitemap_entries is not None):
            cl.max_sitemap_entries = self.max_sitemap_entries
        if (outfile is None):
            print cl.as_xml()
        else:
            cl.write(basename=outfile)
        self.write_dump_if_requested(cl,dump)

    def write_capability_list(self,capabilities=None,outfile=None,links=None):
        """Write a Capability List to outfile or STDOUT"""
        capl = CapabilityList(ln=links)
        capl.pretty_xml = self.pretty_xml
        if (capabilities is not None):
            for name in capabilities.keys():
                capl.add_capability(name=name, uri=capabilities[name])
        if (outfile is None):
            print capl.as_xml()
        else:
            capl.write(basename=outfile)

    def write_capability_list_index(self,capability_lists=None,outfile=None,links=None):
        """Write a Capability List to outfile or STDOUT"""
        capli = CapabilityListIndex(ln=links)
        capli.pretty_xml = self.pretty_xml
        if (capability_lists is not None):
            for uri in capability_lists:
                capli.add_capability_list(uri)
        if (outfile is None):
            print capli.as_xml()
        else:
            capli.write(basename=outfile)

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
        self.logger.info("Reading reference %s resource list from %s ..." % (name,ref_sitemap))
        rl.mapper=self.mapper
        rl.read(uri=ref_sitemap,index_only=(not self.allow_multifile))
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

    def log_status(self, in_sync=True, incremental=False, audit=False,
                   same=None, created=0, updated=0, deleted=0):
        """Write log message regarding status in standard form
        
        Split this off so we messages from baseline/audit/incremental
        are written in a consistent form.
        """
        if (incremental):     
            status = "NO CHANGES" if in_sync else "CHANGES"
        else:
            status = "IN SYNC" if in_sync else ("NOT IN SYNC" if (audit) else "SYNCED")
        if (audit):
            words = { 'created': 'to create',
                      'updated': 'to update',
                      'deleted': 'to delete' }
        else:
            words = { 'created': 'created',
                      'updated': 'updated',
                      'deleted': 'deleted' }
        same =  "" if (same is None) else ("same=%d, " % same)
        self.logger.warning("Status: %11s (%s%s=%d, %s=%d, %s=%d)" %\
             (status, same, words['created'], created, 
              words['updated'], updated, words['deleted'], deleted))

if __name__ == '__main__':
    main()
