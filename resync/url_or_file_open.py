"""Local version of urlopen that supports local files & web URLs, plus adds auth."""

import re
from urllib.request import Request, urlopen

from . import __version__


BEARER_TOKEN = None


def set_bearer_token(token):
    """Set the global Authorization header Bearer token.

    FIXME - This token will be added blindy to all requests. This is insecure
    if the --noauth setting is used allowing requests across different domains.
    It would be better to have some scheme where a token is tide to a particular
    domain, or domain pattern.
    """
    global BEARER_TOKEN
    BEARER_TOKEN = token


def url_or_file_open(uri):
    """Wrapper around urlopen() to prepend file: if no scheme provided."""
    if (not re.match(r'''\w+:''', uri)):
        uri = 'file:' + uri
    # Do we need to send an Authorization header?
    headers = {'User-Agent': 'resync/' + __version__}
    if BEARER_TOKEN is not None:
        headers['Authorization'] = 'Bearer ' + BEARER_TOKEN
    return(urlopen(Request(url=uri, headers=headers)))
