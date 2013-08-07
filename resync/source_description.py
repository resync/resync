"""ResourceSync Description object

A ResourceSync Description enumerates the Capability Lists 
offered by a Source. Since a Source has one Capability List
per set of resources that it distinguishes, the 
ResourceSync Description will enumerate as many Capability 
Lists as the Source has distinct sets of resources.

The ResourceSync Description can only be based on the 
<urlset> format. 

See: http://www.openarchives.org/rs/resourcesync#ResourceSyncDesc

May also contain metadata and links like other ResourceSync
document.
"""

import collections

from resource import Resource
from resource_set import ResourceSet
from list_base import ListBase

class SourceDescription(ListBase):
    """Class representing the set of Capability Lists supported

    Will admit only one resource with any given URI.

    Storage is unordered but the iterator imposes a canonical order
    which is currently alphabetical by URI.
    """

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = ResourceSet()
        super(SourceDescription, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name='description'
        self.capability_md='description'
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

    def add_capability_list(self,uri=None):
        """Add a capability list"""
        self.add( Resource(uri=uri,capability='capabilitylist') )
