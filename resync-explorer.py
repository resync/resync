#!/usr/bin/env python
"""resync-explorer: The ResourceSync explorer.

Copyright 2012-2020 Simeon Warner

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

import optparse
import sys

from resync import __version__
from resync.client import ClientFatalError
from resync.client_utils import init_logging, add_shared_misc_options, process_shared_misc_options
from resync.explorer import Explorer

DEFAULT_LOGFILE = 'resync-explorer.log'


def main():
    """Main function to implement command line script."""
    if (sys.version_info < (2, 7)):
        sys.exit("This program requires python version 2.7 or later")

    # Options and arguments
    p = optparse.OptionParser(description='ResourceSync explorer',
                              usage='usage: %prog [options] uri_path local_path  (-h for help)',
                              version='%prog ' + __version__)

    # Specification of map between remote URI and local file paths, and remote
    # sitemap
    nam = p.add_option_group('FILE/URI NAMING OPTIONS')
    nam.add_option('--outfile', type=str, action='store',
                   help="write sitemap to specified file rather than STDOUT")
    nam.add_option('--paths', type=str, action='store',
                   help="explicit set of paths for disk scan --resourceslist or --changelist "
                        "generation")
    nam.add_option('--sitemap', type=str, action='store',
                   help="explicitly set sitemap name, overriding default sitemap.xml "
                        "appended to first source URI specified in the mappings")
    nam.add_option('--reference', type=str, action='store',
                   help="reference sitemap name for --changelist calculation")
    nam.add_option('--newreference', type=str, action='store',
                   help="updated reference sitemap name for --changelist calculation")
    nam.add_option('--dump', metavar='DUMPFILE', type=str, action='store',
                   help="write dump to specified file for --resourcelist or --changelist")
    nam.add_option('--changelist-uri', '--change-list-uri', type=str, action='store',
                   help="explicitly set the changelist URI that will be use in --inc mode, "
                        "overrides process of getting this from the sitemap")

    # Options that apply to multiple modes
    opt = p.add_option_group('MISCELANEOUS OPTIONS')
    opt.add_option('--max-sitemap-entries', type=int, action='store',
                   help="override default size limits")
    add_shared_misc_options(opt, default_logfile=DEFAULT_LOGFILE)

    (args, map) = p.parse_args()

    init_logging(to_file=args.logger, logfile=args.logfile, default_logfile=DEFAULT_LOGFILE,
                 verbose=args.verbose)

    print("----- ResourceSync Explorer -----")
    process_shared_misc_options(args)

    c = Explorer(hashes=args.hash,
                 verbose=args.verbose)

    try:
        if (map):
            # Mappings apply to (almost) everything
            c.set_mappings(map)
        if (args.sitemap):
            c.sitemap_name = args.sitemap
        if (args.exclude):
            c.exclude_patterns = args.exclude
        if (args.multifile):
            c.allow_multifile = not args.multifile
        if (args.noauth):
            c.noauth = args.noauth
        if (args.max_sitemap_entries):
            c.max_sitemap_entries = args.max_sitemap_entries

        c.explore()

    # Any problem we expect will come as a ClientFatalError, anything else
    # is... an exception ;-)
    except ClientFatalError as e:
        sys.stderr.write("\nFatalError: " + str(e) + "\n")


if __name__ == '__main__':
    main()
