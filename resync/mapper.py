"""Map between source URIs and destination paths"""
import os
import os.path
import re
import urlparse

class MapperError(Exception):
    pass

class Mapper():
    
    def __init__(self, mappings=None, use_default_path=False):
        self.mappings=[]
        if (mappings):
            self.parse(mappings, use_default_path)

    def __len__(self):
        """Length is number of mappings"""
        return(len(self.mappings))

    def parse(self, mappings, use_default_path=False):
        """Parse a list of map strings (mappings)

        Accepts two distinct formats:
        1. If there are exactly two entries then these may be the source base URI
        and the destination base path. Neither may contain an equals (=) sign.
        2. For any number of mapping stings interpret each as a mapping URI=path. 
        These are in the order they will be tried.
        
        And if default_path is set then a third:
        3. If there is exactly one entry and it does not contain an equals (=)
        sign then default_path is assumed for the local path.
        
        """
        if (use_default_path and
            len(mappings)==1 and
            re.search(r"=",mappings[0])==None):
            self.mappings.append(Map(mappings[0],self.path_from_uri(mappings[0])))
        elif (len(mappings)==2 and 
            re.search(r"=",mappings[0])==None and 
            re.search(r"=",mappings[1])==None):
            self.mappings.append(Map(mappings[0],mappings[1]))
        else:
            for mapping in mappings:
                l=mapping.split('=')
                if (len(l)!=2):
                    raise MapperError("Bad mapping argument (%s), got %s"%(mapping,str(l)))
                (src_uri,dst_path)=l
                # Check for dupes
                for map in self.mappings:
                    if (src_uri == map.src_uri):
                        raise MapperError("Attempt to set duplicate mapping for source URI %s (with destination path %s)" % (src_uri,dst_path))
                    if (dst_path == map.dst_path):
                        raise MapperError("Attempt to set duplicate mapping for destination path %s (with source URI %s)" % (dst_path,src_uri))
                self.mappings.append(Map(src_uri, dst_path))

    def dst_to_src(self,dst_file):
        for map in self.mappings:
            src_uri = map.dst_to_src(dst_file)
            if (src_uri is not None):
                return(src_uri)
        # Must have failed if loop exited
        raise MapperError("Unable to translate destination path (%s) into a source URI." % (dst_file))

    def src_to_dst(self,src_uri):
        for map in self.mappings:
            dst_path = map.src_to_dst(src_uri)
            if (dst_path is not None):
                return(dst_path)
        # Must have failed if loop exited
        raise MapperError("Unable to translate source URI (%s) into a destination path." % (src_uri))

    def path_from_uri(self,uri):
        """Make a safe path name from uri
        """
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse( uri )
        if (netloc == ''):
            netloc = 'localfile'
        path = '/'.join([netloc,path])
        path = re.sub('[^\w\-\.]', '_', path)
        path = re.sub('__+', '_', path)
        path = re.sub('[_\.]+$', '', path)
        path = re.sub('^[_\.]+', '', path)
        return(path)

    def __repr__(self):
        s = 'Mapper: with %d maps:\n' % (len(self.mappings))
        for map in self.mappings:
            s += str(map) + '\n'
        return(s)


class Map:
    """A single map from source URI to destination path

    Both URI and destination paths are assumed to use / as the path
    separator. No account is take for other path separators used
    for paths on non-unix systems. This translation must be done 
    elsewhere by consideration of os.sep.
    """

    def __init__(self,src_uri=None,dst_path=None):
        self.src_uri  = self.strip_trailing_slashes(src_uri)
        self.dst_path = self.strip_trailing_slashes(dst_path)

    def strip_trailing_slashes(self,path):
        """Return input path minus any trailing slashes"""
        m=re.match(r"(.*)/+$",path)
        if (m is None):
            return(path)
        return(m.group(1))

    def dst_to_src(self,dst_file):
        """Return the src URI from the dst filepath

        This does not rely on the destination filepath actually existing on the local
        filesystem, just on pattern matching. Return source URI on success, None on 
        failure.
        """
        m=re.match(self.dst_path+"/(.*)$",dst_file)
        if (m is None):
            return(None)
        rel_path=m.group(1)
        return(self.src_uri+'/'+rel_path)
        
    def src_to_dst(self,src_uri):
        """Return the dst filepath from the src URI
        
        FIXME -- look at whether urlparse can be used here?
        Returns None on failure, destination path on success.
        """
        m=re.match(self.src_uri+"/(.*)$",src_uri)
        if (m is None):
            return(None)
        rel_path=m.group(1)
        return(self.dst_path+'/'+rel_path)

    def __repr__(self):
        return("Map( %s -> %s )" % (self.src_uri, self.dst_path))
