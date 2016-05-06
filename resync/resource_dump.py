"""ResourceSync Resource Dump object.

A Resource Dump is a set of content package resources with 
some metadata for each resource. 

The Resource Dump object may also contain metadata and links.

Described in specification at:
http://www.openarchives.org/rs/resourcesync#ResourceDump
"""

from .resource_list import ResourceList

class ResourceDump(ResourceList):
    """Class representing an Resource Dump.

    A Resource Dump comprises a set of content packages that are
    the resources listed. Properties similar to a ResourceList
    and implemented as a sub-class of ResourceList.

    See the Dump class for details of how to create a Resource
    Dump from a ResourceList.
    """

    def __init__(self, resources=None, md=None, ln=None, uri=None, allow_multifile=None, mapper=None):
        """Initialize ResourceDump."""
        super(ResourceDump, self).__init__(resources=resources, md=md, ln=ln, uri=uri, 
                                           mapper=mapper)
        self.capability_name='resourcedump'

    def write(self, basename="/tmp/resource_dump.xml", dumpfile=None):
        """Write out a ResourceDump document and optionally also the dump files.

        Dump files will be written if the dumpfile argument is set to a base
        filename.
        """
        super(ResourceDump,self).write(basename)
