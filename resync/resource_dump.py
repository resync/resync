"""ResourceSync Resource Dump object.

A Resource Dump is a descriptions of a set of content packages
that contain copies of resources at a point in time.

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

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 allow_multifile=None, mapper=None,
                 spec_version='1.0', include_lastmod=True):
        """Initialize ResourceDump."""
        super(ResourceDump, self).__init__(
            resources=resources, md=md, ln=ln, uri=uri, mapper=mapper,
            spec_version=spec_version, include_lastmod=include_lastmod)
        self.capability_name = 'resourcedump'

    def write(self, basename="/tmp/resource_dump.xml"):
        """Write out a ResourceDump document.

        FIXME - should there be support for a tie to writing out
        the Dump files themselves, complete with Resource Dump
        Manifests?
        """
        super(ResourceDump, self).write(basename)
