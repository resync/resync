#!/usr/bin/env python

from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.list_base_with_index import ListBaseIndexError
import sys

try:
    max_sitemap_entries = int(sys.argv[1])
except:
    max_sitemap_entries = 2
print "### max_sitemap_entries=%d" % max_sitemap_entries
basename = 'http://example.com/resourcelist.xml'
my_resources = [ Resource('a'), Resource('b'), Resource('c') ]

def my_resource_list():
    """Simulate the generator used by simulator"""
    rl = ResourceList( resources=iter(my_resources), count=len(my_resources) )
    rl.max_sitemap_entries = max_sitemap_entries
    return(rl)

print "\n### ResourceListHandler"
rl = my_resource_list()
if (rl.requires_multifile):
   print "Single sitemap:"
else:
   print "Sitemapindex:"
print rl.as_xml( allow_multifile=True, basename=basename )


print "\n### ResourceListPartHandler"
rl = my_resource_list()
num_parts=rl.requires_multifile()
if (num_parts):
    for part_number in range(0,num_parts):
        rl = my_resource_list()
        print "Part %d:" % (part_number)
        print rl.as_xml_part( basename=basename, part_number=0 )
else:
    print "404 - no parts"

