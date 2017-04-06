"""ResourceSync client implementation."""

import sys
try:  # python3
    from urllib.request import urlretrieve
    from urllib.parse import urlsplit, urlunsplit, urljoin
except ImportError:  # python2
    from urllib import urlretrieve
    from urlparse import urlsplit, urlunsplit, urljoin
import os.path
import datetime
import distutils.dir_util
import re
import time
import logging
import requests

from .resource_list_builder import ResourceListBuilder
from .resource_list import ResourceList
from .change_list import ChangeList
from .capability_list import CapabilityList
from .source_description import SourceDescription
from .mapper import Mapper
from .sitemap import Sitemap
from .dump import Dump
from .resource import Resource
from .url_authority import UrlAuthority
from .hashes import Hashes
from .client_state import ClientState
from .client_utils import ClientFatalError, ClientError, url_or_file_open
from .list_base_with_index import ListBaseIndexError
from .w3c_datetime import str_to_datetime, datetime_to_str


class Client(object):
    """Implementation of a ResourceSync client.

    Logging is used for both console output and for detailed logs for
    automated analysis. Levels used:
      warning - usually shown to user
      info    - verbose output
      debug   - very verbose for automated analysis
    """

    def __init__(self, hashes=None, verbose=False, dryrun=False):
        """Initialize Client object with default parameters."""
        self.hashes = set(hashes) if hashes else set()
        self.verbose = verbose
        self.dryrun = dryrun
        self.logger = logging.getLogger('resync.client')
        self.mapper = Mapper()
        self.resource_list_name = 'resourcelist.xml'
        self.change_list_name = 'changelist.xml'
        self.dump_format = None
        self.exclude_patterns = []
        self.sitemap_name = None
        self.allow_multifile = True
        self.noauth = False
        self.strictauth = False
        self.max_sitemap_entries = None
        self.ignore_failures = False
        self.pretty_xml = True
        self.fake_input = None
        # Default file names
        self.status_file = '.resync-client-status.cfg'
        self.default_resource_dump = 'resourcedump.zip'
        self.default_change_dump = 'changedump.zip'

    def set_mappings(self, mappings):
        """Build and set Mapper object based on input mappings."""
        self.mapper = Mapper(mappings, use_default_path=True)

    def sitemap_uri(self, basename):
        """Get full URI (filepath) for sitemap based on basename."""
        if (re.match(r"\w+:", basename)):
            # looks like URI
            return(basename)
        elif (re.match(r"/", basename)):
            # looks like full path
            return(basename)
        else:
            # build from mapping with name appended
            return(self.mapper.default_src_uri() + '/' + basename)

    @property
    def sitemap(self):
        """Return the sitemap URI based on maps or explicit settings."""
        if (self.sitemap_name is not None):
            return(self.sitemap_name)
        return(self.sitemap_uri(self.resource_list_name))

    def read_resource_list(self, uri):
        """Read resource list from specified URI else raise exception."""
        self.logger.info("Reading resource list %s" % (uri))
        try:
            resource_list = ResourceList(allow_multifile=self.allow_multifile,
                                         mapper=self.mapper)
            resource_list.read(uri=uri)
        except Exception as e:
            raise ClientFatalError(
                "Can't read source resource list from %s (%s)" %
                (uri, str(e)))
        self.logger.debug("Finished reading resource list")
        return(resource_list)

    def find_resource_list_from_source_description(self, uri):
        """Read source description to find resource list.

        Raises a ClientError in cases where the client might look for a
        source description in another location, but a ClientFatalError if
        a source description is found but there is some problem using it.
        """
        self.logger.info("Reading capability list %s" % (uri))
        try:
            sd = SourceDescription()
            sd.read(uri=uri)
        except Exception as e:
            raise ClientError(
                "Can't read source description from %s (%s)" %
                (uri, str(e)))
        if (len(sd) == 0):
            raise ClientFatalError(
                "Source description %s has no sources" % (uri))
        elif (len(sd) > 1):
            raise ClientFatalError(
                "Source description %s has multiple sources" % (uri))
        self.logger.info("Finished reading source description")
        raise ClientFatalError('debug')
        return(cl)

    def find_resource_list(self):
        """Look for resource list by hueristics.

        1. Use explicitly specified self.sitemap_name (and
            fail if that doesn't work)
        2. Look for base_url/.well-known/resourcesync (then look
            for capability, look for resourcelist)
        3. Look for host/.well-known/resourcesync (then look
            for capability, look for resourcelist)
        4. Look for base_url/resourcelist.xml
        5. Look for base_url/sitemap.xml
        6. Look for host/sitemap.xml
        """
        # 1
        if (self.sitemap_name is not None):
            return(self.read_resource_list(self.sitemap_name))
        # 2 & 3
        parts = urlsplit(self.sitemap)
        uri_host = urlunsplit([parts[0],parts[1],'','',''])
        for uri in [urljoin(self.sitemap, '.well-known/resourcesync'),
                    urljoin(uri_host, '.well-known/resourcesync')]:
            try:
                return(self.find_resource_list_from_source_description(uri))
            except ClientError as e:
                pass
        # 4, 5 & 6
        for uri in [urljoin(self.sitemap, 'resourcelist.xml'),
                    urljoin(self.sitemap, 'sitemap.xml'),
                    urljoin(uri_host, 'sitemap.xml')]:
            try:
                return(self.read_resource_list(uri))
            except ClientError as e:
                pass
        raise ClientFatalError(
                "Failed to find source resource list from common patterns")

    def build_resource_list(self, paths=None, set_path=False):
        """Return a resource list for files on local disk.

        The set of files is taken by disk scan from the paths specified or
        else defaults to the paths specified in the current mappings

        paths - override paths from mappings if specified

        set_path - set true to set the path information for each resource
            included. This is used to build a resource list as the basis
            for creating a dump.

        Return ResourceList. Uses existing self.mapper settings.
        """
        # 0. Sanity checks, parse paths is specified
        if (len(self.mapper) < 1):
            raise ClientFatalError(
                "No source to destination mapping specified")
        if (paths is not None):
            # Expect comma separated list of paths
            paths = paths.split(',')
        # 1. Build from disk
        rlb = ResourceListBuilder(set_hashes=self.hashes, mapper=self.mapper)
        rlb.set_path = set_path
        try:
            rlb.add_exclude_files(self.exclude_patterns)
            rl = rlb.from_disk(paths=paths)
        except ValueError as e:
            raise ClientFatalError(str(e))
        # 2. Set defaults and overrides
        rl.allow_multifile = self.allow_multifile
        rl.pretty_xml = self.pretty_xml
        rl.mapper = self.mapper
        if (self.max_sitemap_entries is not None):
            rl.max_sitemap_entries = self.max_sitemap_entries
        return(rl)

    def log_event(self, change):
        """Log a Resource object as an event for automated analysis."""
        self.logger.debug("Event: " + repr(change))

    def baseline_or_audit(self, allow_deletion=False, audit_only=False):
        """Baseline synchonization or audit.

        Both functions implemented in this routine because audit is a prerequisite
        for a baseline sync. In the case of baseline sync the last timestamp seen
        is recorded as client state.
        """
        action = ('audit' if (audit_only) else 'baseline sync')
        self.logger.debug("Starting " + action)
        # 0. Sanity checks
        if (len(self.mapper) < 1):
            raise ClientFatalError(
                "No source to destination mapping specified")
        if (not audit_only and self.mapper.unsafe()):
            raise ClientFatalError(
                "Source to destination mappings unsafe: %s" %
                str(self.mapper))
        # 1. Get inventories from both src and dst
        # 1.a source resource list
        src_resource_list = self.find_resource_list()
        self.logger.info(
            "Read source resource list, %d resources listed" %
            (len(src_resource_list)))
        if (len(src_resource_list) == 0):
            raise ClientFatalError(
                "Aborting as there are no resources to sync")
        if (len(self.hashes) > 0):
            self.prune_hashes(src_resource_list.hashes(), 'resource')
        # 1.b destination resource list mapped back to source URIs
        rlb = ResourceListBuilder(set_hashes=self.hashes, mapper=self.mapper)
        dst_resource_list = rlb.from_disk()
        # 2. Compare these resource lists respecting any comparison options
        (same, updated, deleted, created) = dst_resource_list.compare(src_resource_list)
        # 3. Report status and planned actions
        self.log_status(in_sync=(len(updated) + len(deleted) + len(created) == 0),
                        audit=True, same=len(same), created=len(created),
                        updated=len(updated), deleted=len(deleted))
        if (audit_only or len(created) + len(updated) + len(deleted) == 0):
            self.logger.debug("Completed " + action)
            return
        # 4. Check that sitemap has authority over URIs listed
        if (not self.noauth):
            uauth = UrlAuthority(self.sitemap, strict=self.strictauth)
            for resource in src_resource_list:
                if (not uauth.has_authority_over(resource.uri)):
                    raise ClientFatalError(
                        "Aborting as sitemap (%s) mentions resource at a location it does not have authority over (%s), override with --noauth" %
                        (self.sitemap, resource.uri))
        # 5. Grab files to do sync
        delete_msg = (
            ", and delete %d resources" %
            len(deleted)) if (allow_deletion) else ''
        self.logger.warning(
            "Will GET %d resources%s" %
            (len(created) + len(updated), delete_msg))
        self.last_timestamp = 0
        num_created = 0
        num_updated = 0
        num_deleted = 0
        for resource in created:
            uri = resource.uri
            filename = self.mapper.src_to_dst(uri)
            self.logger.info("created: %s -> %s" % (uri, filename))
            num_created += self.update_resource(resource, filename, 'created')
        for resource in updated:
            uri = resource.uri
            filename = self.mapper.src_to_dst(uri)
            self.logger.info("updated: %s -> %s" % (uri, filename))
            num_updated += self.update_resource(resource, filename, 'updated')
        for resource in deleted:
            uri = resource.uri
            filename = self.mapper.src_to_dst(uri)
            num_deleted += self.delete_resource(resource,
                                                filename, allow_deletion)
        # 6. Store last timestamp to allow incremental sync
        if (not audit_only and self.last_timestamp > 0):
            ClientState().set_state(self.sitemap, self.last_timestamp)
            self.logger.info(
                "Written last timestamp %s for incremental sync" %
                (datetime_to_str(
                    self.last_timestamp)))
        # 7. Done
        self.log_status(in_sync=(len(updated) + len(deleted) + len(created) == 0),
                        same=len(same), created=num_created,
                        updated=num_updated, deleted=num_deleted, to_delete=len(deleted))
        self.logger.debug("Completed %s" % (action))

    def incremental(self, allow_deletion=False,
                    change_list_uri=None, from_datetime=None):
        """Incremental synchronization.

        Use Change List to do incremental sync
        """
        self.logger.debug("Starting incremental sync")
        # 0. Sanity checks
        if (len(self.mapper) < 1):
            raise ClientFatalError(
                "No source to destination mapping specified")
        if (self.mapper.unsafe()):
            raise ClientFatalError(
                "Source to destination mappings unsafe: %s" % str(
                    self.mapper))
        from_timestamp = None
        if (from_datetime is not None):
            try:
                from_timestamp = str_to_datetime(from_datetime)
            except ValueError:
                raise ClientFatalError(
                    "Bad datetime in --from (%s)" %
                    from_datetime)
        # 1. Work out where to start from
        if (from_timestamp is None):
            from_timestamp = ClientState().get_state(self.sitemap)
            if (from_timestamp is None):
                raise ClientFatalError(
                    "Cannot do incremental sync. No stored timestamp for this site, and no explicit --from.")
        # 2. Get URI of change list, from sitemap or explicit
        if (change_list_uri):
            # Translate as necessary using maps
            change_list = self.sitemap_uri(change_list_uri)
        else:
            # Try default name
            change_list = self.sitemap_uri(self.change_list_name)
        # 3. Read change list from source
        try:
            self.logger.info("Reading change list %s" % (change_list))
            src_change_list = ChangeList()
            src_change_list.read(uri=change_list)
            self.logger.debug("Finished reading change list")
        except Exception as e:
            raise ClientFatalError(
                "Can't read source change list from %s (%s)" %
                (change_list, str(e)))
        self.logger.info(
            "Read source change list, %d changes listed" %
            (len(src_change_list)))
        # if (len(src_change_list)==0):
        #    raise ClientFatalError("Aborting as there are no resources to sync")
        if (len(self.hashes) > 0):
            self.prune_hashes(src_change_list.hashes(), 'change')
        # Check all changes have timestamp and record last
        self.last_timestamp = 0
        for resource in src_change_list:
            if (resource.timestamp is None):
                raise ClientFatalError(
                    "Aborting - missing timestamp for change in %s" %
                    (uri))
            if (resource.timestamp > self.last_timestamp):
                self.last_timestamp = resource.timestamp
        # 4. Check that the change list has authority over URIs listed
        # FIXME - What does authority mean for change list? Here use both the
        # change list URI and, if we used it, the sitemap URI
        if (not self.noauth):
            uauth_cs = UrlAuthority(change_list, self.strictauth)
            if (not change_list_uri):
                uauth_sm = UrlAuthority(self.sitemap)
                for resource in src_change_list:
                    if (not uauth_cs.has_authority_over(resource.uri) and
                            (change_list_uri or not uauth_sm.has_authority_over(resource.uri))):
                        raise ClientFatalError(
                            "Aborting as change list (%s) mentions resource at a location it does not have authority over (%s), override with --noauth" %
                            (change_list, resource.uri))
        # 5. Prune entries before starting timestamp and dupe changes for a
        # resource
        num_skipped = src_change_list.prune_before(from_timestamp)
        if (num_skipped > 0):
            self.logger.info(
                "Skipped %d changes before %s" %
                (num_skipped, datetime_to_str(from_timestamp)))
        num_dupes = src_change_list.prune_dupes()
        if (num_dupes > 0):
            self.logger.info("Removed %d prior changes" % (num_dupes))
        # Review and log status before
        # FIXME - should at this stage prune the change list to pick out
        # only the last change for each resource
        to_update = 0
        to_create = 0
        to_delete = 0
        for resource in src_change_list:
            if (resource.change == 'updated'):
                to_update += 1
            elif (resource.change == 'created'):
                to_create += 1
            elif (resource.change == 'deleted'):
                to_delete += 1
            else:
                raise ClientError("Unknown change type %s" % (resource.change))
        # Log status based on what we know from the Change List. Exit if
        # either there are no changes or if there are only deletions and
        # we don't allow deletion
        in_sync = ((to_update + to_delete + to_create) == 0)
        self.log_status(in_sync=in_sync, incremental=True, created=to_create,
                        updated=to_update, deleted=to_delete)
        if (in_sync or ((to_update + to_create) == 0 and not allow_deletion)):
            self.logger.debug("Completed incremental")
            return
        # 6. Apply changes at same time or after from_timestamp
        delete_msg = (
            ", and delete %d resources" %
            to_delete) if (allow_deletion) else ''
        self.logger.warning(
            "Will apply %d changes%s" %
            (len(src_change_list), delete_msg))
        num_updated = 0
        num_deleted = 0
        num_created = 0
        for resource in src_change_list:
            uri = resource.uri
            filename = self.mapper.src_to_dst(uri)
            if (resource.change == 'updated'):
                self.logger.info("updated: %s -> %s" % (uri, filename))
                self.update_resource(resource, filename, 'updated')
                num_updated += 1
            elif (resource.change == 'created'):
                self.logger.info("created: %s -> %s" % (uri, filename))
                self.update_resource(resource, filename, 'created')
                num_created += 1
            elif (resource.change == 'deleted'):
                num_deleted += self.delete_resource(
                    resource, filename, allow_deletion)
            else:
                raise ClientError("Unknown change type %s" % (resource.change))
        # 7. Report status and planned actions
        self.log_status(incremental=True, created=num_created, updated=num_updated,
                        deleted=num_deleted, to_delete=to_delete)
        # 8. Record last timestamp we have seen
        if (self.last_timestamp > 0):
            ClientState().set_state(self.sitemap, self.last_timestamp)
            self.logger.info(
                "Written last timestamp %s for incremental sync" %
                (datetime_to_str(
                    self.last_timestamp)))
        # 9. Done
        self.logger.debug("Completed incremental sync")

    def update_resource(self, resource, filename, change=None):
        """Update resource from uri to filename on local system.

        Update means three things:
        1. GET resources
        2. set mtime in local time to be equal to timestamp in UTC (should perhaps
        or at least warn if different from LastModified from the GET response instead
        but maybe warn if different (or just earlier than) the lastmod we expected
        from the resource list
        3. check that resource matches expected information

        Also update self.last_timestamp if the timestamp (in source frame) of this
        resource is later and the current value.

        Returns the number of resources updated/created (0 or 1)
        """
        path = os.path.dirname(filename)
        distutils.dir_util.mkpath(path)
        num_updated = 0
        if (self.dryrun):
            self.logger.info(
                "dryrun: would GET %s --> %s" %
                (resource.uri, filename))
        else:
            # 1. GET
            try:
                urlretrieve(resource.uri, filename)
                num_updated += 1
            except IOError as e:
                msg = "Failed to GET %s -- %s" % (resource.uri, str(e))
                if (self.ignore_failures):
                    self.logger.warning(msg)
                    return(num_updated)
                else:
                    raise ClientFatalError(msg)
            # 2. set timestamp if we have one
            if (resource.timestamp is not None):
                unixtime = int(resource.timestamp)  # no fractional
                os.utime(filename, (unixtime, unixtime))
                if (resource.timestamp > self.last_timestamp):
                    self.last_timestamp = resource.timestamp
            self.log_event(Resource(resource=resource, change=change))
            # 3. sanity check
            length = os.stat(filename).st_size
            if (resource.length is not None and resource.length != length):
                self.logger.info(
                    "Downloaded size for %s of %d bytes does not match expected %d bytes" %
                    (resource.uri, length, resource.length))
            if (len(self.hashes) > 0):
                self.check_hashes(filename, resource)
        return(num_updated)

    def check_hashes(self, filename, resource):
        """Check all hashes present in self.hashes _and_ resource object.

        Simply shows warning for mismatch, does not raise exception or
        otherwise stop process.
        """
        # which hashes to calculate?
        hashes = []
        if ('md5' in self.hashes and resource.md5 is not None):
            hashes.append('md5')
        if ('sha-1' in self.hashes and resource.sha1 is not None):
            hashes.append('sha-1')
        if ('sha-256' in self.hashes and resource.sha256 is not None):
            hashes.append('sha-256')
        # calculate
        hasher = Hashes(hashes, filename)
        # check and report
        if ('md5' in hashes and resource.md5 != hasher.md5):
            self.logger.info(
                "MD5 mismatch for %s, got %s but expected %s" %
                (resource.uri, hasher.md5, resource.md5))
        if ('sha-1' in hashes and resource.sha1 != hasher.sha1):
            self.logger.info(
                "SHA-1 mismatch for %s, got %s but expected %s" %
                (resource.uri, hasher.sha1, resource.sha1))
        if ('sha-256' in hashes and resource.sha256 != hasher.sha256):
            self.logger.info(
                "SHA-256 mismatch for %s, got %s but expected %s" %
                (resource.uri, hasher.sha256, resource.sha256))

    def delete_resource(self, resource, filename, allow_deletion=False):
        """Delete copy of resource in filename on local system.

        Will only actually do the deletion if allow_deletion is True. Regardless
        of whether the deletion occurs, self.last_timestamp will be updated
        if the resource.timestamp is later than the current value.

        Returns the number of files actually deleted (0 or 1).
        """
        num_deleted = 0
        uri = resource.uri
        if (resource.timestamp is not None and
                resource.timestamp > self.last_timestamp):
            self.last_timestamp = resource.timestamp
        if (allow_deletion):
            if (self.dryrun):
                self.logger.info(
                    "dryrun: would delete %s -> %s" %
                    (uri, filename))
            else:
                try:
                    os.unlink(filename)
                    num_deleted += 1
                    self.logger.info("deleted: %s -> %s" % (uri, filename))
                    self.log_event(
                        Resource(
                            resource=resource,
                            change="deleted"))
                except OSError as e:
                    msg = "Failed to DELETE %s -> %s : %s" % (
                        uri, filename, str(e))
                    # if (self.ignore_failures):
                    self.logger.warning(msg)
                    #    return
                    # else:
                    #    raise ClientFatalError(msg)
        else:
            self.logger.info(
                "nodelete: would delete %s (--delete to enable)" %
                uri)
        return(num_deleted)

    def parse_document(self):
        """Parse any ResourceSync document and show information.

        Will use sitemap URI taken either from explicit self.sitemap_name
        or derived from the mappings supplied.
        """
        s = Sitemap()
        self.logger.info("Reading sitemap(s) from %s ..." % (self.sitemap))
        try:
            list = s.parse_xml(url_or_file_open(self.sitemap))
        except IOError as e:
            raise ClientFatalError("Cannot read document (%s)" % str(e))
        num_entries = len(list.resources)
        capability = '(unknown capability)'
        if ('capability' in list.md):
            capability = list.md['capability']
        print("Parsed %s document with %d entries" % (capability, num_entries))
        if (self.verbose):
            to_show = 100
            override_str = ' (override with --max-sitemap-entries)'
            if (self.max_sitemap_entries):
                to_show = self.max_sitemap_entries
                override_str = ''
            if (num_entries > to_show):
                print(
                    "Showing first %d entries sorted by URI%s..." %
                    (to_show, override_str))
            n = 0
            for resource in list:
                print('[%d] %s' % (n, str(resource)))
                n += 1
                if (n >= to_show):
                    break

    def write_resource_list(
            self, paths=None, outfile=None, links=None, dump=None):
        """Write a Resource List or a Resource Dump for files on local disk.

        Set of resources included is based on paths setting or else the mappings.
        Optionally links can be added. Output will be to stdout unless outfile
        is specified.

        If dump is true then a Resource Dump is written instead of a Resource
        List. If outfile is not set then self.default_resource_dump will be used.
        """
        rl = self.build_resource_list(paths=paths, set_path=dump)
        if (links is not None):
            rl.ln = links
        if (dump):
            if (outfile is None):
                outfile = self.default_resource_dump
            self.logger.info("Writing resource dump to %s..." % (dump))
            d = Dump(resources=rl, format=self.dump_format)
            d.write(basename=outfile)
        else:
            if (outfile is None):
                try:
                    print(rl.as_xml())
                except ListBaseIndexError as e:
                    raise ClientFatalError(
                        "%s. Use --output option to specify base name for output files." %
                        str(e))
            else:
                rl.write(basename=outfile)

    def write_change_list(self, paths=None, outfile=None, ref_sitemap=None, newref_sitemap=None,
                          empty=None, links=None, dump=None):
        """Write a change list.

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
            # or build resource list from files on disk
            if (newref_sitemap is None):
                # Get resource list from disk
                new_rl = self.build_resource_list(paths=paths, set_path=dump)
            else:
                new_rl = self.read_reference_resource_list(
                    newref_sitemap, name='new reference')
            # 3. Calculate change list
            (same, updated, deleted, created) = old_rl.compare(new_rl)
            cl.add_changed_resources(updated, change='updated')
            cl.add_changed_resources(deleted, change='deleted')
            cl.add_changed_resources(created, change='created')
        # 4. Write out change list
        cl.mapper = self.mapper
        cl.pretty_xml = self.pretty_xml
        if (self.max_sitemap_entries is not None):
            cl.max_sitemap_entries = self.max_sitemap_entries
        if (outfile is None):
            print(cl.as_xml())
        else:
            cl.write(basename=outfile)
        self.write_dump_if_requested(cl, dump)

    def write_capability_list(self, capabilities=None,
                              outfile=None, links=None):
        """Write a Capability List to outfile or STDOUT."""
        capl = CapabilityList(ln=links)
        capl.pretty_xml = self.pretty_xml
        if (capabilities is not None):
            for name in capabilities.keys():
                capl.add_capability(name=name, uri=capabilities[name])
        if (outfile is None):
            print(capl.as_xml())
        else:
            capl.write(basename=outfile)

    def write_source_description(
            self, capability_lists=None, outfile=None, links=None):
        """Write a ResourceSync Description document to outfile or STDOUT."""
        rsd = SourceDescription(ln=links)
        rsd.pretty_xml = self.pretty_xml
        if (capability_lists is not None):
            for uri in capability_lists:
                rsd.add_capability_list(uri)
        if (outfile is None):
            print(rsd.as_xml())
        else:
            rsd.write(basename=outfile)

    def write_dump_if_requested(self, resource_list, dump):
        """Write a dump to the file dump."""
        if (dump is None):
            return
        print("OOPS - FIXME - Wrinting dump to %s not yet implemented" % (dump))
        return(1)

    def read_reference_resource_list(self, ref_sitemap, name='reference'):
        """Read reference resource list and return the ResourceList object.

        The name parameter is used just in output messages to say what type
        of resource list is being read.
        """
        rl = ResourceList()
        self.logger.info(
            "Reading %s resource list from %s ..." %
            (name, ref_sitemap))
        rl.mapper = self.mapper
        rl.read(uri=ref_sitemap, index_only=(not self.allow_multifile))
        num_entries = len(rl.resources)
        self.logger.info(
            "Read %s resource list with %d entries in %d sitemaps" %
            (name, num_entries, rl.num_files))
        if (self.verbose):
            to_show = 100
            override_str = ' (override with --max-sitemap-entries)'
            if (self.max_sitemap_entries):
                to_show = self.max_sitemap_entries
                override_str = ''
            if (num_entries > to_show):
                print(
                    "Showing first %d entries sorted by URI%s..." %
                    (to_show, override_str))
            n = 0
            for r in rl.resources:
                print(r)
                n += 1
                if (n >= to_show):
                    break
        return(rl)

    def prune_hashes(self, hashes, list_type):
        """Prune any hashes not in source resource or change list."""
        discarded = []
        for hash in hashes:
            if (hash in self.hashes):
                self.hashes.discard(hash)
                discarded.append(hash)
        self.logger.info("Not calculating %s hash(es) on destination as not present "
                         "in source %s list" % (', '.join(sorted(discarded)), list_type))

    def log_status(self, in_sync=True, incremental=False, audit=False,
                   same=None, created=0, updated=0, deleted=0, to_delete=0):
        """Write log message regarding status in standard form.

        Split this off so all messages from baseline/audit/incremental
        are written in a consistent form.
        """
        if (audit):
            words = {'created': 'to create',
                     'updated': 'to update',
                     'deleted': 'to delete'}
        else:
            words = {'created': 'created',
                     'updated': 'updated',
                     'deleted': 'deleted'}
        if in_sync:
            # status rather than action
            status = "NO CHANGES" if incremental else "IN SYNC"
        else:
            if audit:
                status = "NOT IN SYNC"
            elif (to_delete > deleted):
                # will need --delete
                status = "PART APPLIED" if incremental else"PART SYNCED"
                words['deleted'] = 'to delete (--delete)'
                deleted = to_delete
            else:
                status = "CHANGES APPLIED" if incremental else "SYNCED"
        same = "" if (same is None) else ("same=%d, " % same)
        self.logger.warning("Status: %15s (%s%s=%d, %s=%d, %s=%d)" %
                            (status, same, words['created'], created,
                             words['updated'], updated, words['deleted'], deleted))
