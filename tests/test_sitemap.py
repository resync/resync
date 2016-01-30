import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.sitemap import Sitemap, SitemapIndexError, SitemapParseError

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
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>3b</loc><lastmod>1970-01-01T00:20:34.100000Z</lastmod><rs:md hash=\"md5:ab54de\" length=\"9999\" /></url>" )

    def test_03_resource_str_hashes(self):
        r1 = Resource('03hashes',1234.1)
        r1.md5 = 'aaa'
        r1.sha1 = 'bbb'
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>03hashes</loc><lastmod>1970-01-01T00:20:34.100000Z</lastmod><rs:md hash=\"md5:aaa sha-1:bbb\" /></url>" )
        r1.sha256 = 'ccc'
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>03hashes</loc><lastmod>1970-01-01T00:20:34.100000Z</lastmod><rs:md hash=\"md5:aaa sha-1:bbb sha-256:ccc\" /></url>" )
        r1.sha1 = None
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>03hashes</loc><lastmod>1970-01-01T00:20:34.100000Z</lastmod><rs:md hash=\"md5:aaa sha-256:ccc\" /></url>" )

    def test_04_resource_str(self):
        r1 = Resource(uri='4a',lastmod="2013-01-02",length=9999,md5='ab54de')
        r1.ln = [{ 'rel':'duplicate',
                   'pri':'1',
                   'href':'http://mirror1.example.com/res1',
                   'modified':'2013-01-02T18:00:00Z' }]
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>4a</loc><lastmod>2013-01-02T00:00:00Z</lastmod><rs:md hash=\"md5:ab54de\" length=\"9999\" /><rs:ln href=\"http://mirror1.example.com/res1\" modified=\"2013-01-02T18:00:00Z\" pri=\"1\" rel=\"duplicate\" /></url>" )
        # add another two rs:ln's
        r1.ln.append( { 'rel':'num2' } )
        r1.ln.append( { 'rel':'num3' } )
        self.assertEqual( Sitemap().resource_as_xml(r1), "<?xml version='1.0' encoding='UTF-8'?>\n<url><loc>4a</loc><lastmod>2013-01-02T00:00:00Z</lastmod><rs:md hash=\"md5:ab54de\" length=\"9999\" /><rs:ln href=\"http://mirror1.example.com/res1\" modified=\"2013-01-02T18:00:00Z\" pri=\"1\" rel=\"duplicate\" /><rs:ln rel=\"num2\" /><rs:ln rel=\"num3\" /></url>" )

    def test_08_print(self):
        r1 = Resource(uri='a',lastmod='2001-01-01',length=1234)
        r2 = Resource(uri='b',lastmod='2002-02-02',length=56789)
        r3 = Resource(uri='c',lastmod='2003-03-03',length=0)
        m = ResourceList(md={'capability':'resourcelist','modified':None})
        m.add(r1)
        m.add(r2)
        m.add(r3)
        #print m
        self.assertEqual( Sitemap().resources_as_xml(m), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><rs:md capability=\"resourcelist\" /><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length=\"1234\" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length=\"56789\" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md length=\"0\" /></url></urlset>")

    def test_09_print_from_iter(self): 
        r1 = Resource(uri='a',lastmod='2001-01-01',length=1234)
        r2 = Resource(uri='b',lastmod='2002-02-02',length=56789)
        m = ResourceList()
        m.add(r1)
        m.add(r2)
        i = iter(m)
        self.assertEqual( Sitemap().resources_as_xml(i), "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:rs=\"http://www.openarchives.org/rs/terms/\"><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length=\"1234\" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length=\"56789\" /></url></urlset>")

    def test_10_sitemap(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>http://e.com/a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md hash="md5:Q2hlY2sgSW50ZWdyaXR5IQ==" length=\"12\" /></url>\
</urlset>'
        s=Sitemap()
        i=s.parse_xml(fh=StringIO.StringIO(xml))
        self.assertFalse( s.parsed_index, 'was a sitemap')
        self.assertEqual( s.resources_created, 1, 'got 1 resources')
        for r in i.resources:
            self.assertTrue( r is not None, 'got the uri expected')
            self.assertEqual( r.uri, 'http://e.com/a' )
            self.assertEqual( r.lastmod, '2012-03-14T18:37:36Z' )
            self.assertEqual( r.length, 12 )
            self.assertEqual( r.md5, 'Q2hlY2sgSW50ZWdyaXR5IQ==' )

    def test_11_parse_2(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length=\"12\" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length=\"32\" /></url>\
</urlset>'
        s=Sitemap()
        i=s.parse_xml(fh=StringIO.StringIO(xml))
        self.assertFalse( s.parsed_index, 'was a sitemap')
        self.assertEqual( s.resources_created, 2, 'got 2 resources')

    def test_12_parse_multi_loc(self):
        xml_start='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url>'
        xml_end='<lastmod>2012-03-14T18:37:36Z</lastmod></url></urlset>'
        s=Sitemap()
        two_loc='<loc>/tmp/rs_test/src/file_a</loc><loc>/tmp/rs_test/src/file_b</loc>'
        self.assertRaises( SitemapParseError, s.parse_xml, 
                           StringIO.StringIO(xml_start+two_loc+xml_end))
        mt_loc='<loc></loc>'
        self.assertRaises( SitemapParseError, s.parse_xml, 
                           StringIO.StringIO(xml_start+mt_loc+xml_end))
        mt_loc_att='<loc att="value"/>'
        self.assertRaises( SitemapParseError, s.parse_xml, 
                           StringIO.StringIO(xml_start+mt_loc_att+xml_end))

    def test_13_parse_multi_lastmod(self):
        xml_start='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>uri:a</loc>'
        xml_end='</url></urlset>'
        s=Sitemap()
        two_lastmod='<lastmod>2013-01-01</lastmod><lastmod>2013-01-02</lastmod>'
        self.assertRaises( SitemapParseError, s.parse_xml, 
                           StringIO.StringIO(xml_start+two_lastmod+xml_end))
        # While it not ideal to omit, <lastmod> is not required and
        # thus either empty lastmod or lastmod with just an attribute
        # and no content are not ambiguous and thus should be accepted
        # with resulting None for resource.lastmod
        mt_lastmod='<lastmod></lastmod>'
        i=s.parse_xml(fh=StringIO.StringIO(xml_start+mt_lastmod+xml_end))
        self.assertEqual( s.resources_created, 1 )
        self.assertEqual( i.resources[0].lastmod, None )
        mt_lastmod_att='<lastmod att="value"/>'
        i=s.parse_xml(fh=StringIO.StringIO(xml_start+mt_lastmod_att+xml_end))
        self.assertEqual( s.resources_created, 1 )
        self.assertEqual( i.resources[0].lastmod, None )

    def test_14_parse_multi(self):
        xml_start='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">'
        xml_end='<url><loc>uri:a</loc></url></urlset>'
        s=Sitemap()
        two_md='<rs:md capability="resourcelist"/><rs:md capability="resourcelist"/>'
        self.assertRaises( SitemapParseError, s.parse_xml, 
                           StringIO.StringIO(xml_start+two_md+xml_end))

    def test_15_parse_illformed(self):
        s=Sitemap()
        # ExpatError in python2.6, ParserError in 2.7
        self.assertRaises( etree_error_class, s.parse_xml, StringIO.StringIO('not xml') )
        self.assertRaises( etree_error_class, s.parse_xml, StringIO.StringIO('<urlset><url>something</urlset>') )

    def test_16_parse_valid_xml_but_other(self):
        s=Sitemap()
        self.assertRaises( SitemapParseError, s.parse_xml, StringIO.StringIO('<urlset xmlns="http://example.org/other_namespace"> </urlset>') )
        self.assertRaises( SitemapParseError, s.parse_xml, StringIO.StringIO('<other xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> </other>') )

    def test_17_parse_sitemapindex_as_sitemap(self):
        s=Sitemap()
        self.assertRaises( SitemapIndexError, s.parse_xml, StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> </sitemapindex>'), sitemapindex=False )

    def test_18_parse_with_rs_ln_on_resource(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability=\"resourcelist\"/>\
<url>\
  <loc>http://example.com/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod>\
  <rs:md hash=\"md5:r2d2\" length=\"12345\" />\
  <rs:ln rel=\"duplicate\" href=\"http://mirror1.example.com/res1\" modified=\"2013-01-02\" pri=\"1\" />\
  <rs:ln rel=\"num2\" href=\"http://m2.example.com/res1\"/>\
  <rs:ln rel=\"num3\" href=\"http://m3.example.com/res1\"/>\
</url>\
<url>\
  <loc>http://example.com/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod>\
  <rs:md length=\"32\" />\
</url>\
</urlset>'
        s=Sitemap()
        rc=s.parse_xml(fh=StringIO.StringIO(xml))
        self.assertFalse( s.parsed_index, 'was a sitemap')
        self.assertEqual( s.resources_created, 2, 'got 2 resources')
        i = iter(rc)
        r1 = i.next()
        r2 = i.next()
        self.assertEqual( r1.uri, 'http://example.com/file_a' )
        self.assertEqual( r1.ln[0]['rel'], 'duplicate' )
        self.assertEqual( r1.ln[0]['href'], 'http://mirror1.example.com/res1' )
        self.assertEqual( r1.ln[0]['modified'], '2013-01-02' )
        self.assertEqual( r1.ln[0]['pri'], 1 )
        self.assertEqual( r2.uri, 'http://example.com/file_b' )

    def test_19_parse_with_bad_rs_ln(self):
        xmlstart='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="resourcelist"/>\
<url><loc>http://example.com/file_a</loc>'
        xmlend='</url></urlset>'
        s=Sitemap()
        #
        # missing href
        xml=xmlstart+'<rs:ln rel="duplicate"/>'+xmlend
        self.assertRaises( SitemapParseError, s.parse_xml, fh=StringIO.StringIO(xml))
        # missing rel
        xml=xmlstart+'<rs:ln href="http://example.com/"/>'+xmlend
        self.assertRaises( SitemapParseError, s.parse_xml, fh=StringIO.StringIO(xml))
        # bad length
        xml=xmlstart+'<rs:ln rel="duplicate" href="http://example.com/" length="a"/>'+xmlend
        self.assertRaises( SitemapParseError, s.parse_xml, fh=StringIO.StringIO(xml))
        # bad pri
        xml=xmlstart+'<rs:ln rel="duplicate" href="http://example.com/" pri="fff"/>'+xmlend
        self.assertRaises( SitemapParseError, s.parse_xml, fh=StringIO.StringIO(xml))
        xml=xmlstart+'<rs:ln rel="duplicate" href="http://example.com/" pri="0"/>'+xmlend
        self.assertRaises( SitemapParseError, s.parse_xml, fh=StringIO.StringIO(xml))
        xml=xmlstart+'<rs:ln rel="duplicate" href="http://example.com/" pri="1000000"/>'+xmlend
        self.assertRaises( SitemapParseError, s.parse_xml, fh=StringIO.StringIO(xml))
        # and finally OK with errors fixes
        xml=xmlstart+'<rs:ln rel="duplicate" href="http://example.com/" length="12345" pri="1" other="whatever"/>'+xmlend
        rc = s.parse_xml(fh=StringIO.StringIO(xml))
        self.assertEqual( len(rc.resources), 1, 'good at last, extra attribute ignored' )

    def test_20_parse_sitemapindex_empty(self):
        s=Sitemap()
        si = s.parse_xml( fh=StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> </sitemapindex>'), sitemapindex=True )
        self.assertTrue( s.parsed_index, 'was a sitemapindex')
        self.assertEqual( len(si.resources), 0, '0 sitemaps')

    def test_21_parse_sitemapindex(self):
        s=Sitemap()
        si = s.parse_xml( fh=StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>aaa</loc></sitemap><sitemap><loc>bbb</loc></sitemap></sitemapindex>'), sitemapindex=True )
        self.assertEqual( len(si.resources), 2, '2 sitemaps')
        sms = sorted(si.uris())
        self.assertEqual( sms, ['aaa','bbb'] )
        # add a couple more
        s.parse_xml( fh=StringIO.StringIO('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>cc</loc></sitemap><sitemap><loc>dd</loc></sitemap></sitemapindex>'), resources=si )
        self.assertTrue( s.parsed_index, 'was a sitemapindex')
        self.assertEqual( len(si.resources), 4, '4 sitemaps total')
        sms = sorted(si.uris())
        self.assertEqual( sms, ['aaa','bbb', 'cc', 'dd'] )

    def test_22_parse_sitemapindex_file(self):
        s=Sitemap()
        fh=open('tests/testdata/sitemapindex1/sitemap.xml','r')
        si = s.parse_xml( fh=fh, sitemapindex=True )
        self.assertTrue( s.parsed_index, 'was a sitemapindex')
        self.assertEqual( len(si.resources), 3, '3 sitemaps')
        sms = sorted(si.uris())
        self.assertEqual( sms, ['http://localhost:8888/sitemap00000.xml','http://localhost:8888/sitemap00001.xml','http://localhost:8888/sitemap00002.xml'] )
        #self.assertEqual( si.resources['http://localhost:8888/sitemap00000.xml'].lastmod, '2012-06-13T18:09:13Z' )

    def test_21_parse_multi_sitemapindex(self):
        s = Sitemap()
        fh=open('tests/testdata/sitemapindex2/sitemap.xml','r')
        si = s.parse_xml( fh=fh, sitemapindex=True )
        self.assertTrue( s.parsed_index, 'was a sitemapindex')
        self.assertEqual( len(si.resources), 3, '3 sitemaps listed')

    def test_30_parse_change_list(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="updated" length="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" /></url>\
</urlset>'
        s=Sitemap()
        s.resource_class=Resource
        c=s.parse_xml(fh=StringIO.StringIO(xml))
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
