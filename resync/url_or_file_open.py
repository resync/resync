"""Local version of urlopen that supports local files & web URLs, plus adds auth."""

import re
import time
from urllib.request import Request, urlopen

from . import __version__


# Global configuration settings
FIRST_REQUEST = False
CONFIG = {
    'bearer_token': None,
    'delay': None
}


def set_url_or_file_open_config(key, value):
    """Set the global config."""
    global CONFIG
    CONFIG[key] = value


def url_or_file_open(uri):
    """Wrapper around urlopen() to prepend file: if no scheme provided."""
    if (not re.match(r'''\w+:''', uri)):
        uri = 'file:' + uri
    # Do we need to send an Authorization header?
    # FIXME - This token will be added blindy to all requests. This is insecure
    # if the --noauth setting is used allowing requests across different domains.
    # It would be better to have some scheme where a token is tied to a particular
    # domain, or domain pattern.
    headers = {'User-Agent': 'resync/' + __version__}
    if CONFIG['bearer_token'] is not None:
        headers['Authorization'] = 'Bearer ' + CONFIG['bearer_token']
    # Have we got a delay set? Apply only to web requests after first
    global FIRST_REQUEST
    if not FIRST_REQUEST and CONFIG['delay'] is not None and not uri.startswith('file:'):
        FIRST_REQUEST = False
        time.sleep(CONFIG['delay'])
    return(urlopen(Request(url=uri, headers=headers)))
