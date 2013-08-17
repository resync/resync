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
        super(SourceDescription, self).__init__(resources=resources, md=md, ln=ln,
                                                capability_name='description')
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

    def add_capability_list(self,capability_list=None):
        """Add a capability list

        Adds either a CapabiltyList object specified in capability_list
        or else creates a Resource with the URI given in capability_list
        and adds that to the Source Description
        """
        if (hasattr(capability_list,'uri')):
            r = Resource( uri=capability_list.uri,
                          capability=capability_list.capability_name )
            if (capability_list.describedby is not None):
                r.link_add( rel='describedby', href=capability_list.describedby )
        else:
            r = Resource( uri=capability_list,
                          capability='capabilitylist')
        self.add( r )
