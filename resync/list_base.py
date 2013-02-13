"""Base class for ResourceSync capabilities with list of resources

Adds Sitemap based IO to the ResourceContainer class and is
intended as the base class for ResourceList, ChangeList,
CapabilityList etc.. Adds common read() and write() methods.
"""

import collections
import os
from datetime import datetime
import re
import sys
import StringIO
from urllib import URLopener

from resource_container import ResourceContainer
from sitemap import Sitemap

class ListBase(ResourceContainer):
    """Class that adds Sitemap based IO to ResourceContainer
    """

    def __init__(self, resources=None, md=None, ln=None):
        super(ListBase, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name = 'unknown'
        self.capability_md = 'unknown'
        self.sitemapindex=False

    def __iter__(self):
        """Default to iterator provided by resources object"""
        return(iter(self.resources))

    def __len__(self):
        """Number of entries in this list"""
        return(len(self.resources))

    ##### INPUT #####

    def read(self,uri=None,**kwargs):
        s = Sitemap(**kwargs)
        s.read(uri=uri,resources=self,capability=self.capability_md)
        self.num_files = s.sitemaps_created

    def parse(self,uri=None,fh=None,**kwargs):
        """Parse a single XML document for this list

        Does not handle the case of sitemapindex+sitemaps ResourceList
        """
        if (uri is not None):
            try:
                fh = URLopener().open(uri)
            except IOError as e:
                raise Exception("Failed to load sitemap/sitemapindex from %s (%s)" % (uri,str(e)))
        if (fh is None):
            raise Exception("Nothing to parse")
        s = Sitemap(**kwargs)
        s.sitemap_parse_xml(fh=fh,resources=self,capability=self.capability_md)
        self.num_files = s.sitemaps_created

    ##### OUTPUT #####

    def as_xml(self,**kwargs):
        """Return XML serialization of this list

        FIXME - What can we do here to deal with the case where the
        list is too big. Applies only to ResourceList since v0.5"""
        self.default_capability_and_modified()
        s = Sitemap(**kwargs)
        return s.resources_as_xml(self,sitemapindex=self.sitemapindex)

    def write(self,**kwargs):
        """Write one or perhaps multiple sitemap/sitemapindex XML documents
        """
        self.default_capability_and_modified()
        basename = "/tmp/resynclist.xml"
        if ('basename' in kwargs):
            basename = kwargs['basename']
            del kwargs['basename']
        s = Sitemap(**kwargs)
        # FIXME - add in sitemapindex option
        return s.write(resources=self,basename=basename)
