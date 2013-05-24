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
from urllib import URLopener

from list_base import ListBase
from resource import Resource
from sitemap import Sitemap

class ChangeList(ListBase):
    """Class representing an Change List"""

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = list()
        super(ChangeList, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name='changelist'
        self.capability_md='changelist'

    def add(self, resource):
        """Add a resource_change or an iterable collection to this ChangeList
      
        Allows multiple resource_change objects for the same resource (ie. URI) and
        preserves the order of addition.
        """
        if isinstance(resource, collections.Iterable):
            for r in resource:
                self.resources.append(r)
        else:
            self.resources.append(resource)

    def add_changed_resources(self, resources, change=None):
        """Add items from a ResourceContainer resources to this ChangeList

        If change is specified then the attribute is set in the Resource 
        objects created.
        """
        for resource in resources:
            rc = Resource( resource=resource, change=change )
            self.add(rc)
