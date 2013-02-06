import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.sitemap import Sitemap, SitemapIndexError

# etree gives ParseError in 2.7, ExpatError in 2.6
etree_error_class = None
if (sys.version_info < (2,7)):
    from xml.parsers.expat import ExpatError
    etree_error_class = ExpatError
else:
    from xml.etree.ElementTree import ParseError
    etree_error_class = ParseError

class TestSitemap(unittest.TestCase):

    def test_01_resource_str(self):
        r1 = Resource('a3')
        r1.lastmod='2012-01-11T01:02:03Z'
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>a3</loc><lastmod>2012-01-11T01:02:03Z</lastmod></url>" )

    def test_02_resource_str(self):
        r1 = Resource('3b',1234.1,9999,'ab54de')
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>3b</loc><lastmod>1970-01-01T00:20:34.100000Z</lastmod><rs:md hash=\"md5:ab54de\" size=\"9999\" /></url>" )

    def test_08_print(self):
        r1 = Resource(uri='a',lastmod='2001-01-01',size=1234)
        r2 = Resource(uri='b',lastmod='2002-02-02',size=56789)
        r3 = Resource(uri='c',lastmod='2003-03-03',size=0)
        m = ResourceList()
        m.add(r1)
        m.add(r2)
        m.add(r3)
        #print m
        self.assertEqual( Sitemap().resources_as_xml(m), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md size=\"1234\" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md size=\"56789\" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md size=\"0\" /></url></urlset>")

    def test_09_print_subset(self): 
        r1 = Resource(uri='a',lastmod='2001-01-01',size=1234)
        r2 = Resource(uri='b',lastmod='2002-02-02',size=56789)
        r3 = Resource(uri='d',lastmod='2003-03-04',size=444)
        m = ResourceList()
        m.add(r1)
        m.add(r2)
        m.add(r3)
        self.assertEqual( Sitemap().resources_as_xml(m, num_resources=2), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md size=\"1234\" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md size=\"56789\" /></url></urlset>")

    def test_09s_print_from_iter(self): 
        r1 = Resource(uri='a',lastmod='2001-01-01',size=1234)
        r2 = Resource(uri='b',lastmod='2002-02-02',size=56789)
        r3 = Resource(uri='c',lastmod='2003-03-03',size=0)
        r4 = Resource(uri='d',lastmod='2004-04-04',size=444)
        m = ResourceList()
        m.add(r1)
        m.add(r2)
        m.add(r3)
        m.add(r4)
        i = iter(m)
        self.assertEqual( Sitemap().resources_as_xml(i, num_resources=2), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md size=\"1234\" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md size=\"56789\" /></url></urlset>")
        self.assertEqual( Sitemap().resources_as_xml(i, num_resources=1), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md size=\"0\" /></url></urlset>")
        self.assertEqual( Sitemap().resources_as_xml(i), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><url><loc>d</loc><lastmod>2004-04-04T00:00:00Z</lastmod><rs:md size=\"444\" /></url></urlset>")

    def test_10_sitemap(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>http://e.com/a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md hash="md5:Q2hlY2sgSW50ZWdyaXR5IQ==" size=\"12\" /></url>\
</urlset>'
        s=Sitemap()
        i=s.sitemap_parse_xml(fh=StringIO.StringIO(xml))
        self.assertEqual( s.resources_created, 1, 'got 1 resources')
        for r in i.resources:
            self.assertTrue( r is not None, 'got the uri expected')
            self.assertEqual( r.uri, 'http://e.com/a' )
            self.assertEqual( r.lastmod, '2012-03-14T18:37:36Z' )
            self.assertEqual( r.size, 12 )
            self.assertEqual( r.md5, 'Q2hlY2sgSW50ZWdyaXR5IQ==' )

    def test_11_parse_2(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md size=\"12\" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md size=\"32\" /></url>\
</urlset>'
        s=Sitemap()
        i=s.sitemap_parse_xml(fh=StringIO.StringIO(xml))
        self.assertEqual( s.resources_created, 2, 'got 2 resources')

    def test_13_parse_illformed(self):
        s=Sitemap()
        # ExpatError in python2.6, ParserError in 2.7
        self.assertRaises( etree_error_class, s.sitemap_parse_xml, StringIO.StringIO('not xml') )
        self.assertRaises( etree_error_class, s.sitemap_parse_xml, StringIO.StringIO('<urlset><url>something</urlset>') )

    def test_13_parse_valid_xml_but_other(self):
        s=Sitemap()
        self.assertRaises( ValueError, s.sitemap_parse_xml, StringIO.StringIO('<urlset xmlns="http://example.org/other_namespace"> </urlset>') )
        self.assertRaises( ValueError, s.sitemap_parse_xml, StringIO.StringIO('<other xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> </other>') )

    def test_14_parse_sitemapindex_as_sitemap(self):
        s=Sitemap()
        self.assertRaises( SitemapIndexError, s.sitemap_parse_xml, StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> </sitemapindex>') )

    def test_20_parse_sitemapindex_empty(self):
        s=Sitemap()
        si = s.sitemapindex_parse_xml( fh=StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> </sitemapindex>') )
        self.assertEqual( s.sitemaps_created, 0, '0 sitemaps in sitemapindex')
        self.assertEqual( len(si.resources), 0, '0 sitemaps')

    def test_21_parse_sitemapindex(self):
        s=Sitemap()
        si = s.sitemapindex_parse_xml( fh=StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>aaa</loc></sitemap><sitemap><loc>bbb</loc></sitemap></sitemapindex>') )
        self.assertEqual( s.sitemaps_created, 2, '2 sitemaps in sitemapindex')
        self.assertEqual( len(si.resources), 2, '2 sitemaps')
        sms = sorted(si.uris())
        self.assertEqual( sms, ['aaa','bbb'] )
        # add a couple more
        s.sitemapindex_parse_xml( fh=StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>cc</loc></sitemap><sitemap><loc>dd</loc></sitemap></sitemapindex>'), sitemapindex=si )
        self.assertEqual( s.sitemaps_created, 2, '2 sitemaps created to sitemapindex')
        self.assertEqual( len(si.resources), 4, '4 sitemaps total')
        sms = sorted(si.uris())
        self.assertEqual( sms, ['aaa','bbb', 'cc', 'dd'] )

    def test_22_parse_sitemapindex_file(self):
        s=Sitemap()
        fh=open('resync/test/testdata/sitemapindex1/sitemap.xml')
        si = s.sitemapindex_parse_xml( fh=fh )
        self.assertEqual( s.sitemaps_created, 3, '3 sitemaps in sitemapindex')
        self.assertEqual( len(si.resources), 3, '3 sitemaps')
        sms = sorted(si.uris())
        self.assertEqual( sms, ['http://localhost:8888/sitemap00000.xml','http://localhost:8888/sitemap00001.xml','http://localhost:8888/sitemap00002.xml'] )
        #self.assertEqual( si.resources['http://localhost:8888/sitemap00000.xml'].lastmod, '2012-06-13T18:09:13Z' )

    def test_21_parse_multi_sitemapindex(self):
        i = Sitemap().read( uri='resync/test/testdata/sitemapindex2/sitemap.xml' )
        self.assertEqual( len(i.resources), 17, '17 resources from 3 sitemaps')
        sr = sorted(i.uris())
        self.assertEqual( sr[0], 'http://localhost:8888/resources/1' )
        self.assertEqual( sr[1], 'http://localhost:8888/resources/10' )
        self.assertEqual( sr[2], 'http://localhost:8888/resources/100' )
        self.assertEqual( sr[3], 'http://localhost:8888/resources/1000' )
        self.assertEqual( sr[16], 'http://localhost:8888/resources/826' )

    def test_30_parse_change_list(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="updated" size="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md size="32" /></url>\
</urlset>'
        s=Sitemap()
        s.resource_class=Resource
        c=s.sitemap_parse_xml(fh=StringIO.StringIO(xml))
        self.assertEqual( s.resources_created, 2, 'got 2 resources')
        i = iter(c)
        r1 = i.next()
        self.assertEqual( r1.uri, '/tmp/rs_test/src/file_a' )
        self.assertEqual( r1.change, 'updated' )
        r2 = i.next()
        self.assertEqual( r2.uri, '/tmp/rs_test/src/file_b' )
        self.assertEqual( r2.change, None )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSitemap)
    unittest.TextTestRunner(verbosity=2).run(suite)
