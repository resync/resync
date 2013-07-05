#!/usr/bin/env python
if (True): #keep indentation of README

    from resync import CapabilityList

    # Read Capability List and show supported capabilities
    cl = CapabilityList()
    cl.read("https://raw.github.com/resync/resync/0.6/resync/test/testdata/examples_from_spec/resourcesync_ex_2_6.xml")
    for resource in cl:
        print "supports %s (at %s)" % (resource.capability,resource.uri)

