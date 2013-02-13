"""ResourceSync capability list index object

A capability list index is a set of capability lists which 
may also contain metadata and links.
"""

import collections

from resource import Resource
from resource_set import ResourceSet
from list_base import ListBase

class CapabilityListIndex(ListBase):
    """Class representing an capability list index

    An capability list index will admit only one resource with any 
    given URI.

    Storage is unordered but the iterator imposes a canonical order
    which is currently alphabetical by URI.
    """

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = ResourceSet()
        super(CapabilityListIndex, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name='capabilitylistindex'
        self.capability_md='capabilitylist'
        self.sitemapindex=True

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

    def add_capability_list(self,uri):
        """Specific add function for capability_lists
        
        Takes uri and adds Resource with that URI
        """
        self.add( Resource(uri=uri) )
