"""ResourceSync resource_list object

An resource_list is a set of resources with some metadata for each 
resource. Comparison of inventories from a source and a 
destination allows understanding of whether the two are in
sync or whether some resources need to be updated at the
destination.

The resource_list object may also contain metadata and links.
"""

import collections
import os
from datetime import datetime
import re
import sys
from urllib import URLopener

from list_base import ListBase
from sitemap import Sitemap
from mapper import Mapper, MapperError
from url_authority import UrlAuthority


class ResourceListDict(dict):
    """Default implementation of class to store resources in ResourceList

    Key properties of this class are:
    - has add(resource) method
    - is iterable and results given in alphanumeric order by resource.uri
    """

    def __iter__(self):
        """Iterator over all the resources in this resource_list"""
        self._iter_next_list = sorted(self.keys())
        self._iter_next_list.reverse()
        return(iter(self._iter_next, None))

    def _iter_next(self):
        if (len(self._iter_next_list)>0):
            return(self[self._iter_next_list.pop()])
        else:
            return(None)

    def uris(self):
        return(sorted(self.keys()))

    def add(self, resource, replace=False):
        """Add just a single resource"""
        uri = resource.uri
        if (uri in self and not replace):
            raise ResourceListDupeError("Attempt to add resource already in resource_list") 
        self[uri]=resource

class ResourceListDupeError(Exception):
    pass

