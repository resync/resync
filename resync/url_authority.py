"""Determine whether one resource can speak authoritatively about another"""

import urlparse
import os.path

class UrlAuthority(object):

    def __init__(self, url=None):
        self.url = url
        if (self.url is not None):
            self.set_master(self.url)
        else:
            self.master_scheme='none'
            self.master_netloc='none.none.none'
            self.master_path='/not/very/likely'

    def set_master(self, url):
        """Set the master url that this object works with"""
        m = urlparse.urlparse(url)
        self.master_scheme=m.scheme
        self.master_netloc=m.netloc
        self.master_path=os.path.dirname(m.path)

    def has_authority_over(self, url):
        """Returns True of the current master has authority over url"""
        s = urlparse.urlparse(url)
        if (s.scheme != self.master_scheme):
            return(False)
        if (s.netloc != self.master_netloc):
            if (not s.netloc.endswith('.'+self.master_netloc)):
                return(False)
            #Maybe should allow parallel for 3+ components, eg. a.example.org, b.example.org
        path = os.path.dirname(s.path)
        if (path != self.master_path and
            not path.startswith(self.master_path)):
            return(False)
        return(True)


