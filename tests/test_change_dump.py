import unittest
try: #python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError: #python3
    import io
import re

from resync.resource import Resource
from resync.change_dump import ChangeDump
from resync.sitemap import SitemapParseError

class TestChangeDump(unittest.TestCase):

    def test01_as_xml(self):
        rd = ChangeDump()
        rd.add( Resource('a.zip',timestamp=1) )
        rd.add( Resource('b.zip',timestamp=2) )
        xml = rd.as_xml()
        #print(xml)
        self.assertTrue( re.search(r'<rs:md .*capability="changedump"', xml), 'XML has capability' )
        self.assertTrue( re.search(r'<url><loc>a.zip</loc><lastmod>1970-01-01T00:00:01Z</lastmod></url>', xml), 'XML has resource a' ) 

    def test10_parse(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="changedump" from="2013-01-01"/>\
<url><loc>http://example.com/a.zip</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12345" /></url>\
<url><loc>http://example.com/b.zip</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="56789" /></url>\
</urlset>'
        rd=ChangeDump()
        rd.parse(fh=io.StringIO(xml))
        self.assertEqual( len(rd.resources), 2, 'got 2 resource dumps')
        self.assertEqual( rd.md['capability'], 'changedump', 'capability set' )
        self.assertEqual( rd.md_from, '2013-01-01' )
        self.assertTrue( 'http://example.com/a.zip' in rd.resources )
        self.assertTrue( rd.resources['http://example.com/a.zip'].length, 12345 )
        self.assertTrue( 'http://example.com/b.zip' in rd.resources )
        self.assertTrue( rd.resources['http://example.com/b.zip'].length, 56789 )

    def test11_parse_no_capability(self):
        # For a resource dump this should be an error
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md at="2013-01-01"/>\
<url><loc>http://example.com/a.zip</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" /></url>\
</urlset>'
        rd=ChangeDump()
        self.assertRaises( SitemapParseError, rd.parse, fh=io.StringIO(xml) )

    def test12_parse_bad_capability(self):
        # the <rs:md capability="bad_capability".. should give error
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="bad_capability" from="2013-01-01"/>\
<url><loc>http://example.com/bad_res_1</loc><lastmod>2012-03-14T18:37:36Z</lastmod></url>\
</urlset>'
        rd=ChangeDump()
        self.assertRaises( SitemapParseError, rd.parse, fh=io.StringIO(xml) )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestChangeDump)
    unittest.TextTestRunner().run(suite)
