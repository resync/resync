import unittest
import re
from resync.resource import Resource
from resync.resourcesync_description import ResourceSyncDescription

class TestResourceSyncDescription(unittest.TestCase):

    def test01_empty(self):
        rsd = ResourceSyncDescription()
        rsd.describedby = "http://example.org/about"
        self.assertEqual( len(rsd), 0 )
        rsd.md_from = None
        self.assertEqual( rsd.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:ln href="http://example.org/about" rel="describedby" /><rs:md capability="resourcesync" /></urlset>' )

    def test02_one_caplist(self):
        rsd = ResourceSyncDescription()
        rsd.describedby = "http://example.org/about"
        self.assertEqual( len(rsd), 0 )
        rsd.md_from = None
        rsd.add_capability_list("http://example.org/ds1/cl.xml")
        self.assertEqual( rsd.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:ln href="http://example.org/about" rel="describedby" /><rs:md capability="resourcesync" /><url><loc>http://example.org/ds1/cl.xml</loc><rs:md capability="capabilitylist" /></url></urlset>' )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceSyncDescription)
    unittest.TextTestRunner().run(suite)
