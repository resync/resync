"""ResourceSync ResourceDumpManifest object.

A ResourceDumpManifest lists the set of files/resources included
within a content package that is included in a ResourceDump.

The ResourceDumpManifest object may also contain metadata and links.

Described in specification at:
http://www.openarchives.org/rs/resourcesync#ResourceDumpManifest
"""

from .resource_list import ResourceList


class ResourceDumpManifest(ResourceList):
    """Class representing a Resource Dump Manifest.

    A ResourceDumpManifest comprises a set of files/resources
    in a content package. Properties much Like a ResourceList
    and implemented as a sub-class of ResourceList.
    """

    def __init__(self, resources=None, md=None, ln=None,
                 uri=None, allow_multifile=None, mapper=None,
                 spec_version='1.1', add_lastmod=False):
        """Initialize ResourceDumpManifest."""
        super(ResourceDumpManifest, self).__init__(
            resources=resources, md=md, ln=ln, uri=uri, mapper=mapper,
            spec_version=spec_version, add_lastmod=add_lastmod)
        self.capability_name = 'resourcedump-manifest'
