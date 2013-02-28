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
import logging
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
        self.sitemapindex = False
        #
        self.logger = logging.getLogger('list_base')
        self.bytes_read = 0
        self.parsed_index = None

    def __iter__(self):
        """Default to iterator provided by resources object"""
        return(iter(self.resources))

    def __len__(self):
        """Number of entries in this list"""
        return(len(self.resources))

    ##### INPUT #####

    def read(self,uri=None,**kwargs):
        """Default case is just to parse document at this URI

        Intention is that the read() method may be overridden to support reading
        of compound documents in more then one sitemapindex/sitemap.
        """
        self.parse(uri=uri,**kwargs)

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
        s.parse_xml(fh=fh,resources=self,capability=self.capability_md,sitemapindex=False)
        self.parsed_index = s.parsed_index
        
    ##### OUTPUT #####

    def as_xml(self,**kwargs):
        """Return XML serialization of this list

        This code does not support the case where the list is too big for 
        a single XML document.
        """
        self.default_capability_and_modified()
        s = Sitemap(**kwargs)
        return s.resources_as_xml(self,sitemapindex=self.sitemapindex)

    def write(self,basename="/tmp/resynclist.xml",**kwargs):
        """Write a single sitemap or sitemapindex XML document

        Must be overridden to support multi-file lists.
        """
        self.default_capability_and_modified()
        fh = open(basename,'w')
        s = Sitemap(**kwargs)
        s.resources_as_xml(self,fh=fh,sitemapindex=self.sitemapindex)
        fh.close()
