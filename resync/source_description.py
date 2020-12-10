"""ResourceSync Source Description object.

A ResourceSync Source Description enumerates the Capability
Lists offered by a Source. Since a Source has one Capability
List per set of resources that it distinguishes, the
ResourceSync Source Description will enumerate as many
Capability Lists as the Source has distinct sets of resources.

The ResourceSync Source Description is based on the <urlset>
format. The specification allows for a very large Source Descriptions
to use and index based on a <sitemapindex>, though this is probably
rarely necessary!

There is no meaning in the order of description of sets of resources
in a Source Description so the default is to store these descriptions
as a set (ResourceSet).

May also contain metadata and links like other ResourceSync
documents.

See: http://www.openarchives.org/rs/resourcesync#SourceDesc
"""

import collections.abc

from resync.resource import Resource
from resync.resource_set import ResourceSet
from resync.list_base_with_index import ListBaseWithIndex


class SourceDescription(ListBaseWithIndex):
    """Class representing the set of Capability Lists supported.

    Will admit only one resource with any given URI.

    Storage is unordered but the iterator imposes a canonical order
    which is currently alphabetical by URI. Pass in a resources object
    to override.
    """

    def __init__(self, resources=None, md=None, ln=None):
        """Initialize based on superclass ListBaseWithIndex."""
        super(SourceDescription, self).__init__(resources=resources, md=md, ln=ln,
                                                capability_name='description',
                                                resources_class=ResourceSet)
        self.md['from'] = None  # usually don't want a from date

    def add(self, resource, replace=False):
        """Add a resource or an iterable collection of resources.

        Will throw a ValueError if the resource (ie. same uri) already
        exists in the capability_list, unless replace=True.
        """
        if isinstance(resource, collections.abc.Iterable):
            for r in resource:
                self.resources.add(r, replace)
        else:
            self.resources.add(resource, replace)

    def add_capability_list(self, capability_list=None):
        """Add a capability list.

        Adds either a CapabiltyList object specified in capability_list
        or else creates a Resource with the URI given in capability_list
        and adds that to the Source Description
        """
        if (hasattr(capability_list, 'uri')):
            r = Resource(uri=capability_list.uri,
                         capability=capability_list.capability_name)
            if (capability_list.describedby is not None):
                r.link_set(rel='describedby', href=capability_list.describedby)
        else:
            r = Resource(uri=capability_list,
                         capability='capabilitylist')
        self.add(r)
