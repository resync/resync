To do list for resync client and library
========================================

See also issues on github tracker. Other big threads that need attention are:

- work through and test creation of Resource and Change Dump ZIPs
- add use of a Resource and Change Dump ZIPs
- add archives (ResoourceListArchive, ChangeListArchive, ResourceDumpArchive, ChangeDumpArchive)
- consider breaking out handling of links that is somewhat duplicated in resource.py and resource_container.py

Issues with specification
=========================

- v1.0 spec Figure 4 shows Capability List indexes but these are not allowed per section 9
