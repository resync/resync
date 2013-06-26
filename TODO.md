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

- this is one of three examples (2.7, 9.1, 9.2) that give a content type for the  <rs:ln rel="describedby" .../>. The rel="describedby" link in example 2.6 does not have a type attribute. Should we either be consistent and use that always, or is a mix better?

Example 2.8
-----------

- we have  part2 before part1. In other documents we write them so that the are read in a forward/chronological direction, this seems backwards and I would change it to have part1 and then part2.

Section 2.2.3 
-------------

- In figure 3 I don't think we should have a Capability List Index, see comments on section 9.2. 

Section 3
---------

- The description of top-level <rs:ln ... /> says "It can have several attributes and the ones defined in the ResourceSync XML Namespace are as follows:" ... and then describes just the rel and href attributes. The examples 2.7, 9.1 and 9.2 also use the type attribute which should presumably be added to this list. I would also change the description to be more specific about attributes, perhaps: "Three attributes are defined in the ResourceSync XML Namespace and are listed below, other attributes may also be used:"

- Typo in "resourcesync - for linking from a Capability List to the ResourceSync Description and from a document that conveys a capability, such as a Resource List, to the Capability List it resorts under." should do s/it resorts under/that lists the capability/.

Section 9.2
-----------

- I don't think we should suggest that a sitemapindex is allowed for a capability list. So far we have defined 8 capabilities which I think gives plenty of headroom (another 49,992 capabilities) before we are in danger of overflowing the <urlset>. I propose replacing "If a Source needs to or chooses to publish and group multiple Capability Lists, one for each set of resources, it needs to establish a Capability List Index, in a manner similar to what was described in Section 4.2." with "The small number of possible capabilities that may be provided for any set of resources means that a Source will never need to split a Capability List into multiple parts, and thus no Capability List Index is defined."
