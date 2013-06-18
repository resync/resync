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

- this is one of three examples (2.7, 9.1, 9.2) that give a content type for the  <rs:ln rel="describedby" .../>. Example 2.6 does not have a type attribute. Should we either be consistent and use that always, or is a mix better?

- I am not sure the rel="describedby" within the <url> block for the capability list has the correct meaning. Doesn't it mean in that context that the capability list if descibedby the giev resource? That seems not quite the same as our usual interpretation of top level rel="describedby" which we take to be a description of the set of resources rather than the capability document.

Example 2.8
-----------

- why is part2 before part1? In other documents we write them so that the are read in a forward/chronological direction, this seems backwards.

Section 3
---------

- The description of top-level <rs:ln ... /> says "It can have several attributes and the ones defined in the ResourceSync XML Namespace are as follows:" ... and then describes just the rel and href attributes. The examples 2.7, 9.1 and 9.2 also use the type attribute which should presumably be added to this list. I would also change the description to be more specific about attributes, perhaps: "Three attributes are defined in the ResourceSync XML Namespace and are listed below, other attributes may also be used:"

Section 9.2
-----------

- I don't think we should suggest that a sitemapindex is allowed for a capability list. So far we have defined 8 capabilities which I think gives plenty of headroom (another 49,992 capabilities) before we are in danger of overflowing the <urlset>. I would add language like that in section 9.1 saying it must be a <urlset> doc.