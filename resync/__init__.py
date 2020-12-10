"""Module config for resync."""

from ._version import __version__

# Enable easy import for core classes, e.g.
# from resync import Resource
from .source_description import SourceDescription
from .capability_list import CapabilityList
from .resource_list import ResourceList
from .change_list import ChangeList
from .resource_dump import ResourceDump
from .resource_dump_manifest import ResourceDumpManifest
from .change_dump import ChangeDump
from .archives import ResourceListArchive, ResourceDumpArchive, ChangeListArchive, ChangeDumpArchive
from .resource import Resource
