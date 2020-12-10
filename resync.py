#!/usr/bin/env python
"""resync: The ResourceSync command line client.

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
from resync.client import Client, ClientFatalError
from resync.client_utils import init_logging, count_true_args, parse_links, parse_capabilities, parse_capability_lists

DEFAULT_LOGFILE = 'resync-client.log'


def main():
    """Main function to implement command line script."""
    if (sys.version_info < (2, 7)):
        sys.exit("This program requires python version 2.7 or later")

    # Options and arguments
    p = optparse.OptionParser(description='ResourceSync command line client',
                              usage='usage: %prog [options] uri_path local_path  (-h for help)',
                              version='%prog ' + __version__)

    # Modes
    # a. modes using remote sitemap/resources
    rem = p.add_option_group('REMOTE MODES',
                             'These modes use a remote source that is specified in a set of uri=path mappings '
                             'and potentially also using an explicit --sitemap location. The default mode is '
                             '--baseline. See also: resync-explorer for an interactive client.')
    rem.add_option('--baseline', '-b', action='store_true',
                   help='baseline sync of resources from remote source (src) to local filesystem (dst)')
    rem.add_option('--incremental', '--inc', '-i', action='store_true',
                   help='incremental sync of resources from remote source (src) to local filesystem (dst). Uses either timestamp recorded from last baseline or incremental sync for this source, or explicit --from parameter, to determine the earlier update timestamp to act on.')
    rem.add_option('--audit', '-a', action='store_true',
                   help="audit sync state of destination wrt source")
    rem.add_option('--parse', '-p', action='store_true',
                   help="parse a remote sitemap/sitemapindex (from mapping or explicit --sitemap) and show summary information including document type and number of entries")
    # b. modes based solely on files on local disk
    loc = p.add_option_group('LOCAL MODES',
                             'These modes act on files on the local disk')
    loc.add_option('--write-resourcelist', '--write-resource-list', action='store_true',
                   help="write a resource list based on files on disk using uri=path mappings "
                        "in reverse to calculate URIs from the local paths. Scans local disk "
                        "based either on explicit --paths setting, else starting from all local "
                        "paths specified in the mappings. Writes to STDOUT by default, override "
                        "with --outfile")
    loc.add_option('--write-changelist', '--write-change-list', action='store_true',
                   help="write a change list based on comparison of a reference sitemap "
                        "(specify file with --reference) and either files on disk (using "
                        "the mapping provided) or a second sitemap (specify file with "
                        "--newreference). Otherwise follows --write-resourcelist options. Also accepts "
                        "the --empty option (with no mapping) to write and empty changelist.")
    loc.add_option('--write-capabilitylist', '--write-capability-list', type=str, action='store',
                   help="write a capability list based on the set of capabilities and "
                        "URIs supplied in cap_name=URI,cap_name=URI format. Otherwise "
                        "follows --write-resourcelist options.")
    loc.add_option('--write-sourcedescription', '--write-source-description', type=str, action='store',
                   help="write a Source Description document based on the set of capability "
                        "list URIs supplied as a comma separated list. Otherwise "
                        "follows --write-resourcelist options.")
    loc.add_option('--write-resourcedump', '--write-resource-dump', '-d', action='store_true',
                   help="write a Resource Dump. Specify output file with --outfile and use other "
                        "options as for --write-resourcelist")
    loc.add_option('--write-changedump', '--write-change-dump', action='store_true',
                   help="write a Resource Dump. Specify output file with --outfile and use other "
                        "options as for --write-changelist")

    # Specification of map between remote URI and local file paths, and remote
    # sitemap
    nam = p.add_option_group('FILE/URI NAMING OPTIONS')
    nam.add_option('--outfile', type=str, action='store',
                   help="write output to specified file rather than STDOUT or default")
    nam.add_option('--paths', type=str, action='store',
                   help="explicit set of paths for disk scan --resourceslist or --changelist "
                        "generation")
    nam.add_option('--sitemap', type=str, action='store',
                   help="explicitly set sitemap name, overriding default sitemap.xml "
                        "appended to first source URI specified in the mappings")
    nam.add_option('--capabilitylist', '--capability-list', type=str, action='store',
                   help="explicitly set capability list URI to search for instead of "
                        "looking for the source description")
    nam.add_option('--reference', type=str, action='store',
                   help="reference sitemap name for --write-changelist calculation")
    nam.add_option('--newreference', type=str, action='store',
                   help="updated reference sitemap name for --write-changelist calculation")
    nam.add_option('--changelist-uri', '--change-list-uri', type=str, action='store',
                   help="explicitly set the changelist URI that will be use in --inc mode, "
                        "overrides process of getting this from the sitemap")

    lks = p.add_option_group("LINK GENERATION")
    lks.add_option('--link', type=str, action='append',
                   help="add discovery links to the output sitemap, "
                        "format: rel,href[,att1=val1,att2=val2] "
                        "(repeat option for multiple links)")
    lks.add_option('--describedby-link', type=str, action='store',
                   help="add an <rs:md rel=\"describedby\" link to "
                        "a description of the feed at the URI given")
    lks.add_option('--sourcedescription-link', '--source-description-link',
                   type=str, action='store',
                   help="for a Capability List add a <rs:md rel=\"up\" link to the"
                        "Source Description document at the URI given, else ignored")
    lks.add_option('--capabilitylist-link', '--capability-list-link',
                   type=str, action='store',
                   help="for all documents except a Capability List or a "
                        "Source Description, add an <rs:md rel=\"up\" link "
                        "to the Capability List at the URI given")

    # Options that apply to multiple modes
    opt = p.add_option_group('MISCELANEOUS OPTIONS')
    opt.add_option('--hash', type=str, action='append',
                   help="use specified hash types in addition to last modification time "
                        "and size (repeatable, may include `md5`, `sha-1` and `sha-256`)")
    opt.add_option('--checksum', action='store_true',
                   help="use md5 checksum in addition to last modification time and size "
                        "(same as --hash=md5)")
    opt.add_option('--delete', action='store_true',
                   help="allow files on destination to be deleted")
    opt.add_option('--from', type=str, action='store', dest='from_datetime', metavar="DATETIME",
                   help="explicit datetime value used to filter updates in change list for "
                        "--incremental sync")
    opt.add_option('--exclude', type=str, action='append',
                   help="exclude resources with URI or filename matching the python regex "
                        "supplied (see: <https://docs.python.org/2/howto/regex.html> for regex "
                        "information, repeat option for multiple excludes)")
    opt.add_option('--empty', action='store_true',
                   help="combine with --changelist to write and empty changelist, perhaps with links")
    opt.add_option('--multifile', '-m', action='store_true',
                   help="disable reading and output of sitemapindex for multifile sitemap")
    opt.add_option('--noauth', action='store_true',
                   help="disable all checking of URLs to ensure that the ResourceSync "
                        "documents refer only to resources on the same server or sub-domains. "
                        "Use with care.")
    opt.add_option('--strictauth', action='store_true',
                   help="use more strict checking of URLs to ensure that the ResourceSync "
                        "documents refer only to resources on the same server or sub-domains, "
                        "and on the same server to sub-paths. This is the authority model "
                        "of Sitemaps but there are legitimate uses where these rules would "
                        "not be followed.")
    opt.add_option('--warc', action='store_true',
                   help="write dumps in WARC format (instead of ZIP+Sitemap default)")
    opt.add_option('--dryrun', '-n', action='store_true',
                   help="don't update local resources, say what would be done")
    opt.add_option('--ignore-failures', action='store_true',
                   help="continue past download failures")
    # These likely only useful for experimentation
    opt.add_option('--max-sitemap-entries', type=int, action='store',
                   help="override default size limits")
    # Want these to show at the end
    opt.add_option('--verbose', '-v', action='store_true',
                   help="verbose, show additional informational messages")
    opt.add_option('--logger', '-l', action='store_true',
                   help="create detailed log of client actions (will write "
                        "to %s unless specified with --logfile" %
                        DEFAULT_LOGFILE)
    opt.add_option('--logfile', type='str', action='store',
                   help="create detailed log of client actions")
    opt.add_option('--eval', '-e', action='store_true',
                   help="output evaluation of source/client synchronization performance... "
                        "be warned, this is very verbose")
    opt.add_option('--tries', '-t', type=int, action='store', metavar='TRIES',
                   help="set number of tries to TRIES. The default is to retry 20 times, "
                        "with the exception of fatal errors like \"connection refused\" "
                        "or \"not found\" (404), which are not retried.")
    opt.add_option('--timeout', '-T', type=int, action='store', metavar='SECONDS',
                   help="set the request timeout for resource downloads to SECONDS seconds")

    (args, map) = p.parse_args()

    # Implement exclusive arguments and default --baseline (support for exclusive
    # groups in argparse is incomplete is python2.6)
    if (not args.baseline and not args.incremental and not args.audit
            and not args.parse and not args.write_resourcelist and not args.write_changelist
            and not args.write_capabilitylist and not args.write_sourcedescription
            and not args.write_resourcedump and not args.write_changedump):
        if (len(map) == 0):
            p.error("No arguments specified (use -h for help)")
            return
        else:
            args.baseline = True
    elif (count_true_args(args.baseline, args.incremental, args.audit, args.parse,
                          args.write_resourcelist, args.write_changelist,
                          args.write_capabilitylist, args.write_sourcedescription,
                          args.write_resourcedump, args.write_changedump) > 1):
        p.error("Only one of --baseline, --incremental, --audit, --parse, --write-resourcelist, "
                "--write-changelist, --write-capabilitylist, --write-sourcedescription, "
                "--write-resourcedump, --write-changedump modes allowed")

    # Configure logging module and create logger instance
    init_logging(to_file=args.logger, logfile=args.logfile, default_logfile=DEFAULT_LOGFILE,
                 verbose=args.verbose, eval_mode=args.eval)

    if (args.checksum):
        args.hash.append('md5')
    c = Client(hashes=args.hash,
               verbose=args.verbose,
               dryrun=args.dryrun)

    try:
        if (map):
            # Mappings apply to (almost) everything
            c.set_mappings(map)
        if (args.sitemap):
            c.sitemap_name = args.sitemap
        if (args.capabilitylist):
            c.capability_list_uri = args.capabilitylist
        if (args.warc):
            c.dump_format = 'warc'
        if (args.exclude):
            c.exclude_patterns = args.exclude
        if (args.multifile):
            c.allow_multifile = not args.multifile
        if (args.noauth):
            c.noauth = args.noauth
        if (args.strictauth):
            c.strictauth = args.strictauth
        if (args.max_sitemap_entries):
            c.max_sitemap_entries = args.max_sitemap_entries
        if (args.ignore_failures):
            c.ignore_failures = args.ignore_failures
        if (args.tries):
            c.tries = args.tries
        if (args.timeout):
            c.timeout = args.timeout

        # Links apply to anything that writes sitemaps
        links = parse_links(args.link)
        # Add specific links is appropriate cases
        if (args.capabilitylist_link
                and not args.write_capabilitylist
                and not args.write_sourcedescription):
            # rel="up" to Capability List in all but Capability List
            # and Source Description
            links.insert(0, {'rel': 'up', 'href': args.capabilitylist_link})
        if (args.sourcedescription_link and args.write_capabilitylist):
            # rel="up" to Source Description from Capability List
            links.insert(0, {'rel': 'up', 'href': args.sourcedescription_link})
        if (args.describedby_link):
            links.insert(0, {'rel': 'describedby',
                             'href': args.describedby_link})

        # Finally, do something...
        if (args.baseline or args.audit):
            c.baseline_or_audit(allow_deletion=args.delete,
                                audit_only=args.audit)
        elif (args.incremental):
            c.incremental(allow_deletion=args.delete,
                          change_list_uri=args.changelist_uri,
                          from_datetime=args.from_datetime)
        elif (args.parse):
            c.parse_document()
        elif (args.write_resourcelist or args.write_resourcedump):
            c.write_resource_list(paths=args.paths,
                                  outfile=args.outfile,
                                  links=links,
                                  dump=args.write_resourcedump)
        elif (args.write_changelist or args.write_changedump):
            if (not args.reference and not args.empty):
                p.error(
                    "Must supply --reference sitemap for --changelist, or --empty")
            c.write_change_list(ref_sitemap=args.reference,
                                newref_sitemap=(args.newreference if (
                                    args.newreference) else None),
                                empty=args.empty,
                                paths=args.paths,
                                outfile=args.outfile,
                                links=links,
                                dump=args.write_changedump)
        elif (args.write_capabilitylist):
            c.write_capability_list(
                capabilities=parse_capabilities(args.write_capabilitylist),
                outfile=args.outfile,
                links=links)
        elif (args.write_sourcedescription):
            c.write_source_description(
                capability_lists=parse_capability_lists(
                    args.write_sourcedescription),
                outfile=args.outfile,
                links=links)
        else:
            p.error("Unknown mode requested")
    # Any problem we expect will come as a ClientFatalError, anything else
    # is... an exception ;-)
    except ClientFatalError as e:
        sys.stderr.write("\nFatalError: " + str(e) + "\n")


if __name__ == '__main__':
    main()
