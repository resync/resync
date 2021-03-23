"""Determine URI authority based on DNS and paths."""

from urllib.parse import urlparse
import os.path


class UrlAuthority(object):
    """Determine URI authority based on DNS and paths.

    Determine whether one resource can speak authoritatively
    about another based on DNS hierarchy of server names and
    path hierarchy within URLs.

    Two modes are supported:

    strict=True: requires that a query URL has the same URI
    scheme (e.g. http) as the primary, is on the same server
    or one in a sub-domain, and that the path component is
    at the same level or below the primary.

    strict=False (default): requires only that a query URL
    has the same URI scheme as the primary, and is on the same
    server or one in a sub-domain of the primary.

    Example use:

        from resync.url_authority import UrlAuthority

        auth = UrlAuthority("http://example.org/primary")
        if (auth.has_authority_over("http://example.com/res1")):
            # will be true
        if (auth.has_authority_over("http://other.com/res1")):
            # will be false
    """

    def __init__(self, url=None, strict=False):
        """Create object and optionally set primary url and/or strict mode."""
        self.url = url
        self.strict = strict
        if (self.url is not None):
            self.set_primary(self.url)
        else:
            self.primary_scheme = 'none'
            self.primary_netloc = 'none.none.none'
            self.primary_path = '/not/very/likely'

    def set_primary(self, url):
        """Set the primary url that this object works with."""
        m = urlparse(url)
        self.primary_scheme = m.scheme
        self.primary_netloc = m.netloc
        self.primary_path = os.path.dirname(m.path)

    def has_authority_over(self, url):
        """Return True of the current primary has authority over url.

        In strict mode checks scheme, server and path. Otherwise checks
        just that the server names match or the query url is a
        sub-domain of the primary.
        """
        s = urlparse(url)
        if (s.scheme != self.primary_scheme):
            return(False)
        if (s.netloc != self.primary_netloc):
            if (not s.netloc.endswith('.' + self.primary_netloc)):
                return(False)
            # Maybe should allow parallel for 3+ components, eg. a.example.org,
            # b.example.org
        path = os.path.dirname(s.path)
        if (self.strict and path != self.primary_path
                and not path.startswith(self.primary_path)):
            return(False)
        return(True)
