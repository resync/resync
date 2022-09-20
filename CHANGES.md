# resync change log

v2.0.2 2022-09-30
  * Add --user-agent option to set web User-Agent string
  * Avoid misleading "(0 bytes)" output when no Content-Length given (https://github.com/resync/resync/issues/52)

v2.0.1 2021-03-23
  * Route all URI and file requests through `resync/url_or_file_open.py` so that settings such as authentication headers can be consistently applied
  * Do not exclude any directories from sync by default, specify with --exclude
  * Fix comparison of using possibly multiple checksums
  * Improve test coverage
  * Remove Python 2 cruft

v2.0.0 2020-12-16
  * Supports ResourceSync v1.1 ANSI/NISO Z39.99-2017 <http://www.openarchives.org/rs/1.1/toc> as default
  * Support for the prior v1.0 ANSI/NISO Z39.99-2014 <http://www.openarchives.org/rs/1.0/toc> is retained with `spec-version='1.0'` option in scripts and `spec_version='1.0'` in various classes
  * Split old `resync` script into `resync-sync` and `resync-build`
  * Move scripts from `bin` dir to base dir for easier testing/development (now that there is no conflict with the module name)
  * Switch from optparse to argparse, use exclusive argument group for commands
  * Add --access_token option to pass bearer token with web requests
  * Add --delay option to pause between successive web requests
  * Drop Python 2.7, 3.3 & 3.4 from tests, add 3.7 & 3.8
  * Fix various depracation warnings and errors for 3.7 & 3.8
  * Switch from pep8 to pycodestyle in tests
  * Change README from RDS to github flavored Markdown
  * Move libraries to support tests into test/testlib

v1.0.9 2018-10-23
  * Add -t/--tries and -T/--timeout options (https://github.com/resync/resync/issues/34)
  * Includes partial replacement of urllib.request with requests

v1.0.8 2017-08-30
  * Fix support for explicitly writing ResourceList objects as indexes (https://github.com/resync/resync/issues/31)
  * Change argument names for local modes to have `--write-` prefix, e.g. --write-resourcelist
  * Improve modes to detect capabilities
  * Abandon support for Python 2.6 (https://github.com/resync/resync/issues/23)

v1.0.7 2017-03-27
  * Fixed silly error in `resync-explorer` introduced in 1.0.6

v1.0.6 2017-03-20
  * Fixed md5 hash format (https://github.com/resync/resync/issues/25)
  * Added support for sha-1 and sha-256 hashes

v1.0.5 2017-01-30
  * Fixed to support non-ASCII URIs/filenames (https://github.com/resync/resync/issues/22)
  * Added tests for Python 3.6
  * Temporarily disabled tests for Python 2.6 due to problems with coverage (https://github.com/resync/resync/issues/23)
  
v1.0.4 2017-01-27
  * pep8 formatting
  * Added contributing note

v1.0.2 2016-05-06
  * Python 3 fixes in resync-explorer
  * Improved test coverage
  * pep257 formatting

v1.0.1 2016-03-22
  * Work with Python 2 (2.6/2.7) and Python 3 (3.3/3.4/3.5)
  * Improved test coverage
  * Use defusedxml for safer XML parsing
  * Changed parameter str to str_data in ListBase.parse(), str still supported
    but deprecated. Issue pointed out by @uweschmitt

v1.0.0 2014-06-18
  * Update for v1.0, Z39.99-2014 specification (http://www.openarchives.org/rs/1.0/)
  * Partial implementation of dump output (no read yet)

v0.9.5 2013-11-06
  * Still working toward v0.9.1 specification (http://www.openarchives.org/rs/0.9.1/)
  * Set up for Travis-CI working from github
  * Use /usr/bin/env to find python in executables
  * Fix timezone handling in w3c_datetime.py
  * Fix a number of documentation inconsistencies
 
v0.9.4 2013-09-06
  * Work toward v0.9.1 specification (http://www.openarchives.org/rs/0.9.1/)
  * ResourceSync Description becomes Source Description

v0.9.3 2013-07-31
  * Add dependencies and tests to setup, no code changes 

v0.9.2 2013-07-04
  * Cosmetic only

v0.9.1 2013-07-04
  * First release working toward v0.9 specification
  * Use test examples from v0.9 specification, add code to build them too
  * Added ResourceSync Description document
  * Improved resync-explore binary replaces --explore mode
  * Relax default notion of URL authority, add --strictauth

v0.6.3 2013-05...
  * Improved --explore mode

v0.6.2 2013-05-14
  * Fixed example code in README!
  * Added --version flag
  * Added --paths option to specify local paths to search rather than mappings

v0.6.1 2013-05-09
  * First release working toward v0.6 specification
  * Changed test examples to be those from v0.6 specification
  * Added first stab at ResourceDump and ResourceDumpManifest objects

v0.5.3 2013-05-08
  * Final release working with v0.5 specification
  * Improved handling of assumed mappings for testing client on a local filesystem
  * Fixed sitemapindex support for large resource lists, add rel="up" for component sitemaps

v0.5.2 2013-03-26
  * Fixed setup.py

v0.5.1 2013-03-22
  * Code reworked for 0.5 specification (http://www.openarchives.org/rs/0.5/)
  * Client code handles --baseline, --audit and --incremental sync against the simulator
