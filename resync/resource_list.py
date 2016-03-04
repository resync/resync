"""ResourceSync Resource List object

An Resource List is a set of resources with some metadata for 
each resource. Comparison of resource lists from a source and 
a destination allows understanding of whether the two are in
sync or whether some resources need to be updated at the
destination.

There may also be metadata about the Resource List, and links
to other ResourceSync documents. Metadata include the 
timestamp of the ResourceList (md_at) and, optionally, the 
timestamp when creation of the Resource List was completed
(md_completed).at the top level. These include a creation timestamp (from) 
and links to the Capability List.

Described in specification at:
http://www.openarchives.org/rs/resourcesync#DescResources
"""

import collections
import os
from datetime import datetime
import re
import sys
try: #python3
    from urllib.request import URLopener
except ImportError: #python2
    from urllib import URLopener

from .list_base_with_index import ListBaseWithIndex
from .sitemap import Sitemap
from .mapper import Mapper, MapperError
from .url_authority import UrlAuthority


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

class ResourceListOrdered(list):
    """Alternative implementation of class to store resources in ResourceList

    FIXME - This is a rather inefficient implementation which involves 
    scanning all resources to check for duplicates. Designed just to enable
    re-creation of examples in the spec. Something dictionary based would
    likely be better. Might be best to use OrderedDict but that is available
    natively only in python >= 2.7 and this library is designed for 2.6,2.7.

    Key properties of this class are:
    - has add(resource) method
    - is iterable and results given in order added (not the usual one!)
    """

    def uris(self):
        """Extract list of all resource URIs (in the order added)"""
        uris = []
        for r in self:
            uris.append(r.uri)
        return(uris)

    def add(self, resource, replace=False):
        """Add a single resource, check for dupes"""
        uri = resource.uri
        for r in self:
            if (uri == r.uri):
                if (replace):
                    r=resource
                    return
                else:
                    raise ResourceListDupeError("Attempt to add resource already in resource_list") 
        # didn't find it in list, add to end
        self.append(resource)

class ResourceListDupeError(Exception):
    pass

class ResourceList(ListBaseWithIndex):
    """Class representing an resource_list of resources

    This same class is used for both the source and the destination
    and is the central point of comparison the decide whether they
    are in sync or what needs to be copied to bring the destinaton
    into sync.

    A Resource List will admit only one resource with any given URI.

    Typical usage for a small Resource List is:
    
    rl = ResourceList()
    rl.add( Resource(...) )
    rl.add( Resource(...) )
    print rl.as_xml()

    The default storage is unordered but the iterator imposes a canonical 
    order which is alphabetical by URI. If it is desired to have 
    resources listed in the order they are added then the ResourceDictOrdered
    class may be specified on creation:

    rl = ResourceList( resources_class=ResourceDictOrdered )
    
    In normal use it is expected that any Resource List Index will be
    created automatically when writing out a large Resource List in
    multiple sitemap files. However, should it be necessary to 
    explicitly create an index then this may be specified with:

    rli = ResourceList( resources_class=ResourceDictOrdered )
    rli.sitemapindex=True

    See additional descriptions in ListBaseWithIndex and ListBase.
    """

    def __init__(self, resources=None, count=None, md=None, ln=None, uri=None, 
                 allow_multifile=None, mapper=None, resources_class=ResourceListDict):
        super(ResourceList, self).__init__(resources=resources, count=count, md=md, ln=ln, uri=uri,
                                           capability_name = 'resourcelist', 
                                           allow_multifile=allow_multifile, mapper=mapper,
                                           resources_class=resources_class)

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
                raise Exception("this should not be possible")
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
