"""Information about a web resource

Each web resource is identified by a URI and may optionally have
other metadata such as timestamp, length, md5. The lastmod property
provides ISO8601 format string access to the timestamp.

The timestamp is assumed to be stored in UTC.

This object is optimized for size in the case whether there is not large
data in the attributes. This is done using __slots__ for the attributes
so that there is no __dict__ defined. The 'ln' attribute is used if
necessary to add links or other information in a hash which is convenient
but will significantly increase the size of each object with such
information.
"""

import re
from urlparse import urlparse
from posixpath import basename
from w3c_datetime import str_to_datetime, datetime_to_str
import _version

class ChangeTypeError(Exception):
    def __init__(self, val):
        self.supplied = val

    def __repr__(self):
        return "<ChangeTypeError: got %s, expected one of [created, updated, deleted]>" % self.supplied

    def __str__(self):
        return repr(self)

class Resource(object):
    __slots__=('uri', 'timestamp', 'length',
               'md5', 'sha1', 'sha256', 'type',
               'change', 'path',
               'capability', 'ln' )
    
    def __init__(self, uri = None, timestamp = None, length = None, 
                 md5 = None, sha1 = None, sha256 = None, type = None,
                 change = None, path = None,
                 lastmod = None, resource = None,
                 capability = None, ln = None):
        """ Initialize object either from parameters specified or
        from an existing Resource object. If explicit parameters
        are specified then they will override values copied from
        a resource object supplied.
        """
        # Create from a Resource?
        self.uri = None
        self.timestamp = None
        self.length = None
        self.md5 = None
        self.sha1 = None
        self.sha256 = None
        self.type = None
        self.change = None
        self.path = None
        self.capability = None
        self.ln = None
        if (resource is not None):
            self.uri = resource.uri
            self.timestamp = resource.timestamp
            self.length = resource.length
            self.md5 = resource.md5
            self.sha1 = resource.sha1
            self.sha256 = resource.sha256
            self.change = resource.change
            self.path = resource.path
            self.capability = resource.capability
            self.ln = resource.ln
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
        # FIXME: type is a builtin function, please use 'typ' for variable name
        if (type is not None):
            self.type = type
        if (change is not None):
            self.change = change
        if (path is not None):
            self.path = path
        if (capability is not None):
            self.capability = capability
        if (ln is not None):
            self.ln = ln
        if (lastmod is not None):
            self.lastmod=lastmod
        # Sanity check
        if (self.uri is None):
            raise ValueError("Cannot create resoure without a URI")


    def __setattr__(self, prop, value):
        if (prop == 'change' and not value in _version.CHANGE_TYPES):
            raise ChangeTypeError(value)
        else:
            object.__setattr__(self, prop, value)
            
    @property
    def lastmod(self):
        """The Last-Modified data in W3C Datetime syntax, Z notation"""
        if (self.timestamp is None):
            return None
        return datetime_to_str(self.timestamp)

    @lastmod.setter
    def lastmod(self, lastmod):
        """Set timestamp from an W3C Datetime Last-Modified value"""
        if (lastmod is None):
            self.timestamp = None
            return
        if (lastmod == ''):
            raise ValueError('Attempt to set empty lastmod')
        self.timestamp = str_to_datetime(lastmod)

    @property
    def hash(self):
        """Provide access to the total hash string"""
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

        http://tools.ietf.org/html/draft-snell-atompub-link-extensions-09
        defines many types, we implement md5, sha-1, sha-256"""
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

    @property
    def basename(self):
        """The resource basename (http://example.com/resource/1 -> 1)"""
        parse_object = urlparse(self.uri)
        return basename(parse_object.path)

    def __eq__(self,other):
        """Equality test for resources allowing <1s difference in timestamp"""
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

        Includes only part necessary for synchronizaion
        """
        s = [ str(self.uri), str(self.lastmod), str(self.length),
              str(self.md5 if self.md5 else self.sha1) ]
        if (self.change is not None):
            s.append(str(self.change))
        if (self.path is not None):
            s.append(str(self.path))
        return "[ " + " | ".join(s) + " ]"
                                         
    def __repr__(self):
        """Return an unambigous representation"""
        dict_repr = dict((name, getattr(self, name, None)) 
                    for name in dir(self) if not (name.startswith('__') 
                                                  or name == 'equal'
                                                  or name == 'basename'
                                                  or name == 'lastmod'))
        return str(dict_repr)
