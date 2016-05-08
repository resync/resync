import unittest
import re
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.resource_set import ResourceSetDupeError
from resync.change_list import ChangeList
from resync.capability_list import CapabilityList


class TestCapabilityList(unittest.TestCase):

    def test01_add(self):
        # one
        caps = CapabilityList()
        r1 = Resource(uri='http://example.org/r1')
        caps.add(r1)
        self.assertEqual(len(caps), 1)
        # dupe
        self.assertRaises(ResourceSetDupeError, caps.add, r1)
        self.assertEqual(len(caps), 1)
        # dupe with replace
        caps = CapabilityList()
        caps.add([r1, r1], replace=True)
        self.assertEqual(len(caps), 1)
        # diff
        caps = CapabilityList()
        r2 = ChangeList(uri='http://example.org/r2')
        caps.add([r1, r2])
        self.assertEqual(len(caps), 2)

    def test02_resourcelist(self):
        rl = ResourceList()
        caps = CapabilityList()
        caps.add_capability(rl, "http://example.org/resourcelist.xml")
        caps.md['from'] = "2013-02-07T22:39:00"
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="capabilitylist" from="2013-02-07T22:39:00" /><url><loc>http://example.org/resourcelist.xml</loc><rs:md capability="resourcelist" /></url></urlset>')

    def test03_multiple(self):
        caps = CapabilityList()
        rl = ResourceList()
        caps.add_capability(rl, "rl.xml")
        cl = ChangeList()
        caps.add_capability(cl, "cl.xml")
        self.assertEqual(len(caps), 2)
        xml = caps.as_xml()
        self.assertTrue(
            re.search(r'<loc>rl.xml</loc><rs:md capability="resourcelist" />', xml))
        self.assertTrue(
            re.search(r'<loc>cl.xml</loc><rs:md capability="changelist" />', xml))

    def test04_parse(self):
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="capabilitylist" from="2013-02-07T22:39:00" /><url><loc>http://example.org/resourcelist.xml</loc><rs:md capability="resourcelist" /></url></urlset>'
        cl = CapabilityList()
        cl.parse(str_data=xml)
        self.assertEqual(cl.capability, 'capabilitylist')
        self.assertEqual(len(cl.resources), 1, 'got 1 resource')
        [r] = cl.resources
        self.assertEqual(
            r.uri, 'http://example.org/resourcelist.xml', 'resourcelist uri')
        self.assertEqual(r.capability, 'resourcelist')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestCapabilityList)
    unittest.TextTestRunner().run(suite)
