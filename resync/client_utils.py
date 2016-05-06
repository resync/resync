"""ResourceSync Client Utilities.

Factor out code shared by both the resync and resync-explorer
clients.

Copyright 2012-2016 Simeon Warner

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License
"""

try: #python3
    from urllib.request import urlopen
except ImportError: #python2
    from urllib import urlopen
import logging
import logging.config
from datetime import datetime
import re

class ClientFatalError(Exception):
    """Non-recoverable error in client, should include message to user."""

    pass

class UTCFormatter(logging.Formatter):
    """Format datetime values as ISO8601 UTC Z form.

    Based on http://bit.ly/T2n3Xk
    """

    def formatTime(self, record, datefmt=None):
        """Format datetime of record.created as ISO8601 UTC Z form."""
        timestamp = record.created
        return datetime.utcfromtimestamp(timestamp).isoformat() + 'Z'

def init_logging(to_file=False, logfile=None, default_logfile='/tmp/resync.log',
                 human=True, verbose=False, eval_mode=False, 
                 default_logger='client', extra_loggers=None):
    """Initialize logging.

    Use of log levels:
    DEBUG - very verbose, for evaluation of output (-e)
    INFO - verbose, only seen by users if they ask for it (-v)
    WARNING - messages output messages to console

    Logging to a file: If to_file is True then output will be written to 
    a file. This will be logfile if set, else default_logfile (which may
    also be overridden).
    """
    fmt = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    formatter = UTCFormatter(fmt)
    
    if human:
        # Create a special handler designed just for human readable output
        hh = logging.StreamHandler()
        hh.setLevel( logging.INFO if (verbose) else logging.WARNING )
        hh.setFormatter(logging.Formatter(fmt='%(message)s'))
    if to_file:
        if (logfile is None):
            logfile = default_logfile
        fh = logging.FileHandler(filename=logfile, mode='a')
        fh.setFormatter(formatter)
        fh.setLevel( logging.DEBUG if (eval_mode) else logging.INFO )

    loggers = [default_logger,'resync']
    if (extra_loggers is not None):
        for logger in extra_loggers:
            loggers.append(logger)
    for logger in loggers:
        log = logging.getLogger(logger)
        log.setLevel(logging.DEBUG) #control at handler instead
        if human:
            log.addHandler(hh)
        if to_file:
            log.addHandler(fh)

    log=logging.getLogger(default_logger)
    if (to_file):
        log.info("Writing detailed log to %s" % (logfile))


def count_true_args(*args):
    """Count number of list of arguments that evaluate True."""
    count=0
    for arg in args:
        if (arg):
            count+=1
    return(count)

def parse_links(args_link):
    """Parse --link options.

    Uses parse_link() to parse each option.
    """
    links=[]
    if (args_link is not None):
        for link_str in args_link:
            try:
                links.append(parse_link(link_str))
            except ClientFatalError as e:
                raise ClientFatalError("Bad --link option '%s' (%s)" % (link_str,str(e)))
    return(links)

def parse_link(link_str):
    """Parse one --link option to add to <rs:ln> links.

    Input string of the form: rel,href,att1=val1,att2=val2
    """
    atts={}
    help_str = "--link option '%s' (format rel,href,att1=val1...)"%(link_str)
    try:
        segs = link_str.split(',')
        # First segments are relation and subject
        atts['rel'] = segs.pop(0)
        atts['href'] = segs.pop(0)
        if (atts['href']==''):
            raise ClientFatalError("Missing uri in " + help_str)
        # Remaining segments are attributes
        for term in segs:
            (k,v)=term.split('=')
            if (k=='' or v==''):
                raise ClientFatalError("Bad attribute (%s) in " % (term) + help_str)
            atts[k]=v
    except ValueError as e:
        raise ClientFatalError("Bad component of " + help_str)
    except IndexError as e:
        raise ClientFatalError("Incomplete component of " + help_str)
    
    return(atts)

def parse_capabilities(caps_str):
    """Parse list of capabilities in --capabilitylist option.

    Input string of the form: cap_name=uri,cap_name=uri
    """
    capabilities={}
    try:
        segs = caps_str.split(',')
        for term in segs:
            (k,v)=term.split('=')
            capabilities[k]=v
    except ValueError as e:
        raise ClientFatalError("Bad component of --capabilitylist option '%s' (%s)"%(caps_str,str(e)))
    return(capabilities)

def parse_capability_lists(cls_str):
    """Parse list of capability lists in --capabilitylistindex option.

    Input string of the form: uri,uri
    """
    return(cls_str.split(','))
  
def url_or_file_open(uri):
    """Wrapper around urlopen() to prepend file: if no scheme provided."""
    if (not re.match(r'''\w+:''',uri)):
        uri = 'file:'+uri
    return(urlopen(uri))

