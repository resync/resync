"""ResourceSync Capability List object

An Capability List is a set of capabilitys with some metadata for 
each capability. The Capability List object may also contain metadata 
and links like other lists.
"""

import collections

from resource import Resource
from resource_set import ResourceSet
from list_base import ListBase
from sitemap import Sitemap

class CapabilitySet(ResourceSet):
    """Class for storage of resources in a Capability List

    Extends the ResourceSet to add checks to ensure that there are 
    never two entries for the same resource, and that values are 
    returned in the canonical order.
    """

    def __init__(self):
        self.order = [ 'resourcelist', 'resourcedump',
                       'changelist', 'changedump',
                       'resourcelist-archive', 'resourcedump-archive',
                       'changelist-archive', 'changedump-archive' ]

    def __iter__(self):
        """Iterator over all the resources in capability order

        Deals with the case of unknown capabilities or duplicate entries
        by using uri order for duplicates and adding any unknown ones 
        at the end
        """
        self._iter_next_list = []
        # look through all resources and build capability to uri index
        uris = {}
        for uri in self.keys():
            cap = self[uri].capability
            if (cap not in uris):
                uris[cap]=[]
            uris[cap].append(uri)
        # now build list or uris in order for iterator
        for cap in uris:
            for uri in sorted(uris[cap]):
                self._iter_next_list.append(uri)
        self._iter_next_list.reverse()
        return(iter(self._iter_next, None))

    def _iter_next(self):
        if (len(self._iter_next_list)>0):
            return(self[self._iter_next_list.pop()])
        else:
            return(None)


class CapabilityList(ListBase):
    """Class representing a Capability List

    An Capability List will admit only one resource with any given 
    URI. The iterator over resources is expected to return them in
    canonical order of capability names as defined in main specification
    section 9.2 and archives specification section 6.
    """

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = CapabilitySet()
        super(CapabilityList, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name='capabilitylist'
        self.capability_md='capabilitylist'
        self.md['from']=None #usually don't want a from date

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
