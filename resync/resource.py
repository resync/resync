"""Information about a web resource

Each web resource is identified by a URI and may optionally 
have other metadata such as timestamp, length, md5, etc..

The lastmod property provides ISO8601 format string access 
to the timestamp. The timestamp is stored internally as a 
unix timestamp value in UTC. This limits the range of 
possible lastmod values but covers all web-era values for
a good way into the future.

This object is optimized for size in the case whether there 
is not large a large amount of data in the attributes. This 
is done using __slots__ for the core attributes so that there
is no __dict__ defined for a Resource object. Core attributes
are:

    uri - Resource URI
    timestamp - Last-Modification time, has lastmod accessor
    length - size in bytes
    mime_type - MIME type 
    md5, sha1, sha256 - digests, have hash accessor
    change - change type
    path - path in dump

If non-core attributes are needed then the '_extra' attribute 
has a dict of values. The ones explicitly used here are:

    capability - Capability name
    ts_at - at time, has md_at accessor 
    ts_completed - completed time, has md_completed accessor 
    ts_from - from time, has md_from accessor 
    ts_until - until time, has md_until accessor 

The accessor names mime_type, md_from etc. are used to avoid conflict 
with Python built-in functions and keywords type(), from etc..

The 'ln' attribute is used when it is necessary to add links 
or other information to the object. Use of non-core attributes 
or links results in dicts being created which is convenient 
but will significantly increase the size of each Resource 
object that contains such information.
"""

import re

try: #python3
    from urllib.parse import urlparse
except: #python2
    from urlparse import urlparse
from posixpath import basename
from .w3c_datetime import str_to_datetime, datetime_to_str


class ChangeTypeError(Exception):
    """Exception class raised by Resource for bad change attribute

    The change attribute of a Resource object may be either None
    or one of the values in Resource.CHANGE_TYPES. Checking is
    disabled by setting Resource.CHANGE_TYPES False.
    """
    
    def __init__(self, val):
        self.supplied = val

    def __repr__(self):
        return "<ChangeTypeError: got %s, expected one of %s>" % \
               (self.supplied,str(Resource.CHANGE_TYPES))

    def __str__(self):
        return repr(self)


