To do list for resync client and library
========================================

See also issues on github tracker. Other big threads that need attention are:

- add creation of ResourceSync Description document
- work through and test creation of Resource and Change Dump ZIPs
- add use of a Resource and Change Dump ZIPs
- ...

Questions about ResourceSync v0.9 spec
======================================

Example 2.7
-----------

- this is the only example that gives a content type for the  <rs:ln rel="describedby" .../>. Should we either be consistent with that or maybe drop it here too?

- I am not sure the rel="describedby" within the <url> block for the capability list has the correct meaning. Doesn't it mean in that context that the capability list if descibedby the giev resource? That seems not quite the same as our usual interpretation of top level rel="describedby" which we take to be a description of the set of resources rather than the capability document.

Section 9.2
-----------

- I don't think we should suggest that a sitemapindex is allowed for a capability list. So far we have defined 8 capabilities which I think gives plenty of headroom (another 49,992 capabilities) before we are in danger of overflowing the <urlset>. I would add language like that in section 9.1 saying it must be a <urlset> doc.