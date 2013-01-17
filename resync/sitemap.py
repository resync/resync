"""Read and write ResourceSync inventories and changelist as sitemaps"""

import re
import os
import sys
import logging
from urllib import URLopener
from xml.etree.ElementTree import ElementTree, Element, parse, tostring
from datetime import datetime
import StringIO

from resource import Resource
from inventory import Inventory, InventoryDupeError
from changelist import ChangeList
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

class SitemapIndex(Inventory):
    """Reuse an inventory to hold the set of sitemaps"""
    pass

class SitemapError(Exception):
    pass

class Sitemap(object):
    """Read and write sitemaps

    Implemented as a separate class that uses ResourceContainer (Inventory or
    ChangeList) and Resource classes as data objects. Reads and write sitemaps, 
    including multiple file sitemaps.
    """

    def __init__(self, pretty_xml=False, allow_multifile=True, mapper=None):
        self.logger = logging.getLogger('sitemap')
        self.pretty_xml=pretty_xml
        self.allow_multifile=allow_multifile
        self.mapper=mapper
        self.max_sitemap_entries=50000
        # Classes used when parsing
        self.inventory_class=Inventory
        self.resource_class=Resource
        self.changelist_class=ChangeList
        self.resourcechange_class=Resource
        # Information recorded for logging
        self.resources_created=None # Set during parsing sitemap
        self.sitemaps_created=None  # Set during parsing sitemapindex
        self.content_length=None    # Size of last sitemap read
        self.bytes_read=0           # Aggregate of content_length values
        self.changelist_read=None   # Set true if changelist read
        self.read_type=None         # Either sitemap/sitemapindex/changelist/changelistindex

    ##### General sitemap methods that also handle sitemapindexes #####

    def write(self, resources=None, basename='/tmp/sitemap.xml', changelist=False):
        """Write one or a set of sitemap files to disk

        resources is a ResourceContainer that may be an Inventory or
        a ChangeList. This may be a generator so data is read as needed
        and length is determined at the end.

        basename is used as the name of the single sitemap file or the 
        sitemapindex for a set of sitemap files.

        if changelist is set true then type information is added to indicate
        that this sitemap file is a changelist and not an inventory.

        Uses self.max_sitemap_entries to determine whether the inventory can 
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
                f.write(self.resources_as_xml(chunk,changelist=changelist))
                f.close()
                # Record timestamp
                sitemaps[file] = os.stat(file).st_mtime
                # Get next chunk
                ( chunk, next ) = self.get_resources_chunk(resources_iter,next)
            self.logger.info("Wrote %d sitemaps" % (len(sitemaps)))
            f = open(basename, 'w')
            self.logger.info("Writing sitemapindex %s..." % (basename))
            f.write(self.sitemapindex_as_xml(sitemaps=sitemaps,inventory=resources,capabilities=resources.capabilities,changelist=changelist))
            f.close()
            self.logger.info("Wrote sitemapindex %s" % (basename))
        else:
            f = open(basename, 'w')
            self.logger.info("Writing sitemap %s..." % (basename))
            f.write(self.resources_as_xml(chunk,capabilities=resources.capabilities,changelist=changelist))
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

    def read(self, uri=None, resources=None, changelist=None, index_only=False):
        """Read sitemap from a URI including handling sitemapindexes

        Returns the inventory or changelist. If changelist is not specified (None)
        then it is assumed that an Inventory is to be read, unless the XML
        indicates a Changelist.

        If changelist is True then a Changelist if expected; if changelist if False
        then an Inventory is expected.

        If index_only is True then individual sitemaps references in a sitemapindex
        will not be read. This will result in no resources being returned and is
        useful only to read the capabilities and metadata listed in the sitemapindex.

        Will set self.read_type to a string value sitemap/sitemapindex/changelist/changelistindex
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
        # assume inventory but look to see whether this is a changelist 
        # as indicated with rs:type="changelist" on the root
        resources_class = self.inventory_class
        sitemap_xml_parser = self.inventory_parse_xml
        self.changelist_read = False
        self.read_type = 'sitemap'
        root_type = root.attrib.get('{'+RS_NS+'}type',None)
        if (root_type is not None):
            if (root_type == 'changelist'):
                self.changelist_read = True
            else:
                self.logger.info("Bad value of rs:type on root element (%s), ignoring" % (root_type))
        elif (changelist is True):
            self.changelist_read = True
        if (self.changelist_read):
            self.read_type = 'changelist'
            resources_class = self.changelist_class
            sitemap_xml_parser = self.changelist_parse_xml
        # now have make sure we have a place to put the data we read
        if (resources is None):
            resources=resources_class()
        # sitemap or sitemapindex?
        if (root.tag == '{'+SITEMAP_NS+"}urlset"):
            self.logger.info( "Parsing as sitemap" )
            sitemap_xml_parser(etree=etree, resources=resources)
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
            self.logger.info( "Now reading %d sitemaps" % len(sitemaps) )
            for sitemap_uri in sorted(sitemaps.resources.keys()):
                if (sitemapindex_is_file):
                    if (not self.is_file_uri(sitemap_uri)):
                        # Attempt to map URI to local file
                        remote_uri = sitemap_uri
                        sitemap_uri = self.mapper.src_to_dst(remote_uri)
                else:
                    # The individual sitemaps should be at a URL (scheme/server/path)
                    # that the sitemapindex URL can speak authoritatively about
                    if (not UrlAuthority(uri).has_authority_over(sitemap_uri)):
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
                sitemap_xml_parser( fh=fh, resources=resources )
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
            lastmod_name = 'lastmod'
            lastmod_attrib = {}
            if (hasattr(resource,'changetype') and 
                resource.changetype is not None):
                # Not a plain old <lastmod>, use <lastmod> with 
                # rs:type attribute or <expires>
                if (resource.changetype == 'created'):
                    lastmod_attrib = {'rs:type': 'created'}
                elif (resource.changetype == 'updated'):
                    lastmod_attrib = {'rs:type': 'updated'}
                elif (resource.changetype == 'deleted'):
                    lastmod_name = 'expires'
                else:
                    raise Exception("Unknown change type '%s' for resource %s" % (resource.changetype,resource.uri))
            # Create appriate element for timestamp
            sub = Element(lastmod_name,lastmod_attrib)
            sub.text = str(resource.lastmod) #W3C Datetime in UTC
            e.append(sub)
        if (resource.size is not None):
            sub = Element('rs:size')
            sub.text = str(resource.size)
            e.append(sub)
        if (resource.md5 is not None):
            sub = Element('rs:fixity')
            sub.attrib = {'type':'md5'}
            sub.text = str(resource.md5)
            e.append(sub)
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
        print "looking for rs;md..."
        print tostring(etree)
        md_elements = etree.findall('{'+RS_NS+"}md")
        if (len(md_elements)>1):
            raise SitemapError("Found multiple (%d) <rs:md> elements for %s", (len(md_elements),loc))
        elif (len(md_elements)==1):
            # have on element, look at attributes
            md_element = md_elements[0]
            print "found rs;md..."
            # change type
            change = md_element.attrib.get("change",None)
            if (change is not None):
                if (change in ['created','updated','deleted'] ):
                    resource.changetype = change
                else:
                    self.logger.warning("Bad change attribute in <rs:md> for %s" % (loc))
            type = md_element.attrib.get("type",None)
            # size in bytes
            size = md_element.attrib.get("size",None)
            if (size is not None):
                try:
                    resource.size=int(size)
                except ValueError as e:
                    raise Exception("Invalid size element in <rs:md> for %s" % (loc))
            # The ResourceSync beta spec lists md5, sha-1 and sha-256 fixity
            # digest types. Currently support only md5, warn if anything else
            # ignored
            hash = md_element.attrib.get("hash",None)
            if (hash is not None):
                #space separated set
                hash_seen = set()
                for entry in hash.split(' '):
                    ( type, value ) = entry.split(':',1)
                    if (type in hash_seen):
                        self.logger.warning("Ignored duplicate hash type %s in <rs:md> for %s" % (type,loc))
                    if (type in ('md5','sha-1','sha-256')):
                        hash_seen.add(type)
                        if (type == 'md5'):
                            resource.md5=value #FIXME - should check valid
                        elif (type == 'sha-1' or type == 'sha-256'):
                            self.logger.warning("Unsupported type (%s) in <rs:fixity for %s" % (type,loc))
                    else:
                        self.logger.warning("Ignored bad hash type in <rs:md> for %s" % (loc))
        # look for rs:ln elements (optional)
        ln_elements = etree.findall('{'+SITEMAP_NS+"}ln")
        if (len(ln_elements)>0):
            self.logger.warning("Ignored <rs:ln> element(s) for %s, FIXME" % (loc))
        return(resource)

    ##### ResourceContainer (Inventory or Changelist) methods #####

    def resources_as_xml(self, resources, num_resources=None, capabilities=None, changelist=False):
        """Return XML for a set of resources in sitemap format
        
        resources is either an iterable or iterator of Resource objects.

        If num_resources is not None then only that number will be written
        before exiting.
        """
        # will include capabilities if allowed and if there are some
        namespaces = { 'xmlns': SITEMAP_NS, 'xmlns:rs': RS_NS }
        if ( capabilities is not None and len(capabilities)>0 ):
            namespaces['xmlns:xhtml'] = RS_NS
        root = Element('urlset', namespaces)
        if (changelist):
            root.set('rs:type','changelist')
        if (self.pretty_xml):
            root.text="\n"
        if ( capabilities is not None and len(capabilities)>0 ):
            self.add_capabilities_to_etree(root,capabilities)
        # now add the entries from either an iterable or an iterator
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

    def inventory_parse_xml(self, fh=None, etree=None, resources=None):
        """Parse XML Sitemap from fh or etree and add resources to an Inventory object

        Returns the inventory.

        Also sets self.resources_created to be the number of resources created. 
        We adopt a very lax approach here. The parsing is properly namespace 
        aware but we search just for the elements wanted and leave everything 
        else alone.

        The one exception is detection of Sitemap indexes. If the root element
        indicates a sitemapindex then an SitemapIndexError() is thrown 
        and the etree passed along with it.
        """
        inventory = resources #use inventory locally but want common argument name
        if (inventory is None):
            inventory=self.inventory_class()
        if (fh is not None):
            etree=parse(fh)
        elif (etree is None):
            raise ValueError("Neither fh or etree set")
        # check root element: urlset (for sitemap), sitemapindex or bad
        if (etree.getroot().tag == '{'+SITEMAP_NS+"}urlset"):
            self.resources_created=0
            for url_element in etree.findall('{'+SITEMAP_NS+"}url"):
                r = self.resource_from_etree(url_element, self.resource_class)
                try:
                    inventory.add( r )
                except InventoryDupeError:
                    self.logger.warning("dupe: %s (%s =? %s)" % 
                        (r.uri,r.lastmod,inventory.resources[r.uri].lastmod))
                self.resources_created+=1
            inventory.capabilities = self.capabilities_from_etree(etree)
            return(inventory)
        elif (etree.getroot().tag == '{'+SITEMAP_NS+"}sitemapindex"):
            raise SitemapIndexError("Got sitemapindex when expecting sitemap",etree)
        else:
            raise ValueError("XML is not sitemap or sitemapindex")

    def changelist_parse_xml(self, fh=None, etree=None, resources=None):
        """Parse XML Sitemap from fh or etree and add resources to an Changelist object

        Returns the Changelist.

        Also sets self.resources_created to be the number of resources created. 
        We adopt a very lax approach here. The parsing is properly namespace 
        aware but we search just for the elements wanted and leave everything 
        else alone.

        The one exception is detection of Sitemap indexes. If the root element
        indicates a sitemapindex then an SitemapIndexError() is thrown 
        and the etree passed along with it.
        """
        changelist = resources #use inventory locally but want common argument name
        if (changelist is None):
            changelist=self.changelist_class()
        if (fh is not None):
            etree=parse(fh)
        elif (etree is None):
            raise ValueError("Neither fh or etree set")
        # check root element: urlset (for sitemap), sitemapindex or bad
        if (etree.getroot().tag == '{'+SITEMAP_NS+"}urlset"):
            self.resources_created=0
            for url_element in etree.findall('{'+SITEMAP_NS+"}url"):
                r = self.resource_from_etree(url_element, self.resourcechange_class)
                changelist.add( r )
                self.resources_created+=1
            changelist.capabilities = self.capabilities_from_etree(etree)
            return(changelist)
        elif (etree.getroot().tag == '{'+SITEMAP_NS+"}sitemapindex"):
            raise SitemapIndexError("Got sitemapindex when expecting sitemap",etree)
        else:
            raise ValueError("XML is not sitemap or sitemapindex")

    ##### Sitemap Index #####

    def sitemapindex_as_xml(self, file=None, sitemaps={}, inventory=None, capabilities=None, changelist=False ):
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
        include_capabilities = capabilities and (len(capabilities)>0)
        namespaces = { 'xmlns': SITEMAP_NS }
        if (include_capabilities):
            namespaces['xmlns:xhtml'] = RS_NS
        root = Element('sitemapindex', namespaces)
        if (changelist):
            root.set('rs:type','changelist')
        if (self.pretty_xml):
            root.text="\n"
        if (include_capabilities):
            self.add_capabilities_to_etree(root,capabilities)
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
            sitemapindex.capabilities = self.capabilities_from_etree(etree)
        elif (etree.getroot().tag == '{'+SITEMAP_NS+"}urlset"):
            raise SitemapIndexError("Got sitemap when expecting sitemapindex",etree)
        else:
            raise ValueError("XML is not sitemap or sitemapindex")


    ##### Capabilities #####

    def add_capabilities_to_etree(self, etree, capabilities):
        """ Add capabilities to the etree supplied

        Each capability is written out as on xhtml:link element where the
        attributes are represented as a dictionary.
        """
        for c in sorted(capabilities.keys()):
            # make attributes by space concatenating any capability dict values 
            # that are arrays
            atts = { 'href': c }
            for a in capabilities[c]:
                value=capabilities[c][a]
                if (a == 'attributes'):
                    a='rel'
                if (isinstance(value, str)):
                    atts[a]=value
                else:
                    atts[a]=' '.join(value)
            e = Element('xhtml:link', atts)
            if (self.pretty_xml):
                e.tail="\n"
            etree.append(e)

    def capabilities_from_etree(self, etree):
        """Read capabilities from sitemap or sitemapindex etree
        """
        capabilities = {}
        for link in etree.findall('{'+RS_NS+"}link"):
            c = link.get('href')
            if (c is None):
                raise Exception("xhtml:link without href")
            capabilities[c]={}
            rel = link.get('rel')
            #if (rel is None):
            #    raise Exception('xhtml:link href="%s" without rel attribute' % (c))
            if (rel is not None):
                attributes = []
                for r in rel.split(' '):
                    attributes.append(r)
                if (len(attributes)==1):
                    attributes = attributes[0]
                capabilities[c]['attributes']=attributes
            type = link.get('type') #fudge, take either
            #if (type is None):
            #    raise Exception('xhtml:link href="%s" without type attribute' % (c))
            if (type is not None):
                types = []
                for t in type.split(' '):
                    types.append(t)
                if (len(types)==1):
                    types = types[0]
                capabilities[c]['type']=types
        #    print capabilities[c]
        #for meta in etree.findall('{'+RS_NS+"}meta"):
        #    print meta
        return(capabilities)

    ##### Utility #####

    def is_file_uri(self, uri):
        """Return true is uri looks like a local file URI, false otherwise"""
        return(re.match('file:',uri) or re.match('/',uri))
