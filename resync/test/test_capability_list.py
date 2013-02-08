import unittest
import re
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.capability_list import CapabilityList, CapabilityListDupeError

class TestCapabilityList(unittest.TestCase):

    def test01_resourcelist(self):
        rl = ResourceList()
        caps = CapabilityList()
        caps.add_capability( rl, "http://example.org/resourcelist.xml" )
        caps.md['modified'] = "2013-02-07T22:39:00"
        self.assertEqual( len(caps), 1 )
        self.assertEqual( caps.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="capabilitylist" modified="2013-02-07T22:39:00" /><url><loc>http://example.org/resourcelist.xml</loc><rs:md capability="resourcelist" /></url></urlset>' )

    def test02_multiple(self):
        caps = CapabilityList()
        rl = ResourceList()
        caps.add_capability( rl, "rl.xml" )
        cl = ChangeList()
        caps.add_capability( cl, "cl.xml" )
        self.assertEqual( len(caps), 2 )
        xml = caps.as_xml()
        self.assertTrue( re.search( r'<loc>rl.xml</loc><rs:md capability="resourcelist" />', xml ) )
        self.assertTrue( re.search( r'<loc>cl.xml</loc><rs:md capability="changelist" />', xml) )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCapabilityList)
    unittest.TextTestRunner().run(suite)
