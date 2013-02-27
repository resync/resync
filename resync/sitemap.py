"""Read and write ResourceSync documents as sitemaps"""

import re
import os
import sys
import logging
from xml.etree.ElementTree import ElementTree, Element, parse, tostring
import StringIO

from resource import Resource
from resource_container import ResourceContainer
from mapper import Mapper, MapperError

SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
RS_NS = 'http://www.openarchives.org/rs/terms/'

class SitemapIndexError(Exception):
    """Exception on attempt to read a sitemapindex instead of sitemap 
    or vice-versa

    Provides both a message and a place to store the etree so that
    the parse tree may be reused as a sitemapingex.
    """

    def __init__(self, message=None, etree=None):
        self.message = message
        self.etree = etree

    def __repr__(self):
        return(self.message)

class SitemapParseError(Exception):
    pass

class SitemapDupeError(Exception):
    pass

class Sitemap(object):
    """Read and write sitemaps

    Implemented as a separate class that uses ResourceContainer 
    (ResourceList or ChangeList) and Resource classes as data objects. 
    Reads and write sitemaps, including multiple file sitemaps.

    This class does not automatically handle the reading or writing
    of a sitemapindex and multiple sitemap documents. Instead it will
    take a default and throw and exception if the other case is found
    so that the calling code can handle it.
    """

    def __init__(self, pretty_xml=False, allow_multifile=True, mapper=None):
        self.logger = logging.getLogger('sitemap')
        self.pretty_xml=pretty_xml
        self.allow_multifile=allow_multifile
        self.mapper=mapper
        self.max_sitemap_entries=50000
        # Classes used when parsing
        self.resource_class=Resource
        # Information recorded for logging
        self.resources_created=0    # Set during parsing sitemap
        self.parsed_index=None      # Set True for sitemapindex, False for sitemap


    ##### Write the XML for a sitemap or sitemapindex #####

    def resources_as_xml(self, resources, num_resources=None, sitemapindex=False, fh=None):
        """Return XML for a set of resources in sitemap format
        
        Arguments:
        - resources - either an iterable or iterator of Resource objects.
        - num_resources - if not None then only that number will be written
        - sitemapindex - set True to write sitemapindex instead of sitemap
        - fh - write to filehandle fh instead of returning string

        """
        # element names depending on sitemapindex or not
        root_element = ( 'sitemapindex' if (sitemapindex) else 'urlset' )
        item_element = ( 'sitemap' if (sitemapindex) else 'url')
        # namespaces and other settings
        namespaces = { 'xmlns': SITEMAP_NS, 'xmlns:rs': RS_NS }
        root = Element(root_element, namespaces)
        if (self.pretty_xml):
            root.text="\n"
        # <rs:md>
        if (hasattr(resources,'md')):
            self.add_md_to_etree(root,resources.md)
        # <rs:ln>
        if (hasattr(resources,'ln')):
            for ln in resources.ln:
                self.add_ln_to_etree(root,ln)
        # <url> entries from either an iterable or an iterator
        for r in resources:
            e=self.resource_etree_element(r, element_name=item_element)
            root.append(e)
            if (num_resources is not None):
                num_resources-=1
                if (num_resources==0):
                    break
        # have tree, now serialize
        tree = ElementTree(root);
        xml_buf=None
        if (fh is None):
            xml_buf=StringIO.StringIO()
            fh=xml_buf
        if (sys.version_info < (2,7)):
            tree.write(xml_buf,encoding='UTF-8')
        else:
            tree.write(xml_buf,encoding='UTF-8',xml_declaration=True,method='xml')
        if (xml_buf is not None):
            return(xml_buf.getvalue())


    ##### Read/parse an XML sitemap or sitemapindex #####

    def parse_xml(self, fh=None, etree=None, resources=None, capability=None, sitemapindex=None):
        """Parse XML Sitemap from fh or etree and add resources to a
        resorces object (which must support the add method). Returns 
        the resources object.

        Also sets self.resources_created to be the number of resources created. 
        We adopt a very lax approach here. The parsing is properly namespace 
        aware but we search just for the elements wanted and leave everything 
        else alone.

        This method will read either sitemap or sitemapindex documents. Behavior
        depends on the sitemapindex parameter:
        - None - will read either
        - False - SitemapIndexError exception if sitemapindex detected
        - True - SitemapIndexError exception if sitemap detected

        Will set self.parsed_index based on whether a sitemap or sitemapindex 
        document was read:
        - False - sitemap
        - True - sitemapindex
        """
        if (resources is None):
            resources=ResourceContainer()
        if (fh is not None):
            etree=parse(fh)
        elif (etree is None):
            raise ValueError("Neither fh or etree set")
        # check root element: urlset (for sitemap), sitemapindex or bad
        root_tag = etree.getroot().tag
        resource_tag = None # will be <url> or <sitemap> depending on type
        self.parsed_index = None
        if (root_tag == '{'+SITEMAP_NS+"}urlset"):
            self.parsed_index = False
            if (sitemapindex is not None and sitemapindex):
                raise SitemapIndexError("Got sitemap when expecting sitemapindex",etree)
            resource_tag = '{'+SITEMAP_NS+"}url"
        elif (root_tag == '{'+SITEMAP_NS+"}sitemapindex"):
            self.parsed_index = True
            if (sitemapindex is not None and not sitemapindex):
                raise SitemapIndexError("Got sitemapindex when expecting sitemap",etree)
            resource_tag = '{'+SITEMAP_NS+"}sitemap"
        else:
            raise SitemapParseError("XML is not sitemap or sitemapindex")
        
        # have what we expect, read it
        in_preamble = True
        self.resources_created=0
        for e in etree.getroot().getchildren():
            # look for <rs:md> and <rs:ln>, first <url> ends
            # then look for resources in <url> blocks
            if (e.tag == resource_tag):
                in_preamble = False #any later rs:md or rs:ln is error
                r = self.resource_from_etree(e, self.resource_class)
                try:
                    resources.add( r )
                except SitemapDupeError:
                    self.logger.warning("dupe of: %s (lastmod=%s)" % (r.uri,r.lastmod))
                self.resources_created+=1
            elif (e.tag == "{"+RS_NS+"}md"):
                if (in_preamble):
                    resources.md = self.md_from_etree(e,'preamble')
                else:
                    raise SitemapParseError("Found <rs:md> after first <url> in sitemap")
            elif (e.tag == "{"+RS_NS+"}ln"):
                if (in_preamble):
                    resources.ln.append(self.ln_from_etree(e,'preamble'))
                else:
                    raise SitemapParseError("Found <rs:md> after first <url> in sitemap")
            else:
                # element we don't recognize, ignore
                # FIXME - might add check for debug?
                pass
        # check that we read to right capability document
        if (capability is not None):
            if ('capability' not in resources.md):
                if (capability == 'resourcelist'):
                    self.logger.warning('No capability specified in sitemap, assuming resourcelist')
                    resources.md['capability'] = 'resourcelist'
                else:
                    raise SitemapParseError("Expected to read a %s document, but not capability specified" %
                                 (capability))
            if (resources.md['capability'] != capability):
                raise SitemapParseError("Expected to read a %s document, got %s" %
                                 (capability,resources.md['capability']))
        # return the resource container object
        return(resources)


    ##### Resource methods #####

    def resource_etree_element(self, resource, element_name='url'):
        """Return xml.etree.ElementTree.Element representing the resource

        Returns and element for the specified resource, of the form <url> 
        with enclosed properties that are based on the sitemap with extensions
        for ResourceSync.
        """
        e = Element(element_name)
        sub = Element('loc')
        sub.text=resource.uri
        e.append(sub)
        if (resource.timestamp is not None):
            # Create appriate element for timestamp
            sub = Element('lastmod')
            sub.text = str(resource.lastmod) #W3C Datetime in UTC
            e.append(sub)
        md_atts = {}
        if (resource.change is not None):
            md_atts['change'] = resource.change
        if (resource.length is not None):
            md_atts['length'] = str(resource.length)
        if (resource.hash is not None):
            md_atts['hash'] = resource.hash
        if (resource.capability is not None):
            md_atts['capability'] = resource.capability
        if (len(md_atts)>0):
            md = Element('rs:md',md_atts)
            e.append(md)
        # add any <rs:ln>
        if (hasattr(resource,'ln') and
            resource.ln is not None):
            for ln in resource.ln:
                self.add_ln_to_etree(e,ln)
        if (self.pretty_xml):
            e.tail="\n"
        return(e)

    def resource_as_xml(self,resource,indent=' '):
        """Return string for the the resource as part of an XML sitemap

        """
        e = self.resource_etree_element(resource)
        if (sys.version_info < (2,7)):
            #must not specify method='xml' in python2.6
            return(tostring(e, encoding='UTF-8'))
        else:
            return(tostring(e, encoding='UTF-8', method='xml'))

    def resource_from_etree(self, etree, resource_class):
        """Construct a Resource from an etree

        Parameters:
         etree - the etree to parse
         resource_class - class of Resource object to create

        The parsing is properly namespace aware but we search just for 
        the elements wanted and leave everything else alone. Provided 
        there is a <loc> element then we'll go ahead and extract as much 
        as possible.
        """
        loc = etree.findtext('{'+SITEMAP_NS+"}loc")
        if (loc is None):
            raise SitemapParseError("Missing <loc> element while parsing <url> in sitemap")
        ###FIXME - test for mutliple <loc> -> error
        # must at least have a URI, make this object
        resource=resource_class(uri=loc)
        # and hopefully a lastmod datetime
        lastmod = etree.findtext('{'+SITEMAP_NS+"}lastmod")
        ###FIXME - test for multple <lastmod> -> error
        if (lastmod is not None):
            resource.lastmod=lastmod
        # then proceed to look for other resource attributes in an rs:md element
        md_elements = etree.findall('{'+RS_NS+"}md")
        if (len(md_elements)>1):
            raise SitemapParseError("Found multiple (%d) <rs:md> elements for %s", (len(md_elements),loc))
        elif (len(md_elements)==1):
            # have on element, look at attributes
            md = self.md_from_etree(md_elements[0],context=loc)
            # change type
            if ('change' in md):
                resource.change = md['change']
            if ('length' in md):
                resource.length = md['length']
            # The ResourceSync beta spec lists md5, sha-1 and sha-256 fixity
            # digest types. Parse and warn of errors ignored.
            if ('hash' in md):
                try:
                    resource.hash = md['hash']
                except ValueError as e:
                    self.logger.warning("%s in <rs:md> for %s" % (str(e),loc))
        # look for rs:ln elements (optional)
        ln_elements = etree.findall('{'+RS_NS+"}ln")
        if (len(ln_elements)>0):
            resource.ln = []
            for ln_element in ln_elements:
                resource.ln.append(self.ln_from_etree(ln_element,loc))
        return(resource)

    def md_from_etree(self, md_element, context=''):
        """Parse rs:md attributes returning a dict of the data

        Parameters:
         md_element     - etree element <rs:md>
        """
        md = {}
        # capability. Allow this to be missing but do a very simple syntax
        # check on plausible values if present
        capability = md_element.attrib.get("capability",None)
        if (capability is not None):
            if (re.match(r"^[\w\-]+$", capability) is not None):
                md['capability'] = capability
            else:
                raise SitemapParseError("Bad capability name '%s' in %s" % (capability,context))
        # modified
        modified = md_element.attrib.get("modified",None)
        if (modified is not None):
            md['modified'] = modified
        # change type
        change = md_element.attrib.get("change",None)
        if (change is not None):
            if (change not in ['created','updated','deleted'] ):
                self.logger.warning("Bad change attribute in <rs:md> for %s" % (context))
            md['change'] = change
        # content type
        type = md_element.attrib.get("type",None)
        if (type is not None):
            md['type'] = type
        # length in bytes
        length = md_element.attrib.get("length",None)
        if (length is not None):
            try:
                md['length']=int(length)
            except ValueError as e:
                raise SitemapParseError("Invalid length element in <rs:md> for %s" % (context))
        # don't attempt to parse hash values here
        hash = md_element.attrib.get("hash",None)
        if (hash is not None):
            md['hash'] = hash
        return(md)


    def ln_from_etree(self,ln_element,context=''):
        """Parse rs:ln element from an etree, returning a dict of the data

        Parameters:
         md_element     - etree element <rs:md>
        """
        ln = {}
        # href (MANDATORY)
        href = ln_element.attrib.get("href",None)
        if (href is not None):
            ln['href'] = href
        else:
            raise SitemapParseError("Missing href in <rs:ln> in %s" % (context))
        # rel (MANDATORY)
        rel = ln_element.attrib.get("rel",None)
        if (rel is not None):
            ln['rel'] = rel
        else:
            raise SitemapParseError("Missing rel in <rs:ln> in %s" % (context))
        # hash - don't attempt to parse hash values here
        hash = ln_element.attrib.get("hash",None)
        if (hash is not None):
            ln['hash'] = hash
        # length in bytes
        length = ln_element.attrib.get("length",None)
        if (length is not None):
            try:
                ln['length']=int(length)
            except ValueError as e:
                raise SitemapParseError("Invalid length attribute value in <rs:ln> for %s" % (context))
        # modified
        modified = ln_element.attrib.get("modified",None)
        if (modified is not None):
            ln['modified'] = modified
        # path
        path = ln_element.attrib.get("path",None)
        if (path is not None):
            ln['path'] = modified
        # type - content type
        type = ln_element.attrib.get("type",None)
        if (type is not None):
            ln['type'] = modified
        # pri - priority, must be a number between 1 and 999999
        pri = ln_element.attrib.get("pri",None)
        if (pri is not None):
            try:
                ln['pri']=int(pri)
            except ValueError as e:
                raise SitemapParseError("Invalid pri attribute in <rs:ln> for %s" % (context))
            if (ln['pri']<1 or ln['pri']>999999):
                raise SitemapParseError("Bad pri attribute value in <rs:ln> for %s" % (context))
        return(ln)


    ##### Metadata and links #####

    def add_md_to_etree(self, etree, md):
        """ Add <rs:md> element to the etree supplied
        """
        atts = {}
        for a in md.keys():
            # make attributes by space concatenating any capability dict values 
            # that are arrays
            value = md[a]
            if (value is None):
                # skip None values
                pass
            elif (isinstance(value, str)):
                atts[a]=value
            else:
                atts[a]=' '.join(value)
        if (len(atts)>0):
            e = Element('rs:md', atts)
            if (self.pretty_xml):
                e.tail="\n"
            etree.append(e)


    def add_ln_to_etree(self, etree, ln):
        """ Add <rs:ln> element to the etree supplied
        """
        atts = {}
        for a in ln.keys():
            # make attributes by space concatenating any capability dict values 
            # that are arrays
            value = ln[a]
            if (value is None):
                # skip None values
                pass
            elif (isinstance(value, str)):
                atts[a]=value
            else:
                atts[a]=' '.join(value)
        if (len(atts)>0):
            e = Element('rs:ln', atts)
            if (self.pretty_xml):
                e.tail="\n"
            etree.append(e)
