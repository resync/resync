"""ResourceSync Client Utilities.

Code shared by client scripts.
"""

import argparse
from datetime import datetime
import logging
import logging.config

from .url_or_file_open import set_url_or_file_open_config


class ClientFatalError(Exception):
    """Non-recoverable error in client, should include message to user."""

    pass


class ClientError(Exception):
    """Possibly recoverable error in client, should include message to user."""

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
        hh.setLevel(logging.INFO if (verbose) else logging.WARNING)
        hh.setFormatter(logging.Formatter(fmt='%(message)s'))
    if to_file:
        if (logfile is None):
            logfile = default_logfile
        fh = logging.FileHandler(filename=logfile, mode='a')
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG if (eval_mode) else logging.INFO)

    loggers = [default_logger, 'resync']
    if (extra_loggers is not None):
        for logger in extra_loggers:
            loggers.append(logger)
    for logger in loggers:
        log = logging.getLogger(logger)
        log.setLevel(logging.DEBUG)  # control at handler instead
        if human:
            log.addHandler(hh)
        if to_file:
            log.addHandler(fh)

    log = logging.getLogger(default_logger)
    if (to_file):
        log.info("Writing detailed log to %s" % (logfile))


def count_true_args(*args):
    """Count number of list of arguments that evaluate True."""
    count = 0
    for arg in args:
        if (arg):
            count += 1
    return(count)


def parse_links(args_link):
    """Parse --link options.

    Uses parse_link() to parse each option.
    """
    links = []
    if (args_link is not None):
        for link_str in args_link:
            try:
                links.append(parse_link(link_str))
            except ClientFatalError as e:
                raise ClientFatalError(
                    "Bad --link option '%s' (%s)" %
                    (link_str, str(e)))
    return(links)


def parse_link(link_str):
    """Parse one --link option to add to <rs:ln> links.

    Input string of the form: rel,href,att1=val1,att2=val2
    """
    atts = {}
    help_str = "--link option '%s' (format rel,href,att1=val1...)" % (link_str)
    try:
        segs = link_str.split(',')
        # First segments are relation and subject
        atts['rel'] = segs.pop(0)
        atts['href'] = segs.pop(0)
        if (atts['href'] == ''):
            raise ClientFatalError("Missing uri in " + help_str)
        # Remaining segments are attributes
        for term in segs:
            (k, v) = term.split('=')
            if (k == '' or v == ''):
                raise ClientFatalError(
                    "Bad attribute (%s) in " %
                    (term) + help_str)
            atts[k] = v
    except ValueError as e:
        raise ClientFatalError("Bad component of " + help_str)
    except IndexError as e:
        raise ClientFatalError("Incomplete component of " + help_str)

    return(atts)


def parse_capabilities(caps_str):
    """Parse list of capabilities in --capabilitylist option.

    Input string of the form: cap_name=uri,cap_name=uri
    """
    capabilities = {}
    try:
        segs = caps_str.split(',')
        for term in segs:
            (k, v) = term.split('=')
            capabilities[k] = v
    except ValueError as e:
        raise ClientFatalError(
            "Bad component of --capabilitylist option '%s' (%s)" %
            (caps_str, str(e)))
    return(capabilities)


def parse_capability_lists(cls_str):
    """Parse list of capability lists in --capabilitylistindex option.

    Input string of the form: uri,uri
    """
    return(cls_str.split(','))


def add_shared_misc_options(opt, default_logfile, include_remote=False):
    """Add shared miscellaneous options to the argument_group opt.

    Options that the resync-sync, resync-build and resync-explorer scripts use.
    """
    opt.add_argument('--hash', type=str, action='append',
                     help="use specified hash types in addition to last modification time "
                          "and size (repeatable, may include `md5`, `sha-1` and `sha-256`)")
    opt.add_argument('--checksum', action='store_true',
                     help="use md5 checksum in addition to last modification time and size "
                          "(same as --hash=md5)")
    opt.add_argument('--from', type=str, action='store', dest='from_datetime', metavar="DATETIME",
                     help="explicit datetime value used to filter updates in change list for "
                          "--incremental sync")
    opt.add_argument('--exclude', type=str, action='append',
                     help="exclude resources with URI or filename matching the python regex "
                          "supplied (see: <https://docs.python.org/3/howto/regex.html> for regex "
                          "information, repeat option for multiple excludes)")
    opt.add_argument('--multifile', '-m', action='store_true',
                     help="disable reading and output of sitemapindex for multifile sitemap")
    if include_remote:
        opt.add_argument('--noauth', action='store_true',
                         help="disable checking of URL paths to ensure that the sitemaps refer "
                              "only to resources on the same server/sub-path etc. Use with care.")
        opt.add_argument('--access-token', type=str, default=None,
                         help="include this access token (a bearer token) in web requests")
        opt.add_argument('--delay', type=float, default=None,
                         help="add a delay between web requests (default is None)")
        opt.add_argument('--user-agent', type=str, default=None,
                         help="set User-Agent string sent with web requests (default is resync/version)")
    # Want these to show at the end
    opt.add_argument('--logger', '-l', action='store_true',
                     help="create detailed log of client actions (will write "
                          "to %s unless specified with --logfile" % (default_logfile))
    opt.add_argument('--logfile', type=str, action='store',
                     help="create detailed log of client actions")
    opt.add_argument('--spec-version', default='1.1', choices=('1.0', '1.1'),
                     help="follow given ResourceSync specification version. The key difference is that v1.0 "
                          "used lastmod for the time of a change (often also the resource Last-Modification "
                          "time but not always). In v1.1 the rs:md datetime attribute in a ChangeList "
                          "indicates the time of the change, and use of lastmod is entirely optional")
    opt.add_argument('--verbose', '-v', action='store_true',
                     help="verbose, show additional informational messages")


def process_shared_misc_options(args, include_remote=False):
    """Process shared miscellaneous options in args.

    Parse options that the resync-sync, resync-build and resync-explorer scripts use.
    """
    if args.checksum and 'md5' not in args.hash:
        args.hash.append('md5')
    if include_remote:
        if args.access_token:
            set_url_or_file_open_config('bearer_token', args.access_token)
        if args.delay:
            if args.delay < 0.0:
                raise argparse.ArgumentTypeError("--delay must be non-negative!")
            set_url_or_file_open_config('delay', args.delay)
        if args.user_agent:
            set_url_or_file_open_config('user_agent', args.user_agent)
