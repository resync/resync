"""ResourceSync ChangeList object

A ChangeList is a list of resource descriptions which includes
both metadata associated with the resource at some point in
time, and also metadata about a change that may have occurred
to bring the resource to that states. These descriptions
are Resource objects.

Different from an resource_list, a change_list may include multiple
descriptions for the same resource. The change_list is ordered
from first entry to last entry. 

Different from an resource_list, dereference by a URI yields a 
ChangeList containing descriptions pertaining to that 
particular resource.
"""

import collections

from resource_container import ResourceContainer
from resource import Resource

class ChangeList(ResourceContainer):
    """Class representing an Change List"""

    def __init__(self, resources=None, capabilities=None):
        if (resources is None):
            resources = list()
        super(ChangeList, self).__init__(resources, capabilities)

    def __len__(self):
        """Number of entries in this change_list"""
        return(len(self.resources))

    def add(self, resource):
        """Add a resource_change or an iterable collection to this ChangeList
      
        Allows multiple resourec_change objects for the same resource (ie. URI) and
        preserves the order of addition.
        """
        if isinstance(resource, collections.Iterable):
            for r in resource:
                self.resources.append(r)
        else:
            self.resources.append(resource)

    def add_changed_resources(self, resources, changeid=None, change=None):
        """Add items from a ResourceContainer resources to this ChangeList

        If changeid or change is specified then these attributes
        are set in the Resource objects created.
        """
        for resource in resources:
            rc = Resource( resource=resource, changeid=changeid, change=change )
            self.add(rc)
