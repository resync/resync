import unittest
import StringIO
import re
from resync.resource import Resource
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.sitemap import SitemapParseError

class TestResourceDumpManifest(unittest.TestCase):

    def test01_as_xml(self):
        rdm = ResourceDumpManifest()
        rdm.add( Resource('a.zip',timestamp=1) )
        rdm.add( Resource('b.zip',timestamp=2) )
        xml = rdm.as_xml()
        print xml
        self.assertTrue( re.search(r'<rs:md .*capability="resourcedump-manifest"', xml), 'XML has capability' )
        self.assertTrue( re.search(r'<rs:md .*modified="\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\dZ"', xml), 'XML has modified to seconds precision (and not more)' )
        self.assertTrue( re.search(r'<url><loc>a.zip</loc><lastmod>1970-01-01T00:00:01Z</lastmod></url>', xml), 'XML has resource a' ) 

    def test10_parse(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="resourcedump-manifest" modified="2013-01-01"/>\
<url><loc>http://example.com/res1</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" path="/res1" /></url>\
<url><loc>http://example.com/res2</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" path="/res2"/></url>\
</urlset>'
        rdm=ResourceDumpManifest()
        rdm.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(rdm.resources), 2, 'got 2 resource dumps')
        self.assertEqual( rdm.md['capability'], 'resourcedump-manifest', 'capability set' )
        self.assertEqual( rdm.md['modified'], '2013-01-01' )
        self.assertTrue( 'http://example.com/res1' in rdm.resources )
        self.assertTrue( rdm.resources['http://example.com/res1'].length, 12 )
        self.assertTrue( rdm.resources['http://example.com/res1'].path, '/res1' )
        self.assertTrue( 'http://example.com/res2' in rdm.resources )
        self.assertTrue( rdm.resources['http://example.com/res2'].path, '/res2' )

    def test11_parse_no_capability(self):
        # For a resource dump this should be an error
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md modified="2013-01-01"/>\
<url><loc>http://example.com/res1</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" path="/res1" /></url>\
<url><loc>http://example.com/res2</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" path="/res2"/></url>\
</urlset>'
        rdm=ResourceDumpManifest()
        self.assertRaises( SitemapParseError, rdm.parse, fh=StringIO.StringIO(xml) )

    def test12_parse_bad_capability(self):
        # the <rs:md capability="bad_capability".. should give error
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="bad_capability" modified="2013-01-01"/>\
<url><loc>http://example.com/a.zip</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" /></url>\
</urlset>'
        rdm=ResourceDumpManifest()
        self.assertRaises( SitemapParseError, rdm.parse, fh=StringIO.StringIO(xml) )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceDumpManifest)
    unittest.TextTestRunner().run(suite)
