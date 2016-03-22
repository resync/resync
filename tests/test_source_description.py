import unittest
import re
from resync.resource import Resource
from resync.source_description import SourceDescription

class TestSourceDescription(unittest.TestCase):

    def test01_empty(self):
        rsd = SourceDescription()
        rsd.describedby = "http://example.org/about"
        self.assertEqual( len(rsd), 0 )
        rsd.md_at = None
        self.assertEqual( rsd.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:ln href="http://example.org/about" rel="describedby" /><rs:md capability="description" /></urlset>' )

    def test02_one_caplist(self):
        rsd = SourceDescription()
        rsd.describedby = "http://example.org/about"
        self.assertEqual( len(rsd), 0 )
        rsd.md_at = None
        rsd.add_capability_list("http://example.org/ds1/cl.xml")
        self.assertEqual( len(rsd), 1 )
        self.assertEqual( rsd.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:ln href="http://example.org/about" rel="describedby" /><rs:md capability="description" /><url><loc>http://example.org/ds1/cl.xml</loc><rs:md capability="capabilitylist" /></url></urlset>' )

    def test03_a_bunch(self):
        rsd = SourceDescription()
        rsd.describedby = "http://example.org/about"
        self.assertEqual( len(rsd), 0 )
        rsd.add_capability_list("http://example.org/ds1/cl.xml")
        rsd.add_capability_list("http://example.org/ds2/cl.xml")
        rsd.add_capability_list("http://example.org/ds3/cl.xml")
        self.assertEqual( len(rsd), 3 )
        self.assertEqual( rsd.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:ln href="http://example.org/about" rel="describedby" /><rs:md capability="description" /><url><loc>http://example.org/ds1/cl.xml</loc><rs:md capability="capabilitylist" /></url><url><loc>http://example.org/ds2/cl.xml</loc><rs:md capability="capabilitylist" /></url><url><loc>http://example.org/ds3/cl.xml</loc><rs:md capability="capabilitylist" /></url></urlset>' )

    def test04_parse(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:ln href="http://example.org/about" rel="describedby" /><rs:md capability="description" /><url><loc>http://example.org/ds1/cl.xml</loc><rs:md capability="capabilitylist" /></url><url><loc>http://example.org/ds2/cl.xml</loc><rs:md capability="capabilitylist" /></url><url><loc>http://example.org/ds3/cl.xml</loc><rs:md capability="capabilitylist" /></url></urlset>'
        sd=SourceDescription()
        sd.parse(str_data=xml)
        self.assertEqual( sd.link_href('describedby'), 'http://example.org/about', 
                          'describedby link' )
        self.assertEqual( sd.capability, 'description' )
        self.assertEqual( len(sd.resources), 3, 'got 3 capacility lists' )
        [r1,r2,r3]=sd.resources
        self.assertEqual( r1.uri, 'http://example.org/ds1/cl.xml' )
        self.assertEqual( r1.capability, 'capabilitylist' )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSourceDescription)
    unittest.TextTestRunner().run(suite)
