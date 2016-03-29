"""Determine URI authority based on DNS and paths."""

try: #python3
    from urllib.parse import urlparse
except ImportError: #python2
    from urlparse import urlparse
import os.path

class UrlAuthority(object):

    """Determine URI authority based on DNS and paths.

    Determine whether one resource can speak authoritatively
    about another based on DNS hierarchy of server names and
    path hierarchy within URLs.

    Two modes are supported:

    strict=True: requires that a query URL has the same URI 
    scheme (e.g. http) as the master, is on the same server
    or one in a sub-domain, and that the path component is
    at the same level or below the master.

    strict=False (default): requires only that a query URL
    has the same URI scheme as the master, and is on the same 
    server or one in a sub-domain of the master.

    Example use:

        from resync.url_authority import UrlAuthority

        auth = UrlAuthority("http://example.org/master")
        if (auth.has_authority_over("http://example.com/res1")):
            # will be true
        if (auth.has_authority_over("http://other.com/res1")):
            # will be false
    """

    def __init__(self, url=None, strict=False):
        """Create object and optionally set master url and/or strict mode."""
        self.url = url
        self.strict = strict
        if (self.url is not None):
            self.set_master(self.url)
        else:
            self.master_scheme='none'
            self.master_netloc='none.none.none'
            self.master_path='/not/very/likely'

    def set_master(self, url):
        """Set the master url that this object works with."""
        m = urlparse(url)
        self.master_scheme=m.scheme
        self.master_netloc=m.netloc
        self.master_path=os.path.dirname(m.path)

    def has_authority_over(self, url):
        """Return True of the current master has authority over url.

        In strict mode checks scheme, server and path. Otherwise checks
        just that the server names match or the query url is a 
        sub-domain of the master
        """
        s = urlparse(url)
        if (s.scheme != self.master_scheme):
            return(False)
        if (s.netloc != self.master_netloc):
            if (not s.netloc.endswith('.'+self.master_netloc)):
                return(False)
            #Maybe should allow parallel for 3+ components, eg. a.example.org, b.example.org
        path = os.path.dirname(s.path)
        if (self.strict and
            path != self.master_path and
            not path.startswith(self.master_path)):
            return(False)
        return(True)
