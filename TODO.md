To do list for resync client and library
========================================

See also issues on github tracker. Other big threads that need attention are:

  * work through and test creation of Resource and Change Dump ZIPs
  * add use of a Resource and Change Dump ZIPs
  * add archives (ResoourceListArchive, ChangeListArchive, ResourceDumpArchive, ChangeDumpArchive)
  * consider breaking out handling of links that is somewhat duplicated in resource.py and resource_container.py

Planned changes and deprecation
-------------------------------

  * Remove support for ListBase.parse(str=...) which was deprecated in favor of ListBase.parse(str_data=...) 2016-03-22 in 1.0.1
