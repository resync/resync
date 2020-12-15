"""Base class for ResourceSync capabilities with large lists of resources.

Handles possibly large lists by including support for both sitemaps and
sitemapindexes. Extends ListBase to add the support for sitemapindexes.
"""

import collections
import math
import os
from datetime import datetime
import re
import sys
import itertools

from .hashes import Hashes
from .list_base import ListBase
from .mapper import Mapper, MapperError
from .resource import Resource
from .sitemap import Sitemap
from .url_authority import UrlAuthority
from .url_or_file_open import url_or_file_open


class ListBaseWithIndex(ListBase):
    """Class that add handling of sitemapindexes to ListBase.

    Splitting of a list into multiple sitemaps with a sitemapindex is currently
    handled based solely on the number of entries in the list. The configurable
    self.max_sitemap_entries controls the number of entries that will be written
    in a single sitemap or a component sitemap that has a sitemapindex. Support
    for sitemapindexes can be disabled by setting allow_multifile False.

    resources - an iterable of resources

    count - add optional explicit setting of the number of items in
        resources which is useful when this is an iterator/generator.
        Is used instead of trying len(resources)

    md - metadata information for the list (<rs:md>)

    ln - link information for the list (<rs:ln>)

    allow_multifile - set False to disable support for indexes. Defaults to True

    mapper - Mapper instance used to map between file names and URIs so that
        the correct URIs can be written into a sitemapindex which correspond
        to those that the component sitemap files will be exposed as
    """

    def __init__(self, resources=None, count=None, md=None, ln=None, uri=None,
                 capability_name='unknown', allow_multifile=None, mapper=None,
                 spec_version='1.1', include_lastmod=False, resources_class=None):
        """Initialize ListBaseWithIndex."""
        self.resources_class = list if resources_class is None else resources_class
        if (resources is None):
            resources = self.resources_class()
        super(ListBaseWithIndex, self).__init__(
            resources=resources,
            count=count,
            md=md,
            ln=ln,
            uri=uri,
            capability_name=capability_name,
            spec_version=spec_version,
            include_lastmod=include_lastmod)
        # specific to lists with indexes
        self.max_sitemap_entries = 50000
        self.mapper = mapper
        self.allow_multifile = (
            True if (
                allow_multifile is None) else allow_multifile)
        self.check_url_authority = False
        self.content_length = 0
        self.num_files = 0            # Number of files read
        self.bytes_read = 0           # Aggregate of content_length values

    # INPUT

    def read(self, uri=None, resources=None, index_only=False):
        """Read sitemap from a URI including handling sitemapindexes.

        If index_only is True then individual sitemaps references in a sitemapindex
        will not be read. This will result in no resources being returned and is
        useful only to read the metadata and links listed in the sitemapindex.

        Includes the subtlety that if the input URI is a local file and is a
        sitemapindex which contains URIs for the individual sitemaps, then these
        are mapped to the filesystem also.
        """
        try:
            fh = url_or_file_open(uri)
            self.num_files += 1
        except IOError as e:
            raise IOError(
                "Failed to load sitemap/sitemapindex from %s (%s)" %
                (uri, str(e)))
        # Get the Content-Length if we can (works fine for local files)
        try:
            self.content_length = int(fh.info()['Content-Length'])
            self.bytes_read += self.content_length
            self.logger.debug(
                "Read %d bytes from %s" %
                (self.content_length, uri))
        except KeyError:
            # If we don't get a length then c'est la vie
            self.logger.debug("Read ????? bytes from %s" % (uri))
            pass
        self.logger.info("Read sitemap/sitemapindex from %s" % (uri))
        s = self.new_sitemap()
        s.parse_xml(fh=fh, resources=self, capability=self.capability_name)
        # what did we read? sitemap or sitemapindex?
        if (s.parsed_index):
            # sitemapindex
            if (not self.allow_multifile):
                raise ListBaseIndexError(
                    "Got sitemapindex from %s but support for sitemapindex disabled" %
                    (uri))
            self.logger.info(
                "Parsed as sitemapindex, %d sitemaps" %
                (len(
                    self.resources)))
            sitemapindex_is_file = self.is_file_uri(uri)
            if (index_only):
                # don't read the component sitemaps
                self.sitemapindex = True
                return
            # now loop over all entries to read each sitemap and add to
            # resources
            sitemaps = self.resources
            self.resources = self.resources_class()
            self.logger.info("Now reading %d sitemaps" % len(sitemaps.uris()))
            for sitemap_uri in sorted(sitemaps.uris()):
                self.read_component_sitemap(
                    uri, sitemap_uri, s, sitemapindex_is_file)
        else:
            # sitemap
            self.logger.info("Parsed as sitemap, %d resources" %
                             (len(self.resources)))

    def read_component_sitemap(
            self, sitemapindex_uri, sitemap_uri, sitemap, sitemapindex_is_file):
        """Read a component sitemap of a Resource List with index.

        Each component must be a sitemap with the
        """
        if (sitemapindex_is_file):
            if (not self.is_file_uri(sitemap_uri)):
                # Attempt to map URI to local file
                remote_uri = sitemap_uri
                sitemap_uri = self.mapper.src_to_dst(remote_uri)
                self.logger.info(
                    "Mapped %s to local file %s" %
                    (remote_uri, sitemap_uri))
            else:
                # The individual sitemaps should be at a URL (scheme/server/path)
                # that the sitemapindex URL can speak authoritatively about
                if (self.check_url_authority
                        and not UrlAuthority(sitemapindex_uri).has_authority_over(sitemap_uri)):
                    raise ListBaseIndexError(
                        "The sitemapindex (%s) refers to sitemap at a location it does not have authority over (%s)" %
                        (sitemapindex_uri, sitemap_uri))
        try:
            fh = url_or_file_open(sitemap_uri)
            self.num_files += 1
        except IOError as e:
            raise ListBaseIndexError(
                "Failed to load sitemap from %s listed in sitemap index %s (%s)" %
                (sitemap_uri, sitemapindex_uri, str(e)))
        # Get the Content-Length if we can (works fine for local files)
        try:
            self.content_length = int(fh.info()['Content-Length'])
            self.bytes_read += self.content_length
        except KeyError:
            # If we don't get a length then c'est la vie
            pass
        self.logger.info(
            "Reading sitemap from %s (%d bytes)" %
            (sitemap_uri, self.content_length))
        component = sitemap.parse_xml(fh=fh, sitemapindex=False)
        # Copy resources into self, check any metadata
        for r in component:
            self.resources.add(r)
        # FIXME - if rel="up" check it goes to correct place
        # FIXME - check capability

    # OUTPUT

    def requires_multifile(self):
        """Return False or the number of component sitemaps required.

        In the case that no len() is available for self.resources then
        then self.count must be set beforehand to avoid an exception.
        """
        if (self.max_sitemap_entries is None
                or len(self) <= self.max_sitemap_entries):
            return(False)
        return(int(math.ceil(len(self) / float(self.max_sitemap_entries))))

    def as_xml(self, allow_multifile=False, basename="/tmp/sitemap.xml"):
        """Return XML serialization of this list.

        If this list can be serialized as a single sitemap then the
        superclass method is used.

        If there is no single XML serialization (in the case that the
        number of list resources is more than is allowed in a single sitemap)
        then raise an exception unless allow_multifile is set True.
        If allow_multifile is set True then will return the sitemapindex
        for the set of component sitemaps.
        """
        if (not self.requires_multifile()):
            return super(ListBaseWithIndex, self).as_xml()
        elif (allow_multifile):
            return self.as_xml_index(basename)
        else:
            raise ListBaseIndexError(
                "Attempt to write single XML string for list with %d entries when max_sitemap_entries is set to %d" %
                (len(self), self.max_sitemap_entries))

    def as_xml_index(self, basename="/tmp/sitemap.xml"):
        """Return a string of the index for a large list that is split.

        All we need to do is determine the number of component sitemaps will
        be is and generate their URIs based on a pattern.

        Q - should there be a flag to select generation of each component sitemap
        in order to calculate the md5sum?

        Q - what timestamp should be used?
        """
        num_parts = self.requires_multifile()
        if (not num_parts):
            raise ListBaseIndexError(
                "Request for sitemapindex for list with only %d entries when max_sitemap_entries is set to %s" %
                (len(self), str(
                    self.max_sitemap_entries)))
        index = ListBase()
        index.sitemapindex = True
        index.capability_name = self.capability_name
        index.default_capability()
        for n in range(num_parts):
            r = Resource(uri=self.part_name(basename, n))
            index.add(r)
        return(index.as_xml())

    def as_xml_part(self, basename="/tmp/sitemap.xml", part_number=0):
        """Return a string of component sitemap number part_number.

        Used in the case of a large list that is split into component
        sitemaps.

        basename is used to create "index" links to the sitemapindex

        Q - what timestamp should be used?
        """
        if (not self.requires_multifile()):
            raise ListBaseIndexError(
                "Request for component sitemap for list with only %d entries when max_sitemap_entries is set to %s" %
                (len(self), str(
                    self.max_sitemap_entries)))
        start = part_number * self.max_sitemap_entries
        if (start > len(self)):
            raise ListBaseIndexError(
                "Request for component sitemap with part_number too high, would start at entry %d yet the list has only %d entries" %
                (start, len(self)))
        stop = start + self.max_sitemap_entries
        if (stop > len(self)):
            stop = len(self)
        part = ListBase(itertools.islice(self.resources, start, stop))
        part.capability_name = self.capability_name
        part.default_capability()
        part.index = basename
        s = self.new_sitemap()
        return(s.resources_as_xml(part))

    def write(self, basename='/tmp/sitemap.xml'):
        """Write one or a set of sitemap files to disk.

        resources is a ResourceContainer that may be an ResourceList or
        a ChangeList. This may be a generator so data is read as needed
        and length is determined at the end.

        basename is used as the name of the single sitemap file or the
        sitemapindex for a set of sitemap files.

        Uses self.max_sitemap_entries to determine whether the resource_list can
        be written as one sitemap. If there are more entries and
        self.allow_multifile is set True then a set of sitemap files,
        with an sitemapindex, will be written.
        """
        # Access resources through iterator only
        resources_iter = iter(self.resources)
        (chunk, nxt) = self.get_resources_chunk(resources_iter)
        s = self.new_sitemap()
        if (nxt is not None):
            # Have more than self.max_sitemap_entries => sitemapindex
            if (not self.allow_multifile):
                raise ListBaseIndexError(
                    "Too many entries for a single sitemap but multifile disabled")
            # Work out URI of sitemapindex so that we can link up to
            # it from the individual sitemap files
            try:
                index_uri = self.mapper.dst_to_src(basename)
            except MapperError as e:
                raise ListBaseIndexError(
                    "Cannot map sitemapindex filename to URI (%s)" %
                    str(e))
            # Use iterator over all resources and count off sets of
            # max_sitemap_entries to go into each sitemap, store the
            # names of the sitemaps as we go. Copy md from self into
            # the index and use this for all chunks also
            index = ListBase(md=self.md.copy(), ln=list(self.ln))
            index.capability_name = self.capability_name
            index.default_capability()
            while (len(chunk) > 0):
                file = self.part_name(basename, len(index))
                # Check that we can map the filename of this sitemap into
                # URI space for the sitemapindex
                try:
                    uri = self.mapper.dst_to_src(file)
                except MapperError as e:
                    raise ListBaseIndexError(
                        "Cannot map sitemap filename to URI (%s)" % str(e))
                self.logger.info("Writing sitemap %s..." % (file))
                f = open(file, 'w')
                chunk.index = index_uri
                chunk.md = index.md
                s.resources_as_xml(chunk, fh=f)
                f.close()
                # Record information about this sitemap for index
                r = Resource(uri=uri,
                             timestamp=os.stat(file).st_mtime,
                             md5=Hashes(['md5'], file).md5)
                index.add(r)
                # Get next chunk
                (chunk, nxt) = self.get_resources_chunk(resources_iter, nxt)
            self.logger.info("Wrote %d sitemaps" % (len(index)))
            f = open(basename, 'w')
            self.logger.info("Writing sitemapindex %s..." % (basename))
            s.resources_as_xml(index, sitemapindex=True, fh=f)
            f.close()
            self.logger.info("Wrote sitemapindex %s" % (basename))
        elif self.sitemapindex:
            f = open(basename, 'w')
            self.logger.info("Writing sitemapindex %s..." % (basename))
            s.resources_as_xml(chunk, sitemapindex=True, fh=f)
            f.close()
            self.logger.info("Wrote sitemapindex %s" % (basename))
        else:
            f = open(basename, 'w')
            self.logger.info("Writing sitemap %s..." % (basename))
            s.resources_as_xml(chunk, fh=f)
            f.close()
            self.logger.info("Wrote sitemap %s" % (basename))

    def index_as_xml(self):
        """XML serialization of this list taken to be sitemapindex entries."""
        self.default_capability()
        s = self.new_sitemap()
        return s.resources_as_xml(self, sitemapindex=True)

    # Utility

    def get_resources_chunk(self, resource_iter, first=None):
        """Return next chunk of resources from resource_iter, and next item.

        If first parameter is specified then this will be prepended to
        the list.

        The chunk will contain self.max_sitemap_entries if the iterator
        returns that many. next will have the value of the next value from
        the iterator, providing indication of whether more is available.
        Use this as first when asking for the following chunk.
        """
        chunk = ListBase(md=self.md.copy(), ln=list(self.ln))
        chunk.capability_name = self.capability_name
        chunk.default_capability()
        if (first is not None):
            chunk.add(first)
        for r in resource_iter:
            chunk.add(r)
            if (len(chunk) >= self.max_sitemap_entries):
                break
        # Get next to see whether there are more resources
        try:
            nxt = next(resource_iter)
        except StopIteration:
            nxt = None
        return(chunk, nxt)

    def part_name(self, basename='/tmp/sitemap.xml', part_number=0):
        """Name (file or URI) for one component sitemap.

        Works for both filenames and URIs because manipulates only the end
        of the string.

        Abstracting this into a function that starts from the basename to get
        prefix and suffix each time seems a bit wasteful but perhaps not worth
        worrying about. Allows same code to be used for the write() and
        as_xml_index() cases.
        """
        # Work out how to name the sitemaps, attempt to add %05d before
        # ".xml$", else append
        sitemap_prefix = basename
        sitemap_suffix = '.xml'
        if (basename[-4:] == '.xml'):
            sitemap_prefix = basename[:-4]
        return(sitemap_prefix + ("%05d" % (part_number)) + sitemap_suffix)

    def is_file_uri(self, uri):
        """Return true if uri looks like a local file URI, false otherwise.

        Test is to see whether have either an explicit file: URI or whether
        there is no scheme name.
        """
        return(re.match(r'file:', uri) or not re.match(r'\w{3,4}:', uri))


class ListBaseIndexError(Exception):
    """Exception for problems with sitemapindexes in ListBaseIndex."""

    pass
