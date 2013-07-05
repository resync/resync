#!/usr/bin/env python
if (True): #keep indentation of README

    from resync import Resource,ResourceList

    rl = ResourceList()
    rl.add( Resource('http://example.com/res1', lastmod='2013-01-01') )
    rl.add( Resource('http://example.com/res2', lastmod='2013-01-02') )
    print rl.as_xml()
