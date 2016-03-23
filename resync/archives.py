"""ResourceSync Archive objects

The ResourceSync Archives specification
http://www.openarchives.org/rs/archives specifies capabilities
that provide archives of the 4 core capabilities. While some 
optional attributes are different the basic structure is the
same for the Resource List Archive, Change List Archive, 
Resource Dump Archive, and Change Dump Archive. 
"""

import collections
try: #python3
    from urllib.request import URLopener
except ImportError: #python2
    from urllib import URLopener

from .list_base_with_index import ListBaseWithIndex
from .resource import Resource
from .sitemap import Sitemap

class ResourceListArchive(ListBaseWithIndex):
    """Class representing an Change List Archive"""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 resources_class=None):
        self.resources_class = list if resources_class is None else resources_class
        if (resources is None):
            resources = self.resources_class()
        super(ResourceListArchive, self).__init__(resources=resources, md=md, ln=ln, uri=uri,
                                                  capability_name='resourcelist-archive')

class ChangeListArchive(ListBaseWithIndex):
    """Class representing an Change List Archive"""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 resources_class=None):
        super(ChangeListArchive, self).__init__(resources=resources, md=md, ln=ln, uri=uri,
                                                capability_name='changelist-archive')

class ResourceDumpArchive(ListBaseWithIndex):
    """Class representing an Resource Dump Archive"""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 resources_class=None):
        super(ResourceDumpArchive, self).__init__(resources=resources, md=md, ln=ln, uri=uri,
                                                  capability_name='resourcedump-archive',
                                                  resources_class=resources_class)

class ChangeDumpArchive(ListBaseWithIndex):
    """Class representing an Change Dump Archive"""

    def __init__(self, resources=None, md=None, ln=None, uri=None,
                 resources_class=None):
        super(ChangeDumpArchive, self).__init__(resources=resources, md=md, ln=ln, uri=uri,
                                                capability_name='changedump-archive',
                                                resources_class=resources_class)
