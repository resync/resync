"""Map between source URIs and destination paths."""

import os
import os.path
import re
try:  # python3
    from urllib.parse import urlparse
except ImportError:  # pragma: no cover  python2
    from urlparse import urlparse  # pragma: no cover
import logging


class Mapper():
    """Mapper object to map between source URIs and destination paths.

    Implemented as a list of Map objects.
    """

    def __init__(self, mappings=None, use_default_path=False):
        """Initialize Mapper."""
        self.logger = logging.getLogger('resync.mapper')
        self.mappings = []
        if (mappings):
            self.parse(mappings, use_default_path)

    def __len__(self):
        """Length is number of mappings."""
        return(len(self.mappings))

    def parse(self, mappings, use_default_path=False):
        """Parse a list of map strings (mappings).

        Accepts two distinct formats:
        1. If there are exactly two entries then these may be the source
        base URI and the destination base path. Neither may contain an
        equals (=) sign.
        2. For any number of mapping stings interpret each as a mapping
        URI=path. These are in the order they will be tried.

        And if use_default_path is True then a third:
        3. If there is exactly one entry and it does not contain an
        equals (=) sign then a safe local path is created based on the
        source base URI. In the case that the source base URI is a local
        path already then an indentity mapping is used.
        """
        if (use_default_path
                and len(mappings) == 1
                and re.search(r"=", mappings[0]) is None):
            path = self.path_from_uri(mappings[0])
            self.logger.warning("Using URI mapping: %s -> %s" %
                                (mappings[0], path))
            self.mappings.append(Map(mappings[0], path))
        elif (len(mappings) == 2
                and re.search(r"=", mappings[0]) is None
                and re.search(r"=", mappings[1]) is None):
            self.mappings.append(Map(mappings[0], mappings[1]))
        else:
            for mapping in mappings:
                entry = mapping.split('=')
                if (len(entry) != 2):
                    raise MapperError(
                        "Bad mapping argument (%s), got %s" %
                        (mapping, str(entry)))
                (src_uri, dst_path) = entry
                # Check for dupes
                for map in self.mappings:
                    if (src_uri == map.src_uri):
                        raise MapperError(
                            "Attempt to set duplicate mapping for "
                            "source URI %s (with destination path %s)" %
                            (src_uri, dst_path))
                    if (dst_path == map.dst_path):
                        raise MapperError(
                            "Attempt to set duplicate mapping for "
                            "destination path %s (with source URI %s)" %
                            (dst_path, src_uri))
                self.mappings.append(Map(src_uri, dst_path))

    def default_src_uri(self):
        """Default src_uri from mapping.

        This is take just to be the src_uri of the first entry
        """
        if (len(self.mappings) > 0):
            return(self.mappings[0].src_uri)
        raise MapperError("Can't get default source URI from empty mapping")

    def unsafe(self):
        """True if one or more mapping is unsafe.

        See Map.unsafe() for logic. Provide this as a test rather than
        building into object creation/parse because it is useful to
        allow unsafe mappings in situations where it doesn't matter.
        """
        for map in self.mappings:
            if (map.unsafe()):
                return(True)
        return(False)

    def dst_to_src(self, dst_file):
        """Map destination path to source URI."""
        for map in self.mappings:
            src_uri = map.dst_to_src(dst_file)
            if (src_uri is not None):
                return(src_uri)
        # Must have failed if loop exited
        raise MapperError(
            "Unable to translate destination path (%s) "
            "into a source URI." % (dst_file))

    def src_to_dst(self, src_uri):
        """Map source URI to destination path."""
        for map in self.mappings:
            dst_path = map.src_to_dst(src_uri)
            if (dst_path is not None):
                return(dst_path)
        # Must have failed if loop exited
        raise MapperError(
            "Unable to translate source URI (%s) into "
            "a destination path." % (src_uri))

    def path_from_uri(self, uri):
        """Make a safe path name from uri.

        In the case that uri is already a local path then the
        same path is returned.
        """
        (scheme, netloc, path, params, query, frag) = urlparse(uri)
        if (netloc == ''):
            return(uri)
        path = '/'.join([netloc, path])
        path = re.sub(r'[^\w\-\.]', '_', path)
        path = re.sub(r'__+', '_', path)
        path = re.sub(r'[_\.]+$', '', path)
        path = re.sub(r'^[_\.]+', '', path)
        return(path)

    def __repr__(self):
        """Human readable dump of all Maps in the Mapper."""
        s = 'Mapper with %d maps:\n' % (len(self.mappings))
        for map in self.mappings:
            s += str(map) + '\n'
        return(s)


class Map:
    """A single map from source URI to destination path.

    Both URI and destination paths are assumed to use / as the path
    separator. No account is take for other path separators used
    for paths on non-unix systems. This translation must be done
    elsewhere by consideration of os.sep.
    """

    def __init__(self, src_uri=None, dst_path=None):
        """Initialize Map object.

        Will strip trailing slashes from src_uri and dst_path.
        """
        self.src_uri = self.strip_trailing_slashes(src_uri)
        self.dst_path = self.strip_trailing_slashes(dst_path)

    def strip_trailing_slashes(self, path):
        """Return input path minus any trailing slashes."""
        m = re.match(r"(.*)/+$", path)
        if (m is None):
            return(path)
        return(m.group(1))

    def dst_to_src(self, dst_file):
        """Return the src URI from the dst filepath.

        This does not rely on the destination filepath actually
        existing on the local filesystem, just on pattern matching.
        Return source URI on success, None on failure.

        Relies upon self.dst_path and self.src_path not including trailing
        slashes. However, a match of just self.dst_path withouth a trailing
        slash will return self.src_path with a trailing slash.
        """
        m = re.match(self.dst_path + "(/.*)?$", dst_file)
        if (m is None):
            return(None)
        rel_path = m.group(1)
        if rel_path is None:
            rel_path = '/'
        return self.src_uri + rel_path

    def src_to_dst(self, src_uri):
        """Return the dst filepath from the src URI.

        Returns None on failure, local destination path on success.

        Relies upon self.dst_path and self.src_path not including trailing
        slashes. However, a match of just self.src_path withouth a trailing
        slash will return self.dst_path with a trailing slash.
        """
        m = re.match(self.src_uri + "(/.*)?$", src_uri)
        if (m is None):
            return(None)
        rel_path = m.group(1)
        if rel_path is None:
            rel_path = '/'
        return self.dst_path + rel_path

    def unsafe(self):
        """True if the mapping is unsafe for an update.

        Applies only to local source. Returns True if the paths for source and
        destination are the same, or if one is a component of the other path.
        """
        (scheme, netloc, path, params, query, frag) = urlparse(self.src_uri)
        if (scheme != ''):
            return(False)
        s = os.path.normpath(self.src_uri)
        d = os.path.normpath(self.dst_path)
        lcp = os.path.commonprefix([s, d])
        return(s == lcp or d == lcp)

    def __repr__(self):
        """Human readable string for one map."""
        return("Map( %s -> %s )" % (self.src_uri, self.dst_path))


class MapperError(Exception):
    """Exception for errors in Mapper class."""

    pass
