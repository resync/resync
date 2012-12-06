"""Information about a web resource

Each web resource is identified by a URI and may optionally have
other metadata such as timestamp, size, md5. The lastmod property
provides ISO8601 format string access to the timestamp.

The timestamp is assumed to be stored in UTC.
"""

import re
from urlparse import urlparse
from posixpath import basename
from w3c_datetime import str_to_datetime, datetime_to_str

class Resource(object):
    __slots__=('uri', 'timestamp', 'size', 'md5', 'sha1',
               'changetype', 'changeid', 'path')
    
    def __init__(self, uri = None, timestamp = None, size = None, 
                 md5 = None, sha1 = None, lastmod = None, 
                 changetype = None, changeid = None, path = None,
                 resource = None ):
        """ Initialize object either from parameters specified or
        from an existing Resource object. If explicit parameters
        are specified then they will override values copied from
        a resource object supplied.
        """
        # Create from a Resource?
        self.uri = None
        self.timestamp = None
        self.size = None
        self.md5 = None
        self.sha1 = None
        self.changetype = None
        self.changeid = None
        self.path = None
        if (resource is not None):
            self.uri = resource.uri
            self.timestamp = resource.timestamp
            self.size = resource.size
            self.md5 = resource.md5
            self.sha1 = resource.sha1
            self.changetype = resource.changetype
            self.changeid = resource.changeid
            self.path = resource.path
        if (uri is not None):
            self.uri = uri
        if (timestamp is not None):
            self.timestamp = timestamp
        if (size is not None):
            self.size = size
        if (md5 is not None):
            self.md5 = md5
        if (sha1 is not None):
            self.sha1 = sha1
        if (changetype is not None):
            self.changetype = changetype
        if (changeid is not None):
            self.changeid = changeid
        if (path is not None):
            self.path = path
        if (lastmod is not None):
            self.lastmod=lastmod
        # Sanity check
        if (self.uri is None):
            raise ValueError("Cannot create resoure without a URI")
            
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
        4. same size if specified for both
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
        if ( ( self.size is not None and other.size is not None ) and
             self.size != other.size ):
            return(False)
        return(True)
    
    def __str__(self):
        """Return a human readable string for this resource"""
        s = [ str(self.uri), str(self.lastmod), str(self.size),
              str(self.md5 if self.md5 else self.sha1) ]
        if (self.changetype is not None):
            s.add(str(self.changetype))
            #s.add(str(self.changeid))
        if (self.path is not None):
            s.add(str(self.path))
        return "[ " + " | ".join(s) + " ]"
                                         
    def __repr__(self):
        """Return an unambigous representation"""
        dict_repr = dict((name, getattr(self, name)) 
                    for name in dir(self) if not (name.startswith('__') 
                                                  or name == 'equal'
                                                  or name == 'basename'
                                                  or name == 'lastmod'))
        return str(dict_repr)
