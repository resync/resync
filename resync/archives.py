"""ResourceSync Archive objects.

The ResourceSync Archives specification
http://www.openarchives.org/rs/archives specifies capabilities
that provide archives of the 4 core capabilities. While some
optional attributes are different the basic structure is the
same for the Resource List Archive, Change List Archive,
Resource Dump Archive, and Change Dump Archive.
"""

import collections

from .list_base_with_index import ListBaseWithIndex
from .resource import Resource
from .sitemap import Sitemap


class ResourceListArchive(ListBaseWithIndex):
    """Class representing an Resource List Archive."""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 spec_version='1.1', add_lastmod=False,
                 resources_class=None):
        """Initialize ResourceListArchive."""
        self.resources_class = list if resources_class is None else resources_class
        if (resources is None):
            resources = self.resources_class()
        super(ResourceListArchive, self).__init__(
            resources=resources, md=md, ln=ln, uri=uri,
            capability_name='resourcelist-archive',
            spec_version=spec_version, add_lastmod=add_lastmod)


class ChangeListArchive(ListBaseWithIndex):
    """Class representing an Change List Archive."""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 spec_version='1.1', add_lastmod=False,
                 resources_class=None):
        """Initialize ChangeListArchive."""
        super(ChangeListArchive, self).__init__(
            resources=resources, md=md, ln=ln, uri=uri,
            capability_name='changelist-archive',
            spec_version=spec_version, add_lastmod=add_lastmod)


class ResourceDumpArchive(ListBaseWithIndex):
    """Class representing an Resource Dump Archive."""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 spec_version='1.1', add_lastmod=False,
                 resources_class=None):
        """Initialize ResourceDumpArchive."""
        super(ResourceDumpArchive, self).__init__(
            resources=resources, md=md, ln=ln, uri=uri,
            capability_name='resourcedump-archive',
            spec_version=spec_version, add_lastmod=add_lastmod,
            resources_class=resources_class)


class ChangeDumpArchive(ListBaseWithIndex):
    """Class representing an Change Dump Archive."""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 spec_version='1.1', add_lastmod=False,
                 resources_class=None):
        """Initialize ChangeDumpArchive."""
        super(ChangeDumpArchive, self).__init__(
            resources=resources, md=md, ln=ln, uri=uri,
            capability_name='changedump-archive',
            spec_version=spec_version, add_lastmod=add_lastmod,
            resources_class=resources_class)
