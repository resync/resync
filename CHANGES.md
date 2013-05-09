=================
resync change log
=================

The first two components of the version tags are tied to the ResourceSync specification 
version. Versions 0.6.x are intended to implement the v0.6 ResourceSync specification
(http://www.openarchives.org/rs/0.6/),

v0.6.1 2013-05-09
- First release working toward v0.6 specification
- Changed test examples to be those from v0.6 specification
- Added first stab at ResourceDump and ResourceDumpManifest objects

v0.5.3 2013-05-08
- Final release working with v0.5 specification
- Improve handling of assumed mappings for testing client on a local filesystem
- Fix sitemapindex support for large resource lists, add rel="up" for component sitemaps

v0.5.2 2013-03-26
- Fix setup.py

v0.5.1 2013-03-22
- Code reworked for 0.5 specification (http://www.openarchives.org/rs/0.5/)
- Client code handles --baseline, --audit and --incremental sync against the simulator
