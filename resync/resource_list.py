"""ResourceSync resource_list object

An resource_list is a set of resources with some metadata for each 
resource. Comparison of inventories from a source and a 
destination allows understanding of whether the two are in
sync or whether some resources need to be updated at the
destination.

The resource_list object may also contain metadata regarding 
capabilities and discovery information.
"""

import collections
import os
from datetime import datetime
import re
import sys
import StringIO
from urllib import URLopener

from resource_container import ResourceContainer
from sitemap import Sitemap

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

    def add(self, resource, replace=False):
        """Add just a single resource"""
        uri = resource.uri
        if (uri in self and not replace):
            raise ResourceListDupeError("Attempt to add resource already in resource_list") 
        self[uri]=resource

class ResourceListDupeError(Exception):
    pass

class ResourceList(ResourceContainer):
    """Class representing an resource_list of resources

    This same class is used for both the source and the destination
    and is the central point of comparison the decide whether they
    are in sync or what needs to be copied to bring the destinaton
    into sync.

    An resource_list will admit only one resource with any given URI.

    Storage is unordered but the iterator imposes a canonical order
    which is currently alphabetical by URI.
    """

    def __init__(self, resources=None, capabilities=None):
        self.resources=(resources if (resources is not None) else ResourceListDict())
        self.capabilities=(capabilities if (capabilities is not None) else {})

    def __iter__(self):
        """Iterator over all the resources in this resource_list"""
        return(iter(self.resources))

    def __len__(self):
        """Return number of resources in this resource_list"""
        return(len(self.resources))

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

    def parse(self,uri=None,fh=None):
        if (uri is not None):
            try:
                fh = URLopener().open(uri)
            except IOError as e:
                raise Exception("Failed to load sitemap/sitemapindex from %s (%s)" % (uri,str(e)))
        if (fh is None):
            raise Exception("Nothing to parse")
        s = Sitemap()
        s.sitemap_parse_xml(fh=fh,resources=self,capability='resourcelist')

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