class Resource(object):
    __slots__=('uri', 'timestamp', 'length', 'mime_type', 
               'md5', 'sha1', 'sha256', 'change', 'path',
               '_extra', 'ln' )

    CHANGE_TYPES = ['created', 'updated', 'deleted']
    
    def __init__(self, uri = None, timestamp = None, length = None, 
                 md5 = None, sha1 = None, sha256 = None, mime_type = None,
                 change = None, path = None, lastmod = None, 
                 capability = None,
                 ts_at = None, md_at = None,
                 ts_completed = None, md_completed = None,
                 ts_from = None, md_from = None,
                 ts_until = None, md_until = None,
                 resource = None, ln = None):
        """Initialize object either from parameters specified or
        from an existing Resource object. If explicit parameters
        are specified then they will override values copied from
        a resource object supplied.
        """
        # Initialize core attributes
        self.uri = None
        self.timestamp = None
        self.length = None
        self.mime_type = None
        self.md5 = None
        self.sha1 = None
        self.sha256 = None
        self.change = None
        self.path = None
        self._extra = None
        self.ln = None
        # Create from a Resource-like object? Copy any relevant attributes
        if (resource is not None):
            for att in ['uri','timestamp','length','md5','sha1','sha256',
                        'change','path', 'capability',
                        'ts_at','md_at', 'ts_completed', 'md_completed',
                        'ts_from','md_from','ts_until','md_until','ln']:
                if hasattr(resource,att):
                    setattr(self, att, getattr(resource, att))
        # Any arguments will then override
        if (uri is not None):
            self.uri = uri
        if (timestamp is not None):
            self.timestamp = timestamp
        if (length is not None):
            self.length = length
        if (md5 is not None):
            self.md5 = md5
        if (sha1 is not None):
            self.sha1 = sha1
        if (sha256 is not None):
            self.sha256 = sha256
        if (mime_type is not None):
            self.mime_type = mime_type
        if (change is not None):
            self.change = change
        if (path is not None):
            self.path = path
        if (ts_at is not None):
            self.ts_at = ts_at
        if (ts_completed is not None):
            self.ts_completed = ts_completed
        if (ts_from is not None):
            self.ts_from = ts_from
        if (ts_until is not None):
            self.ts_until = ts_until
        if (capability is not None):
            self.capability = capability
        if (ln is not None):
            self.ln = ln
        # Timestamp setters
        if (lastmod is not None):
            self.lastmod=lastmod
        if (md_at is not None):
            self.md_at=md_at
        if (md_completed is not None):
            self.md_completed=md_completed
        if (md_from is not None):
            self.md_from=md_from
        if (md_until is not None):
            self.md_until=md_until
        # Sanity check
        if (self.uri is None):
            raise ValueError("Cannot create resource without a URI")

    def __setattr__(self, prop, value):
        # Add validity check for self.change
        if (prop == 'change' and Resource.CHANGE_TYPES and
            value is not None and not value in Resource.CHANGE_TYPES):
            raise ChangeTypeError(value)
        else:
            try:
                object.__setattr__(self, prop, value)
            except AttributeError:
                # assume an extra one...
                self._set_extra(prop, value)

    def _set_extra(self, prop, value):
        # Use self._extra dict to hold non-core attributes to 
        # save space
        if (self._extra is None):
            self._extra = dict()
        self._extra[prop] = value
    
    def _get_extra(self, prop):
        # Returns None for a property not set
        if (self._extra is None):
            return None
        return self._extra.get(prop)

    @property
    def lastmod(self):
        """The Last-Modified data in W3C Datetime syntax, Z notation"""
        return datetime_to_str(self.timestamp)

    @lastmod.setter
    def lastmod(self, lastmod):
        """Set timestamp from a W3C Datetime Last-Modified value"""
        self.timestamp = str_to_datetime(lastmod, context='lastmod')

    @property
    def md_at(self):
        """md_at values in W3C Datetime syntax, Z notation"""
        return datetime_to_str(self._get_extra('ts_at'))

    @md_at.setter
    def md_at(self, md_at):
        """Set at value from a W3C Datetime value"""
        self._set_extra( 'ts_at', str_to_datetime(md_at, context='md_at datetime') )

    @property
    def md_completed(self):
        """md_completed value in W3C Datetime syntax, Z notation"""
        return datetime_to_str(self._get_extra('ts_completed'))

    @md_completed.setter
    def md_completed(self, md_completed):
        """Set md_completed value from a W3C Datetime value"""
        self._set_extra( 'ts_completed', str_to_datetime(md_completed, context='md_completed datetime') )

    @property
    def md_from(self):
        """md_from value in W3C Datetime syntax, Z notation"""
        return datetime_to_str(self._get_extra('ts_from'))

    @md_from.setter
    def md_from(self, md_from):
        """Set md_from value from a W3C Datetime value"""
        self._set_extra( 'ts_from', str_to_datetime(md_from, context='md_from datetime') )

    @property
    def md_until(self):
        """md_until value in W3C Datetime syntax, Z notation"""
        return datetime_to_str(self._get_extra('ts_until'))

    @md_until.setter
    def md_until(self, md_until):
        """Set md_until value from a W3C Datetime value"""
        self._set_extra( 'ts_until', str_to_datetime(md_until, context='md_until datetime') )

    @property
    def capability(self):
        """Get Capability name string"""
        return self._get_extra('capability')

    @capability.setter
    def capability(self, capability):
        """Set Capability name string"""
        self._set_extra('capability', capability)

    @property
    def hash(self):
        """Provide access to the complete hash string

        The hash string may have zero or more hash values with
        appropriate prefixes. All hash values are assumed to be
        strings
        """
        hashvals = []
        if (self.md5 is not None):
            hashvals.append('md5:'+self.md5)
        if (self.sha1 is not None):
            hashvals.append('sha-1:'+self.sha1)
        if (self.sha256 is not None):
            hashvals.append('sha-256:'+self.sha256)
        if (len(hashvals)>0):
            return(' '.join(hashvals))
        return(None)

    @hash.setter
    def hash(self, hash):
        """Parse space separated set of values

        See specification at:
        http://tools.ietf.org/html/draft-snell-atompub-link-extensions-09
        which defines many types. We implement md5, sha-1, sha-256
        """
        self.md5 = None
        self.sha1 = None
        self.sha256 = None
        if (hash is None):
            return
        hash_seen = set()
        errors = []
        for entry in hash.split():
            ( hash_type, value ) = entry.split(':',1)
            if (hash_type in hash_seen):
                errors.append("Ignored duplicate hash type %s" % (hash_type))
            else:
                hash_seen.add(hash_type)
                if (hash_type == 'md5'):
                    self.md5=value
                elif (hash_type == 'sha-1'):
                    self.sha1=value
                elif (hash_type == 'sha-256'):
                    self.sha256=value
                else:
                    errors.append("Ignored unsupported hash type (%s)" % (hash_type))
        if (len(errors)>0):
            raise ValueError(". ".join(errors))

    def link(self,rel):
        """Look for link with specified rel, return else None

        Searches through dicts in self.ln looking for one with the
        specified rel value. If there are multiple links with the 
        same rel then just the first will be returned
        """
        if (self.ln is None):
            return(None)
        for link in self.ln:
            if ('rel' in link and
                link['rel']==rel):
                return(link)
        return(None)

    def link_href(self,rel):
        """Look for link with specified rel, return href from it or None"""
        link = self.link(rel)
        if (link is not None):
            link = link['href']
        return(link)

    def link_set(self,rel,href,allow_duplicates=False,**atts):
        """Set/create link with specified rel, set href and any other attributes

        Any link element must have both rel and href values, the specification
        also defines the type attributes and others are permitted also. See 
        description of allowed formats in

        http://www.openarchives.org/rs/resourcesync.html#DocumentFormats

        Be aware that adding links to a Resource object will 
        significantly increase the size of the object.
        """
        if (self.ln is None):
            # automagically create a self.ln list
            self.ln = []
            link = None
        else:
            link = self.link(rel)
        if (link is not None and not allow_duplicates):
            # overwrite current value
            link['href'] = href
        else:
            # create new link
            link = {'rel':rel,'href':href}
            self.ln.append(link)
        for k in atts:
            link[k] = atts[k]

    def link_add(self,rel,href,**atts):
        """Create an link with specified rel even if one with that rel already exists"""
        self.link_set(rel,href,allow_duplicates=True,**atts)

    @property
    def describedby(self):
        """Convenient access to <rs:ln rel="describedby" href="uri">"""
        return(self.link_href('describedby'))

    @describedby.setter
    def describedby(self,uri):
        """Set ResourceSync Description link to given URI"""
        self.link_set('describedby',uri)

    @property
    def up(self):
        """Get the URI of any ResourceSync rel="up" link"""
        return(self.link_href('up'))

    @up.setter
    def up(self,uri):
        """Set rel="up" link to given URI"""
        self.link_set('up',uri)

    @property
    def index(self):
        """Get the URI of and ResourceSync rel="index" link"""
        return(self.link_href('index'))

    @index.setter
    def index(self,uri):
        """Set rel="index" link to given URI"""
        self.link_set('index',uri)

    @property
    def contents(self):
        """Get the URI of and ResourceSync rel="contents" link"""
        return(self.link_href('index'))

    @contents.setter
    def contents(self,uri,type='application/xml'):
        """Set rel="contents" link to given URI

        Will also set the type="application/xml" unless overridden
        """
        self.link_set('contents',uri,type=type)

    @property
    def basename(self):
        """The resource basename (http://example.com/resource/1 -> 1)"""
        parse_object = urlparse(self.uri)
        return basename(parse_object.path)

    def __eq__(self,other):
        """Equality test for resources allowing <1s difference in timestamp
        
        See equal(...) for more details of equality test
        """
        return( self.equal(other,delta=1.0) )

    def equal(self,other,delta=0.0):
        """Equality or near equality test for resources
        
        Equality means:
        1. same uri, AND
        2. same timestamp WITHIN delta if specified for either, AND
        3. same md5 if specified for both, AND
        4. same length if specified for both
        """
        if (other is None): return False
        
        if (self.uri != other.uri):
            return(False)
        if ( self.timestamp is not None or other.timestamp is not None ):
            # not equal if only one timestamp specified
            if ( self.timestamp is None or 
                 other.timestamp is None or
                 abs(self.timestamp-other.timestamp)>=delta ):
                return(False)
        if ( ( self.md5 is not None and other.md5 is not None ) and
             self.md5 != other.md5 ):
            return(False)
        if ( ( self.length is not None and other.length is not None ) and
             self.length != other.length ):
            return(False)
        return(True)
    
    def __str__(self):
        """Return a human readable string for this resource

        Includes only the parts necessary for synchronizaion and
        designed to support logging.
        """
        s = [ str(self.uri), str(self.lastmod), str(self.length),
              str(self.md5 if self.md5 else self.sha1) ]
        if (self.change is not None):
            s.append(str(self.change))
        if (self.path is not None):
            s.append(str(self.path))
        return "[ " + " | ".join(s) + " ]"
                                         
    def __repr__(self):
        """Return an unambigous representation of this resource

        Uses format like Python's representation of a dict() for 
        attributes. Includes only those attributes with values that 
        are not None. Order defined by __slots__.
        """
        s = []
        for attr in self.__slots__:
            val = getattr(self, attr, None)
            if (val is not None):
                s.append( repr(attr) + ': ' + repr(val) )
        return "{" + ", ".join(s) + "}"
