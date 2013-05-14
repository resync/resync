"""ResourceSync capability_list object

An capability_list is a set of capabilitys with some metadata for each 
capability. 

The capability_list object may also contain metadata and links.
"""

import collections

from resource import Resource
from resource_set import ResourceSet
from list_base import ListBase
from sitemap import Sitemap

class CapabilityList(ListBase):
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
            resources = ResourceSet()
        super(CapabilityList, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name='capabilitylist'
        self.capability_md='capabilitylist'

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

    def add_capability(self,capability=None,uri=None,name=None):
        """Specific add function for capabilities
        
        Takes either:
        - a capability object (derived from ListBase) as the first argument 
          from which the capability name is extracted
        - or a plain name string
        and
        - the URI of the capability
        """
        if (capability is not None):
            name = capability.capability_md
        self.add( Resource(uri=uri,capability=name) )

    def has_capability(self,name=None):
        """True if the Capability List includes the named capability"""
        return( self.capability(name) is not None )

    def capability(self,name=None):
        """Return information about the requested capability from this list

        Will return None if there is no information about the requested capability
        """
        for r in self.resources:
            if (r.capability == name):
                return(r)
        return(None)
