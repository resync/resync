"""Read and write ResourceSync documents as sitemaps."""

import io
import logging
import os
import sys
from defusedxml.ElementTree import parse
from xml.etree.ElementTree import ElementTree, Element, tostring

from .resource import Resource
from .resource_container import ResourceContainer

SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
RS_NS = 'http://www.openarchives.org/rs/terms/'
# Mapping of Resource object atts to XML atts, see Sitemap._xml_att_name()
XML_ATT_NAME = {
    'mime_type': 'type',
    'md_at': 'at',
    'md_completed': 'completed',
    'md_from': 'from',
    'md_until': 'until'
}


class SitemapIndexError(Exception):
    """Exception if sitemapindex read instead of sitemap or vice-versa.

    Provides both a message and a place to store the etree so that
    the parse tree may be reused as a sitemapindex.
    """

    def __init__(self, message=None, etree=None):
        """Initialize SitemapIndexError with supplied parameters."""
        self.message = message
        self.etree = etree

    def __str__(self):
        """Return just the message attribute."""
        return(self.message)


class SitemapParseError(Exception):
    """Exception for sitemap parsing structural error."""

    pass


class SitemapDupeError(Exception):
    """Exception for case of duplicate resources in sitemap."""

    pass


class Sitemap(object):
    """Read and write sitemaps.

    Implemented as a separate class that uses ResourceContainer
    (ResourceList or ChangeList) and Resource classes as data objects.
    Reads and write sitemaps, including multiple file sitemaps.

    This class does not automatically handle the reading or writing
    of a sitemapindex and multiple sitemap documents. Instead it will
    take a default and throw and exception if the other case is found
    so that the calling code can handle it.

    Default is to follow ResourceSync v1.1 which distinguishes the meanings
    of the <lastmod> element (resource modified time as used for Last-Modified
    header) and the newly introduced <rs:md datetime="..."> attribute (the
    change time in ChangeList and similar resources). There are two parameters
    to control these behaviors:

        spec_version - set to either '1.0' or '1.1'. If set to '1.0' then no
            datetime attribute will be written or parsed
        add_lastmod - set True to add a lastmod with the same value of datetime
            if no specific lastmod is specified. Applies only when spec_version
            '1.1' is selected, provide compatibility with systems that do not
            understand datetime but instead rely on lastmod
    """

    def __init__(self, pretty_xml=False, spec_version='1.1', add_lastmod=False):
        """Initialize Sitemap object."""
        self.logger = logging.getLogger('resync.sitemap')
        self.pretty_xml = pretty_xml
        self.spec_1_0 = (spec_version == '1.0')  # v1.0 else assume v1.1
        self.add_lastmod = add_lastmod  # Optional in v1.1
        # Classes used when parsing
        self.resource_class = Resource
        # Information recorded for logging
        self.resources_created = 0    # Set during parsing sitemap
        self.parsed_index = None      # Set True for sitemapindex, False for sitemap
        # rs:md attributes
        self.md_att_keys = ['md_at', 'capability', 'change', 'datetime',
                            'md_completed', 'md_from', 'hash', 'length',
                            'path', 'mime_type', 'md_until']
        # capabilities
        self.capabilities = ['resourcelist', 'changelist', 'resourcedump',
                             'changedump', 'resourcedump-manifest',
                             'changedump-manifest', 'capabilitylist',
                             'description',
                             'resourcelist-archive', 'resourcedump-archive',
                             'changelist-archive', 'changedump-archive']
        if self.spec_1_0:
            self.md_att_keys.remove('datetime')

    # Write the XML for a sitemap or sitemapindex

    def resources_as_xml(self, resources, sitemapindex=False, fh=None):
        """Write or return XML for a set of resources in sitemap format.

        Arguments:
        - resources - either an iterable or iterator of Resource objects;
                      if there an md attribute this will go to <rs:md>
                      if there an ln attribute this will go to <rs:ln>
        - sitemapindex - set True to write sitemapindex instead of sitemap
        - fh - write to filehandle fh instead of returning string
        """
        # element names depending on sitemapindex or not
        root_element = ('sitemapindex' if (sitemapindex) else 'urlset')
        item_element = ('sitemap' if (sitemapindex) else 'url')
        # namespaces and other settings
        namespaces = {'xmlns': SITEMAP_NS, 'xmlns:rs': RS_NS}
        root = Element(root_element, namespaces)
        if (self.pretty_xml):
            root.text = "\n"
        # <rs:ln>
        if (hasattr(resources, 'ln')):
            for ln in resources.ln:
                self.add_element_with_atts_to_etree(root, 'rs:ln', ln)
        # <rs:md>
        if (hasattr(resources, 'md')):
            self.add_element_with_atts_to_etree(root, 'rs:md', resources.md)
        # <url> entries from either an iterable or an iterator
        for r in resources:
            e = self.resource_etree_element(r, element_name=item_element)
            root.append(e)
        # have tree, now serialize
        tree = ElementTree(root)
        xml_buf = None
        if (fh is None):
            xml_buf = io.StringIO()
            fh = xml_buf
        tree.write(
            fh,
            encoding='unicode',
            xml_declaration=True,
            method='xml')
        if (xml_buf is not None):
            return(xml_buf.getvalue())

    # Read/parse an XML sitemap or sitemapindex

    def parse_xml(self, fh=None, etree=None, resources=None,
                  capability=None, sitemapindex=None):
        """Parse XML Sitemap and add to resources object.

        Reads from fh or etree and adds resources to a resorces object
        (which must support the add method). Returns the resources object.

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
            resources = ResourceContainer()
        if (fh is not None):
            etree = parse(fh)
        elif (etree is None):
            raise ValueError("Neither fh or etree set")
        # check root element: urlset (for sitemap), sitemapindex or bad
        root_tag = etree.getroot().tag
        resource_tag = None  # will be <url> or <sitemap> depending on type
        self.parsed_index = None
        if (root_tag == '{' + SITEMAP_NS + "}urlset"):
            self.parsed_index = False
            if (sitemapindex is not None and sitemapindex):
                raise SitemapIndexError(
                    "Got sitemap when expecting sitemapindex", etree)
            resource_tag = '{' + SITEMAP_NS + "}url"
        elif (root_tag == '{' + SITEMAP_NS + "}sitemapindex"):
            self.parsed_index = True
            if (sitemapindex is not None and not sitemapindex):
                raise SitemapIndexError(
                    "Got sitemapindex when expecting sitemap", etree)
            resource_tag = '{' + SITEMAP_NS + "}sitemap"
        else:
            raise SitemapParseError(
                "XML is not sitemap or sitemapindex (root element is <%s>)" %
                root_tag)

        # have what we expect, read it
        in_preamble = True
        self.resources_created = 0
        seen_top_level_md = False
        for e in list(etree.getroot()):
            # look for <rs:md> and <rs:ln>, first <url>/<sitemap> ends
            # then look for resources in <url>/<sitemap> blocks.
            # ignore any elements we don't recognize
            if (e.tag == resource_tag):
                in_preamble = False  # any later rs:md or rs:ln is error
                r = self.resource_from_etree(e, self.resource_class)
                resources.add(r)
                self.resources_created += 1
            elif (e.tag == "{" + RS_NS + "}md"):
                if (in_preamble):
                    if (seen_top_level_md):
                        raise SitemapParseError(
                            "Multiple <rs:md> at top level of sitemap")
                    else:
                        resources.md = self.md_from_etree(e, 'preamble')
                        seen_top_level_md = True
                else:
                    raise SitemapParseError(
                        "Found <rs:md> after first <url> in sitemap")
            elif (e.tag == "{" + RS_NS + "}ln"):
                if (in_preamble):
                    resources.ln.append(self.ln_from_etree(e, 'preamble'))
                else:
                    raise SitemapParseError(
                        "Found <rs:ln> after first <url> in sitemap")
        # check that we read to right capability document
        if (capability is not None):
            if ('capability' not in resources.md):
                if (capability == 'resourcelist'):
                    self.logger.warning(
                        'No capability specified in sitemap, assuming resourcelist')
                    resources.md['capability'] = 'resourcelist'
                else:
                    raise SitemapParseError("Expected to read a %s document, but no capability specified in sitemap" %
                                            (capability))
            if (resources.md['capability'] != capability):
                raise SitemapParseError("Expected to read a %s document, got %s" %
                                        (capability, resources.md['capability']))
        # return the resource container object
        return(resources)

    # Resource methods

    def resource_etree_element(self, resource, element_name='url'):
        """Return xml.etree.ElementTree.Element representing the resource.

        Returns and element for the specified resource, of the form <url>
        with enclosed properties that are based on the sitemap with extensions
        for ResourceSync.
        """
        e = Element(element_name)
        sub = Element('loc')
        sub.text = resource.uri
        e.append(sub)
        lm = resource.lastmod  # W3C Datetime in UTC
        if lm is not None or self.spec_1_0 or self.add_lastmod:
            # In 1.0 we either use the lastmod specified or else use the
            # datetime value because there should always be a lastmod
            if lm is None and (self.spec_1_0 or self.add_lastmod):
                lm = resource.datetime  # W3C Datetime in UTC
            if lm is not None:
                sub = Element('lastmod')
                sub.text = lm
                e.append(sub)
        md_atts = {}
        for att in self.md_att_keys:
            val = getattr(resource, att, None)
            if (val is not None):
                md_atts[att] = str(val)
        if (len(md_atts) > 0):
            self.add_element_with_atts_to_etree(e, 'rs:md', md_atts, add_return=False)
        # add any <rs:ln>
        if (hasattr(resource, 'ln') and resource.ln is not None):
            for ln in resource.ln:
                self.add_element_with_atts_to_etree(e, 'rs:ln', ln)
        if (self.pretty_xml):
            e.tail = "\n"
        return(e)

    def resource_as_xml(self, resource):
        """Return string for the resource as part of an XML sitemap.

        Returns a string with the XML snippet representing the resource,
        without any XML declaration. (So much simpler now only Python 3.x
        supported, see earlier versions for 2.6, 2.7 etc.)
        """
        e = self.resource_etree_element(resource)
        return(tostring(e, encoding='unicode', method='xml'))

    def resource_from_etree(self, etree, resource_class):
        """Construct a Resource from an etree.

        Parameters:
         etree - the etree to parse
         resource_class - class of Resource object to create

        The parsing is properly namespace aware but we search just
        for the elements wanted and leave everything else alone. Will
        raise an error if there are multiple <loc> or multiple <lastmod>
        elements. Otherwise, provided there is a <loc> element then will
        go ahead and extract as much as possible.

        All errors raised are SitemapParseError with messages intended
        to help debug problematic sitemap XML.
        """
        loc_elements = etree.findall('{' + SITEMAP_NS + "}loc")
        if (len(loc_elements) > 1):
            raise SitemapParseError(
                "Multiple <loc> elements while parsing <url> in sitemap")
        elif (len(loc_elements) == 0):
            raise SitemapParseError(
                "Missing <loc> element while parsing <url> in sitemap")
        else:
            loc = loc_elements[0].text
        if (loc is None or loc == ''):
            raise SitemapParseError(
                "Bad <loc> element with no content while parsing <url> in sitemap")
        # must at least have a URI, make this object
        resource = resource_class(uri=loc)
        # and hopefully a lastmod datetime (but none is OK)
        lastmod_elements = etree.findall('{' + SITEMAP_NS + "}lastmod")
        if (len(lastmod_elements) > 1):
            raise SitemapParseError(
                "Multiple <lastmod> elements while parsing <url> in sitemap")
        elif (len(lastmod_elements) == 1):
            resource.lastmod = lastmod_elements[0].text
        # proceed to look for other resource attributes in an rs:md element
        md_elements = etree.findall('{' + RS_NS + "}md")
        if (len(md_elements) > 1):
            raise SitemapParseError(
                "Found multiple (%d) <rs:md> elements for %s", (len(md_elements), loc))
        elif (len(md_elements) == 1):
            # have on element, look at attributes
            md = self.md_from_etree(md_elements[0], context=loc)
            # simple attributes that map directly to Resource object attributes
            for att in ('capability', 'change', 'datetime', 'length', 'path', 'mime_type'):
                if (att in md):
                    setattr(resource, att, md[att])
            # The ResourceSync beta spec lists md5, sha-1 and sha-256 fixity
            # digest types. Parse and warn of errors ignored.
            if ('hash' in md):
                try:
                    resource.hash = md['hash']
                except ValueError as e:
                    self.logger.warning("%s in <rs:md> for %s" % (str(e), loc))
        # look for rs:ln elements (optional)
        ln_elements = etree.findall('{' + RS_NS + "}ln")
        if (len(ln_elements) > 0):
            resource.ln = []
            for ln_element in ln_elements:
                resource.ln.append(self.ln_from_etree(ln_element, loc))
        return(resource)

    def md_from_etree(self, md_element, context=''):
        """Parse rs:md attributes returning a dict of the data.

        Parameters:
            md_element  - etree element <rs:md>
            context     - context for error reporting

        ResourceSync v1.1 adds the datetime attribute
        """
        md = {}
        # grab all understood attributes into md dict
        for att in self.md_att_keys:
            xml_att = self._xml_att_name(att)
            val = md_element.attrib.get(xml_att, None)
            if (val is not None):
                md[att] = val
        # capability. Allow this to be missing or a new value but warn if it
        # isn't recognized
        if ('capability' in md and md['capability'] not in self.capabilities):
            self.logger.warning("Unknown capability name '%s' in %s" % (md['capability'], context))
        # change must be one of defined values
        if ('change' in md and md['change'] not in ['created', 'updated', 'deleted']):
            raise SitemapParseError("Bad change attribute in <rs:md> for %s" % (context))
        # length must be an integer
        if ('length' in md):
            try:
                md['length'] = int(md['length'])
            except ValueError as e:
                raise SitemapParseError("Invalid length element in <rs:md> for %s" %
                                        (context))
        return(md)

    def ln_from_etree(self, ln_element, context=''):
        """Parse rs:ln element from an etree, returning a dict of the data.

        Parameters:
            md_element - etree element <rs:md>
            context    - context string for error reporting
        """
        ln = {}
        # grab all understood attributes into ln dict
        for att in ('hash', 'href', 'length', 'modified',
                    'path', 'rel', 'pri', 'mime_type'):
            xml_att = self._xml_att_name(att)
            val = ln_element.attrib.get(xml_att, None)
            if (val is not None):
                ln[att] = val
        # now do some checks and conversions...
        # href (MANDATORY)
        if ('href' not in ln):
            raise SitemapParseError("Missing href in <rs:ln> in %s" %
                                    (context))
        # rel (MANDATORY)
        if ('rel' not in ln):
            raise SitemapParseError("Missing rel in <rs:ln> in %s" % (context))
        # length in bytes
        if ('length' in ln):
            try:
                ln['length'] = int(ln['length'])
            except ValueError as e:
                raise SitemapParseError("Invalid length attribute value in <rs:ln> for %s" %
                                        (context))
        # pri - priority, must be a number between 1 and 999999
        if ('pri' in ln):
            try:
                ln['pri'] = int(ln['pri'])
            except ValueError as e:
                raise SitemapParseError(
                    "Invalid pri attribute in <rs:ln> for %s" %
                    (context))
            if (ln['pri'] < 1 or ln['pri'] > 999999):
                raise SitemapParseError(
                    "Bad pri attribute value in <rs:ln> for %s" %
                    (context))
        return(ln)

    # Metadata and link elements

    def add_element_with_atts_to_etree(self, etree, name, atts, add_return=True):
        """Add empty element with name and atts to etree iff there are any atts.

        Parameters:
            etree - an etree object
            name  - XML element name
            atts  - dicts of attribute values. Attribute names are transformed
        """
        xml_atts = {}
        for att in atts.keys():
            val = atts[att]
            if (val is not None):
                xml_atts[self._xml_att_name(att)] = str(val)
        if (len(xml_atts) > 0):
            e = Element(name, xml_atts)
            if (add_return and self.pretty_xml):
                e.tail = "\n"
            # There is no real reason why the attribute keys should be sorted
            # but ElementTree serialization up to Python 3.7 always wrote XML
            # with attributes in sort order. This was changed in Python 3.8
            # to be the order of addition. Adding sorting here keeps consistent
            # behavior for all versions. See:
            # https://docs.python.org/3/library/xml.etree.elementtree.html#element-objects
            attribs = sorted(e.attrib.items())
            e.attrib.clear()
            e.attrib.update(attribs)
            etree.append(e)

    def _xml_att_name(self, att):
        """Get XML attribute name corresponding to supplied Resource object attribute.

        We cannot use the XML attribute names in Python because 'from' and others
        conflict with Python reserved words. To be consistent all the extra timestamps
        are prefixed with md_. Assumption is that attibute name is same unless
        specified in XML_ATT_NAME.
        """
        return XML_ATT_NAME.get(att, att)
