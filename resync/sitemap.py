"""Read and write ResourceSync documents as sitemaps"""

import re
import os
import sys
import logging
from urllib import URLopener
from xml.etree.ElementTree import ElementTree, Element, parse, tostring
from datetime import datetime
import StringIO

from resource import Resource
from resource_container import ResourceContainer
from mapper import Mapper, MapperError
from url_authority import UrlAuthority

SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
RS_NS = 'http://www.openarchives.org/rs/terms/'

class SitemapIndexError(Exception):
    """Exception on attempt to read a sitemapindex instead of sitemap"""

    def __init__(self, message=None, etree=None):
        self.message = message
        self.etree = etree

    def __repr__(self):
        return(self.message)

class SitemapIndex(ResourceContainer):
    """Reuse a ResourceContainer to hold the set of sitemaps"""
    pass

class SitemapError(Exception):
    pass

class SitemapDupeError(Exception):
    pass

class Sitemap(object):
    """Read and write sitemaps

    Implemented as a separate class that uses ResourceContainer 
    (ResourceList or ChangeList) and Resource classes as data objects. 
    Reads and write sitemaps, including multiple file sitemaps.
    """

    def __init__(self, pretty_xml=False, allow_multifile=True, mapper=None):
        self.logger = logging.getLogger('sitemap')
        self.pretty_xml=pretty_xml
        self.allow_multifile=allow_multifile
        self.mapper=mapper
        self.max_sitemap_entries=50000
        self.check_url_authority=False
        # Classes used when parsing
        self.resource_class=Resource
        # Information recorded for logging
        self.resources_created=None # Set during parsing sitemap
        self.sitemaps_created=None  # Set during parsing sitemapindex
        self.content_length=None    # Size of last sitemap read
        self.bytes_read=0           # Aggregate of content_length values
        self.change_list_read=None  # Set true if change_list read
        self.read_type=None         # Either sitemap/sitemapindex/change_list/change_listindex

    ##### General sitemap methods that also handle sitemapindexes #####

    def write(self, resources=None, basename='/tmp/sitemap.xml'):
        """Write one or a set of sitemap files to disk

        resources is a ResourceContainer that may be an ResourceList or
        a ChangeList. This may be a generator so data is read as needed
        and length is determined at the end.

        basename is used as the name of the single sitemap file or the 
        sitemapindex for a set of sitemap files.

        Uses self.max_sitemap_entries to determine whether the resource_list can 
        be written as one sitemap. If there are more entries and 
        self.allow_multifile is set true then a set of sitemap files, 
        with an sitemapindex, will be written.
        """
        # Access resources trough iterator only
        resources_iter = iter(resources)
        ( chunk, next ) = self.get_resources_chunk(resources_iter)
        if (next is not None):
            # Have more than self.max_sitemap_entries => sitemapindex
            if (not self.allow_multifile):
                raise Exception("Too many entries for a single sitemap but multifile disabled")
            # Work out how to name the sitemaps, attempt to add %05d before ".xml$", else append
            sitemap_prefix = basename
            sitemap_suffix = '.xml'
            if (basename[-4:] == '.xml'):
                sitemap_prefix = basename[:-4]
            # Use iterator over all resources and count off sets of
            # max_sitemap_entries to go into each sitemap, store the
            # names of the sitemaps as we go
            sitemaps={}
            while (len(chunk)>0):
                file = sitemap_prefix + ( "%05d" % (len(sitemaps)) ) + sitemap_suffix
                self.logger.info("Writing sitemap %s..." % (file))
                f = open(file, 'w')
                f.write(self.resources_as_xml(chunk))
                f.close()
                # Record timestamp
                sitemaps[file] = os.stat(file).st_mtime
                # Get next chunk
                ( chunk, next ) = self.get_resources_chunk(resources_iter,next)
            self.logger.info("Wrote %d sitemaps" % (len(sitemaps)))
            f = open(basename, 'w')
            self.logger.info("Writing sitemapindex %s..." % (basename))
            f.write(self.sitemapindex_as_xml(sitemaps=sitemaps,resource_list=resources))
            f.close()
            self.logger.info("Wrote sitemapindex %s" % (basename))
        else:
            f = open(basename, 'w')
            self.logger.info("Writing sitemap %s..." % (basename))
            f.write(self.resources_as_xml(chunk))
            f.close()
            self.logger.info("Wrote sitemap %s" % (basename))

    def get_resources_chunk(self, resource_iter, first=None):
        """Return next chunk of resources from resource_iter, and next item
        
        If first parameter is specified then this will be prepended to
        the list.

        The chunk will contain self.max_sitemap_entries if the iterator 
        returns that many. next will have the value of the next value from
        the iterator, providing indication of whether more is available. 
        Use this as first when asking for the following chunk.
        """
        chunk = []
        next = None
        if (first is not None):
            chunk.append(first)
        for r in resource_iter:
            chunk.append(r)
            if (len(chunk)>self.max_sitemap_entries):
                break
        if (len(chunk)>self.max_sitemap_entries):
            next = chunk.pop()
        return(chunk,next)

    def read(self, uri=None, resources=None, index_only=False):
        """Read sitemap from a URI including handling sitemapindexes

        Returns the resource_list or change_list. 

        If index_only is True then individual sitemaps references in a sitemapindex
        will not be read. This will result in no resources being returned and is
        useful only to read the metadata and links listed in the sitemapindex.

        Will set self.read_type to a string value sitemap/sitemapindex/change_list/change_listindex
        depleding on the type of the file expected/read.

        Includes the subtlety that if the input URI is a local file and is a 
        sitemapindex which contains URIs for the individual sitemaps, then these
        are mapped to the filesystem also.
        """
        try:
            fh = URLopener().open(uri)
        except IOError as e:
            raise Exception("Failed to load sitemap/sitemapindex from %s (%s)" % (uri,str(e)))
        # Get the Content-Length if we can (works fine for local files)
        try:
            self.content_length = int(fh.info()['Content-Length'])
            self.bytes_read += self.content_length
            self.logger.debug( "Read %d bytes from %s" % (self.content_length,uri) )
        except KeyError:
            # If we don't get a length then c'est la vie
            self.logger.debug( "Read ????? bytes from %s" % (uri) )
            pass
        self.logger.info( "Read sitemap/sitemapindex from %s" % (uri) )
        etree = parse(fh)
        # check root element: urlset (for sitemap), sitemapindex or bad
        self.sitemaps_created=0
        root = etree.getroot()
        # assume resource_list but look to see whether this is a change_list 
        # as indicated with rs:type="change_list" on the root
        self.change_list_read = False
        self.read_type = 'sitemap'
        root_type = root.attrib.get('{'+RS_NS+'}type',None)
        if (root_type is not None):
            if (root_type == 'change_list'):
                self.change_list_read = True
            else:
                self.logger.info("Bad value of rs:type on root element (%s), ignoring" % (root_type))
        if (self.change_list_read):
            self.read_type = 'change_list'
        # now have make sure we have a place to put the data we read
        if (resources is None):
            resources=ResourceContainer()
        # sitemap or sitemapindex?
        if (root.tag == '{'+SITEMAP_NS+"}urlset"):
            self.logger.info( "Parsing as sitemap" )
            self.sitemap_parse_xml(etree=etree, resources=resources)
            self.sitemaps_created+=1
        elif (root.tag == '{'+SITEMAP_NS+"}sitemapindex"):
            self.read_type += 'index'
            if (not self.allow_multifile):
                raise Exception("Got sitemapindex from %s but support for sitemapindex disabled" % (uri))
            self.logger.info( "Parsing as sitemapindex" )
            sitemaps=self.sitemapindex_parse_xml(etree=etree)
            sitemapindex_is_file = self.is_file_uri(uri)
            if (index_only):
                return(resources)
            # now loop over all entries to read each sitemap and add to resources
            self.logger.info( "Now reading %d sitemaps" % len(sitemaps.uris()) )
            for sitemap_uri in sorted(sitemaps.uris()):
                if (sitemapindex_is_file):
                    if (not self.is_file_uri(sitemap_uri)):
                        # Attempt to map URI to local file
                        remote_uri = sitemap_uri
                        sitemap_uri = self.mapper.src_to_dst(remote_uri)
                else:
                    # The individual sitemaps should be at a URL (scheme/server/path)
                    # that the sitemapindex URL can speak authoritatively about
                    if (self.check_url_authority and
                        not UrlAuthority(uri).has_authority_over(sitemap_uri)):
                        raise Exception("The sitemapindex (%s) refers to sitemap at a location it does not have authority over (%s)" % (uri,sitemap_uri))
                try:
                    fh = URLopener().open(sitemap_uri)
                except IOError as e:
                    raise Exception("Failed to load sitemap from %s listed in sitemap index %s (%s)" % (sitemap_uri,uri,str(e)))
                # Get the Content-Length if we can (works fine for local files)
                try:
                    self.content_length = int(fh.info()['Content-Length'])
                    self.bytes_read += self.content_length
                except KeyError:
                    # If we don't get a length then c'est la vie
                    pass
                self.logger.info( "Read sitemap from %s (%d)" % (sitemap_uri,self.content_length) )
                self.sitemap_parse_xml( fh=fh, resources=resources )
                self.sitemaps_created+=1
        else:
            raise ValueError("XML read from %s is not a sitemap or sitemapindex" % (uri))
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
            raise SitemapError("Missing <loc> element while parsing <url> in sitemap")
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
            raise SitemapError("Found multiple (%d) <rs:md> elements for %s", (len(md_elements),loc))
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
                print "## " + md['hash']
                try:
                    resource.hash = md['hash']
                except ValueError as e:
                    self.logger.warning("%s in <rs:md> for %s" % (str(e),loc))
        # look for rs:ln elements (optional)
        ln_elements = etree.findall('{'+SITEMAP_NS+"}ln")
        if (len(ln_elements)>0):
            self.logger.warning("Ignored <rs:ln> element(s) for %s, FIXME" % (loc))
        return(resource)

    def md_from_etree(self, md_element, context=''):
        """Parse rs:md attributesConstruct a Resource from an etree

        Parameters:
         md_element     - etree element <rs:md>
        """
        md = {}
        # capability
        capability = md_element.attrib.get("capability",None)
        if (capability is not None):
            if (capability in ('resourcelist','changelist',
                               'resourcedump','changedump',
                               'resourcedump-manifest','changedump-manifest',
                               'capabilitylist')):
                md['capability'] = capability
            else:
                raise ValueError("Bad capability name '%s' in %s" % (capability,context))
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
                raise Exception("Invalid length element in <rs:md> for %s" % (context))
        # don't attempt to parse hash values here
        hash = md_element.attrib.get("hash",None)
        if (hash is not None):
            md['hash'] = hash
        return(md)

    def ln_from_etree(self,ln_element):
        ln = {}
        # href (MANDATORY)
        href = ln_element.attrib.get("href",None)
        if (href is not None):
            ln['href'] = href
        else:
            raise ValueError("Missing href in <rs:ln> in %s" % (context))
        # rel (MANDATORY)
        rel = ln_element.attrib.get("rel",None)
        if (rel is not None):
            ln['rel'] = rel
        else:
            raise ValueError("Missing rel in <rs:ln> in %s" % (context))
        # don't attempt to parse hash values here
        hash = ln_element.attrib.get("hash",None)
        if (hash is not None):
            ln['hash'] = hash
        # modified
        modified = ln_element.attrib.get("modified",None)
        if (modified is not None):
            ln['modified'] = modified
        # content type
        type = ln_element.attrib.get("type",None)
        # length in bytes
        length = ln_element.attrib.get("length",None)
        if (length is not None):
            try:
                ln['length']=int(length)
            except ValueError as e:
                raise Exception("Invalid length element in <rs:ln> for %s" % (context))
        return(ln)

    ##### ResourceContainer (ResourceList or Changelist) methods #####

    def resources_as_xml(self, resources, num_resources=None):
        """Return XML for a set of resources in sitemap format
        
        resources is either an iterable or iterator of Resource objects.

        If num_resources is not None then only that number will be written
        before returning.
        """
        namespaces = { 'xmlns': SITEMAP_NS, 'xmlns:rs': RS_NS }
        root = Element('urlset', namespaces)
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
            e=self.resource_etree_element(r)
            root.append(e)
            if (num_resources is not None):
                num_resources-=1
                if (num_resources==0):
                    break
        # have tree, now serialize
        tree = ElementTree(root);
        xml_buf=StringIO.StringIO()
        if (sys.version_info < (2,7)):
            tree.write(xml_buf,encoding='UTF-8')
        else:
            tree.write(xml_buf,encoding='UTF-8',xml_declaration=True,method='xml')
        return(xml_buf.getvalue())

    def sitemap_parse_xml(self, fh=None, etree=None, resources=None, capability=None):
        """Parse XML Sitemap from fh or etree and add resources to a
        resorces object (which must support the add method). Returns 
        the resources object.

        Also sets self.resources_created to be the number of resources created. 
        We adopt a very lax approach here. The parsing is properly namespace 
        aware but we search just for the elements wanted and leave everything 
        else alone.

        The one exception is detection of Sitemap indexes. If the root element
        indicates a sitemapindex then an SitemapIndexError() is thrown 
        and the etree passed along with it.
        """
        if (resources is None):
            resources=ResourceContainer()
        if (fh is not None):
            etree=parse(fh)
        elif (etree is None):
            raise ValueError("Neither fh or etree set")
        # check root element: urlset (for sitemap), sitemapindex or bad
        if (etree.getroot().tag == '{'+SITEMAP_NS+"}sitemapindex"):
            raise SitemapIndexError("Got sitemapindex when expecting sitemap",etree)
        elif (etree.getroot().tag != '{'+SITEMAP_NS+"}urlset"):
            raise ValueError("XML is not sitemap or sitemapindex")
        # have what we expect, read it
        in_preamble = True
        self.resources_created=0
        for e in etree.getroot().getchildren():
            # look for <rs:md> and <rs:ln>, first <url> ends
            # then look for resources in <url> blocks
            if (e.tag == "{"+SITEMAP_NS+"}url"):
                in_preamble = False #any later rs:md or rs:ln is error
                r = self.resource_from_etree(e, self.resource_class)
                try:
                    resources.add( r )
                except SitemapDupeError:
                    self.logger.warning("dupe of: %s (lastmod=%s)" % (r.uri,r.lastmod))
                self.resources_created+=1
            elif (e.tag == "{"+RS_NS+"}md"):
                if (in_preamble):
                    resources.md = self.md_from_etree(e)
                else:
                    raise Exception("Found <rs:md> after first <url> in sitemap")
            elif (e.tag == "{"+RS_NS+"}ln"):
                if (in_preamble):
                    resources.ln.append(self.ln_from_etree(e))
                else:
                    raise Exception("Found <rs:md> after first <url> in sitemap")
            else:
                # element we don't recognize, ignore
                # FIXME - might add check for debug?
                pass
        # check that we read to right capability document
        if (capability is not None):
            if ('capability' not in resources.md):
                self.logger.warning('No capabiliy specified, assuming resourcelist')
                resources.md['capability'] = 'resourcelist'
            elif (resources.md['capability'] != capability):
                raise ValueError("Expected to read a %s document, got %s" %
                                 (capability,resources.md['capability']))
        # return the resource container object
        return(resources)

    ##### Sitemap Index #####

    def sitemapindex_as_xml(self, file=None, sitemaps={}, resource_list=None):
        """Return a sitemapindex as an XML string

        Format:
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap>
            <loc>http://www.example.com/sitemap1.xml.gz</loc>
            <lastmod>2004-10-01T18:23:17+00:00</lastmod>
          </sitemap>
          ...more...
        </sitemapeindex>
        """
        namespaces = { 'xmlns': SITEMAP_NS }
        root = Element('sitemapindex', namespaces)
        if (self.pretty_xml):
            root.text="\n"
        for file in sitemaps.keys():
            try:
                uri = self.mapper.dst_to_src(file)
            except MapperError:
                uri = 'file://'+file
                self.logger.error("sitemapindex: can't map %s into URI space, writing %s" % (file,uri))
            # Make a Resource for the Sitemap and serialize
            smr = Resource( uri=uri, timestamp=sitemaps[file] )
            root.append( self.resource_etree_element(smr, element_name='sitemap') )
        tree = ElementTree(root);
        xml_buf=StringIO.StringIO()
        if (sys.version_info < (2,7)):
            tree.write(xml_buf,encoding='UTF-8')
        else:
            tree.write(xml_buf,encoding='UTF-8',xml_declaration=True,method='xml')
        return(xml_buf.getvalue())

    def sitemapindex_parse_xml(self, fh=None, etree=None, sitemapindex=None):
        """Parse XML SitemapIndex from fh and return sitemap info

        Returns the SitemapIndex object.

        Also sets self.sitemaps_created to be the number of resources created. 
        We adopt a very lax approach here. The parsing is properly namespace 
        aware but we search just for the elements wanted and leave everything 
        else alone.

        The one exception is detection of a Sitemap when an index is expected. 
        If the root element indicates a sitemap then a SitemapIndexError() is 
        thrown and the etree passed along with it.
        """
        if (sitemapindex is None):
            sitemapindex=SitemapIndex()
        if (fh is not None):
            etree=parse(fh)
        elif (etree is None):
            raise ValueError("Neither fh or etree set")
        # check root element: urlset (for sitemap), sitemapindex or bad
        if (etree.getroot().tag == '{'+SITEMAP_NS+"}sitemapindex"):
            self.sitemaps_created=0
            for sitemap_element in etree.findall('{'+SITEMAP_NS+"}sitemap"):
                # We can parse the inside just like a <url> element indicating a resource
                sitemapindex.add( self.resource_from_etree(sitemap_element,self.resource_class) )
                self.sitemaps_created+=1
            return(sitemapindex)
        elif (etree.getroot().tag == '{'+SITEMAP_NS+"}urlset"):
            raise SitemapIndexError("Got sitemap when expecting sitemapindex",etree)
        else:
            raise ValueError("XML is not sitemap or sitemapindex")


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


    ##### Utility #####

    def is_file_uri(self, uri):
        """Return true is uri looks like a local file URI, false otherwise"""
        return(re.match('file:',uri) or re.match('/',uri))
