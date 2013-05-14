"""ResourceSync ResourceDump object

A ResourceDump is a set of content package resources with 
some metadata for each resource. 

The ResourceDump object may also contain metadata and links.

Described in specification at:
http://www.openarchives.org/rs/resourcesync#ResourceDump
"""

from resource_list import ResourceList

class ResourceDump(ResourceList):
    """Class representing an Resource Dump

    A ResourceDump comprises a set of content packages that are
    the resources listed. Properties much Like a ResourceList
    and implemented as a sub-class of ResourceList.
    """

    def __init__(self, resources=None, md=None, ln=None, allow_multifile=None, mapper=None):
        super(ResourceDump, self).__init__(resources=resources, md=md, ln=ln, mapper=mapper)
        self.capability_name = 'resourcedump'
        self.capability_md = 'resourcedump'
