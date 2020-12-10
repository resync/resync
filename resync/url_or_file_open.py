"""Local version of urlopen that supports files+web and auth."""

import re
from urllib.request import urlopen


def url_or_file_open(uri):
    """Wrapper around urlopen() to prepend file: if no scheme provided."""
    if (not re.match(r'''\w+:''', uri)):
        uri = 'file:' + uri
    return(urlopen(uri))