class ResourceList(ListBase):
    """Class representing an resource_list of resources

    This same class is used for both the source and the destination
    and is the central point of comparison the decide whether they
    are in sync or what needs to be copied to bring the destinaton
    into sync.

    An resource_list will admit only one resource with any given URI.

    Storage is unordered but the iterator imposes a canonical order
    which is currently alphabetical by URI.
    """

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = ResourceListDict()
        super(ResourceList, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name = 'resourcelist'
        self.capability_md = 'resourcelist'
        # specific to Resource Lists:
        self.max_sitemap_entries=50000
        # related to Indexes
        self.mapper = None
        self.allow_multifile = True
        self.check_url_authority = False
        self.content_length = 0
        self.bytes_read = 0           # Aggregate of content_length values

    def add(self, resource, replace=False):
        """Add a resource or an iterable collection of resources

        Will throw a ValueError if the resource (ie. same uri) already
        exists in the resource_list, unless replace=True.
        """
        if isinstance(resource, collections.Iterable):
            for r in resource:
                self.resources.add(r,replace)
        else:
            self.resources.add(resource,replace)

    def compare(self,src):
        """Compare the current resource_list object with the specified resource_list

        The parameter src must also be an resource_list object, it is assumed
        to be the source, and the current object is the destination. This 
        written to work for any objects in self and sc, provided that the
        == operator can be used to compare them.

        The functioning of this method depends on the iterators for self and
        src providing access to the resource objects in URI order.
        """
        dst_iter = iter(self.resources)
        src_iter = iter(src.resources)
        same=ResourceList()
        updated=ResourceList()
        deleted=ResourceList()
        created=ResourceList()
        dst_cur=next(dst_iter,None)
        src_cur=next(src_iter,None)
        while ((dst_cur is not None) and (src_cur is not None)):
            #print 'dst='+dst_cur+'  src='+src_cur
            if (dst_cur.uri == src_cur.uri):
                if (dst_cur==src_cur):
                    same.add(dst_cur)
                else:
                    updated.add(src_cur)
                dst_cur=next(dst_iter,None)
                src_cur=next(src_iter,None)
            elif (not src_cur or dst_cur.uri < src_cur.uri):
                deleted.add(dst_cur)
                dst_cur=next(dst_iter,None)
            elif (not dst_cur or dst_cur.uri > src_cur.uri):
                created.add(src_cur)
                src_cur=next(src_iter,None)
            else:
                raise InternalError("this should not be possible")
        # what do we have leftover in src or dst lists?
        while (dst_cur is not None):
            deleted.add(dst_cur)
            dst_cur=next(dst_iter,None)
        while (src_cur is not None):
            created.add(src_cur)
            src_cur=next(src_iter,None)
        # have now gone through both lists
        return(same,updated,deleted,created)

    def has_md5(self):
        """Return true if at least one contained resource-like object has md5 data"""
        if (self.resources is None):
            return(False)
        for resource in self:
            if (resource.md5 is not None):
                return(True)
        return(False)

    ##### General sitemap methods that also handle sitemapindexes #####

    def write(self, resources=None, basename='/tmp/sitemap.xml'):
        """Write one or a set of sitemap files to disk

        resources is a ResourceContainer that may be an ResourceList or
        a ChangeList. This may be a generator so data is read as needed
        and length is determined at the end.

        basename is used as the name of the single sitemap file or the 
        sitemapindex for a set of sitemap files.

        Uses self.max_sitemap_entries to determine whether the resource_list can 
        be written as one sitemap. If there are more entries and 
        self.allow_multifile is set true then a set of sitemap files, 
        with an sitemapindex, will be written.
        """
        # Access resources through iterator only
        resources_iter = iter(resources)
        ( chunk, next ) = self.get_resources_chunk(resources_iter)
        if (next is not None):
            # Have more than self.max_sitemap_entries => sitemapindex
            if (not self.allow_multifile):
                raise Exception("Too many entries for a single sitemap but multifile disabled")
            # Work out how to name the sitemaps, attempt to add %05d before ".xml$", else append
            sitemap_prefix = basename
            sitemap_suffix = '.xml'
            if (basename[-4:] == '.xml'):
                sitemap_prefix = basename[:-4]
            # Use iterator over all resources and count off sets of
            # max_sitemap_entries to go into each sitemap, store the
            # names of the sitemaps as we go
            sitemaps={}
            while (len(chunk)>0):
                file = sitemap_prefix + ( "%05d" % (len(sitemaps)) ) + sitemap_suffix
                self.logger.info("Writing sitemap %s..." % (file))
                f = open(file, 'w')
                f.write(self.resources_as_xml(chunk))
                f.close()
                # Record timestamp
                sitemaps[file] = os.stat(file).st_mtime
                # Get next chunk
                ( chunk, next ) = self.get_resources_chunk(resources_iter,next)
            self.logger.info("Wrote %d sitemaps" % (len(sitemaps)))
            f = open(basename, 'w')
            self.logger.info("Writing sitemapindex %s..." % (basename))
            f.write(self.sitemapindex_as_xml(sitemaps=sitemaps,resource_list=resources))
            f.close()
            self.logger.info("Wrote sitemapindex %s" % (basename))
        else:
            f = open(basename, 'w')
            self.logger.info("Writing sitemap %s..." % (basename))
            f.write(self.resources_as_xml(chunk))
            f.close()
            self.logger.info("Wrote sitemap %s" % (basename))

    def read(self, uri=None, resources=None, capability=None, index_only=False):
        """Read sitemap from a URI including handling sitemapindexes

        If index_only is True then individual sitemaps references in a sitemapindex
        will not be read. This will result in no resources being returned and is
        useful only to read the metadata and links listed in the sitemapindex.

        Includes the subtlety that if the input URI is a local file and is a 
        sitemapindex which contains URIs for the individual sitemaps, then these
        are mapped to the filesystem also.
        """
        try:
            fh = URLopener().open(uri)
        except IOError as e:
            raise Exception("Failed to load sitemap/sitemapindex from %s (%s)" % (uri,str(e)))
        # Get the Content-Length if we can (works fine for local files)
        try:
            self.content_length = int(fh.info()['Content-Length'])
            self.bytes_read += self.content_length
            self.logger.debug( "Read %d bytes from %s" % (self.content_length,uri) )
        except KeyError:
            # If we don't get a length then c'est la vie
            self.logger.debug( "Read ????? bytes from %s" % (uri) )
            pass
        self.logger.info( "Read sitemap/sitemapindex from %s" % (uri) )
        s = Sitemap()
        s.parse_xml(fh=fh,resources=self,capability='resource_list')
        # what did we read? sitemap or sitemapindex?
        if (s.parsed_index):
            # sitemapindex
            if (not self.allow_multifile):
                raise Exception("Got sitemapindex from %s but support for sitemapindex disabled" % (uri))
            self.logger.info( "Parsed as sitemapindex, %d sitemaps" % (len(self.resources)) )
            sitemapindex_is_file = self.is_file_uri(uri)
            if (index_only):
                # don't read the component sitemaps
                return
            # now loop over all entries to read each sitemap and add to resources
            sitemaps = self.resources
            self.resources = ResourceListDict()
            self.logger.info( "Now reading %d sitemaps" % len(sitemaps.uris()) )
            for sitemap_uri in sorted(sitemaps.uris()):
                self.read_component_sitemap(uri,sitemap_uri,s,sitemapindex_is_file)
        else:
            # sitemap
            self.logger.info( "Parsed as sitemap, %d resources" % (len(self.resources)) )

    def read_component_sitemap(self, sitemapindex_uri, sitemap_uri, sitemap, sitemapindex_is_file):
        """Read a component sitemap of a Resource List with index
        """
        print sitemapindex_is_file
        print self.mapper
        if (sitemapindex_is_file):
            if (not self.is_file_uri(sitemap_uri)):
                # Attempt to map URI to local file
                remote_uri = sitemap_uri
                sitemap_uri = self.mapper.src_to_dst(remote_uri)
                self.logger.info("Mapped %s to local file %s" % (remote_uri, sitemap_uri))
            else:
                # The individual sitemaps should be at a URL (scheme/server/path)
                # that the sitemapindex URL can speak authoritatively about
                if (self.check_url_authority and
                    not UrlAuthority(sitemapindex_uri).has_authority_over(sitemap_uri)):
                    raise Exception("The sitemapindex (%s) refers to sitemap at a location it does not have authority over (%s)" % (sitemapindex_uri,sitemap_uri))
        try:
            fh = URLopener().open(sitemap_uri)
        except IOError as e:
            raise Exception("Failed to load sitemap from %s listed in sitemap index %s (%s)" % (sitemap_uri,sitemapindex_uri,str(e)))
        # Get the Content-Length if we can (works fine for local files)
        try:
            self.content_length = int(fh.info()['Content-Length'])
            self.bytes_read += self.content_length
        except KeyError:
            # If we don't get a length then c'est la vie
            pass
        self.logger.info( "Reading sitemap from %s (%d bytes)" % (sitemap_uri,self.content_length) )
        sitemap.parse_xml( fh=fh, resources=self.resources, sitemapindex=False )

    ##### Utility #####                                                                                          
    def is_file_uri(self, uri):
        """Return true if uri looks like a local file URI, false otherwise
        
        Test is to see whether have either an explicit file: URI or whether
        there is no scheme name.
        """
        return(re.match('file:',uri) or not re.match('\w{3,4}:',uri))
