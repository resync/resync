"""ResourceSync capability_list object

An capability_list is a set of capabilitys with some metadata for each 
capability. 

The capability_list object may also contain metadata and links.
"""

import collections
import os
from datetime import datetime
import re
import sys
import StringIO
from urllib import URLopener

from resource import Resource
from resource_container import ResourceContainer
from sitemap import Sitemap

class CapabilityListDict(dict):
    """Default implementation of class to store capabilitys in CapabilityList

    Key properties of this class are:
    - has add(resource) method
    - is iterable and results given in alphanumeric order by resource.uri
    """

    def __iter__(self):
        """Iterator over all the resources in this capability_list"""
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
            raise ResourceListDupeError("Attempt to add resource already in capability_list") 
        self[uri]=resource

class CapabilityListDupeError(Exception):
    pass

class CapabilityList(ResourceContainer):
    """Class representing an capability_list of resources

    This same class is used for both the source and the destination
    and is the central point of comparison the decide whether they
    are in sync or what needs to be copied to bring the destinaton
    into sync.

    An capability_list will admit only one resource with any given URI.

    Storage is unordered but the iterator imposes a canonical order
    which is currently alphabetical by URI.
    """

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = CapabilityListDict()
        super(CapabilityList, self).__init__(resources=resources, md=md, ln=ln)
        self.capability='capabilitylist'

    def __iter__(self):
        """Iterator over all the resources in this capability_list"""
        return(iter(self.resources))

    def __len__(self):
        """Return number of resources in this capability_list"""
        return(len(self.resources))

    def add(self, resource, replace=False):
        """Add a resource or an iterable collection of resources

        Will throw a ValueError if the resource (ie. same uri) already
        exists in the capability_list, unless replace=True.
        """
        if isinstance(resource, collections.Iterable):
            for r in resource:
                self.resources.add(r,replace)
        else:
            self.resources.add(resource,replace)

    def add_capability(self,rc,uri):
        """Specific add function for capabilities
        
        Takes ResourceContainer as the first argument from which the
        capability name is extracted, and the URI as second argument"""
        self.add( Resource(uri=uri,capability=rc.capability) )

    def parse(self,uri=None,fh=None):
        if (uri is not None):
            try:
                fh = URLopener().open(uri)
            except IOError as e:
                raise Exception("Failed to load sitemap/sitemapindex from %s (%s)" % (uri,str(e)))
        if (fh is None):
            raise Exception("Nothing to parse")
        s = Sitemap()
        s.sitemap_parse_xml(fh=fh,resources=self,capability=self.capability)

    def as_xml(self,**kwargs):
        """Return XML serialization of this capability list"""
        self.default_capability_and_modified()
        s = Sitemap(**kwargs)
        return s.resources_as_xml(self)
