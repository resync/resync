"""Local version of urlopen that supports local files & web URLs, plus adds auth."""

import re
import time
from urllib.request import Request, urlopen

from . import __version__


# Global configuration settings
NUM_REQUESTS = 0
CONFIG = {
    'bearer_token': None,
    'delay': None,
    'user_agent': 'resync/' + __version__
}


def set_url_or_file_open_config(key, value):
    """Set the global config."""
    global CONFIG
    CONFIG[key] = value


def url_or_file_open(uri, method=None, timeout=None):
    """Wrapper around urlopen() to prepend file: if no scheme provided.

    Can be used as a context manager because the return value from urlopen(...)
    supports both that and straightforwrd use as simple file handle object.

    If timeout is exceeded then urlopen(..) will raise a socket.timeout exception. If
    no timeout is specified then the global default will be used.
    """
    if (not re.match(r'''\w+:''', uri)):
        uri = 'file:' + uri
    headers = {'User-Agent': CONFIG['user_agent']}
    # Do we need to send an Authorization header?
    # FIXME - This token will be added blindy to all requests. This is insecure
    # if the --noauth setting is used allowing requests across different domains.
    # It would be better to have some scheme where a token is tied to a particular
    # domain, or domain pattern.
    if CONFIG['bearer_token'] is not None:
        headers['Authorization'] = 'Bearer ' + CONFIG['bearer_token']
    # Have we got a delay set? Apply only to web requests after first
    global NUM_REQUESTS
    if NUM_REQUESTS != 0 and CONFIG['delay'] is not None and not uri.startswith('file:'):
        time.sleep(CONFIG['delay'])
    NUM_REQUESTS += 1
    maybe_timeout = {} if timeout is None else {'timeout': timeout}
    return urlopen(Request(url=uri, headers=headers, method=method), **maybe_timeout)
