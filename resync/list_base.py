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

    resources - an iterable of resources

    count - add optional explicit setting of the number of items in 
        resources which is useful when this is an iterator/generator.
        Is used instead of trying len(resources)

    md - metadata information for the list (<rs:md>)
     
    ln - link information for the list (<rs:ln>)

    sitemapindex - defaults to False, set True if this is an index object
    """

    def __init__(self, resources=None, count=None, md=None, ln=None, uri=None, 
                 capability_name='unknown'):
        super(ListBase, self).__init__(resources=resources, md=md, ln=ln, uri=uri,
                                       capability_name=capability_name)
        self.count = count
        self.sitemapindex = False
        self.pretty_xml = False
        #
        self.logger = logging.getLogger('list_base')
        self.bytes_read = 0
        self.parsed_index = None

    def __iter__(self):
        """Default to iterator provided by resources object"""
        return(iter(self.resources))

    def __len__(self):
        """Number of entries in this list

        To handle the case where self.resources is a generator or an iterator and
        thus cannot provide len(...) we first check to see whether an explicit
        self.count is set and return that, otherwise just do len(...).

        Typical usage would be to set this on instantiation:
           list = ListBase( resources=my_generator, count=count)
           print list.as_xml()
        """
        if (self.count is not None):
            return(self.count)
        return(len(self.resources))

    ##### INPUT #####

    def read(self,uri=None):
        """Default case is just to parse document at this URI

        Intention is that the read() method may be overridden to support reading
        of compound documents in more then one sitemapindex/sitemap.
        """
        self.parse(uri=uri)

    def parse(self,uri=None,fh=None):
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
        s = self.new_sitemap()
        s.parse_xml(fh=fh,resources=self,capability=self.capability_name,sitemapindex=False)
        self.parsed_index = s.parsed_index
        
    ##### OUTPUT #####

    def as_xml(self):
        """Return XML serialization of this list

        This code does not support the case where the list is too big for 
        a single XML document.
        """
        self.default_capability()
        s = self.new_sitemap()
        return s.resources_as_xml(self,sitemapindex=self.sitemapindex)

    def write(self,basename="/tmp/resynclist.xml"):
        """Write a single sitemap or sitemapindex XML document

        Must be overridden to support multi-file lists.
        """
        self.default_capability()
        fh = open(basename,'w')
        s = self.new_sitemap()
        s.resources_as_xml(self,fh=fh,sitemapindex=self.sitemapindex)
        fh.close()

    ##### UTILITY #####

    def new_sitemap(self):
        """Create new Sitemap object with default settings"""
        return Sitemap(pretty_xml=self.pretty_xml)
