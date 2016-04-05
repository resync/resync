import re
import sys
import unittest
try: #python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError: #python3
    import io

from resync.resource import Resource
from resync.list_base_with_index import ListBaseWithIndex, ListBaseIndexError
from resync.sitemap import Sitemap, SitemapIndexError

# etree gives ParseError in 2.7, ExpatError in 2.6
etree_error_class = None
if (sys.version_info < (2,7)):
    from xml.parsers.expat import ExpatError
    etree_error_class = ExpatError
else:
    from xml.etree.ElementTree import ParseError
    etree_error_class = ParseError

class TestListBaseWithIndex(unittest.TestCase):

    def test01_print(self):
        lb = ListBaseWithIndex()
        lb.add( Resource(uri='a',lastmod='2001-01-01',length=1234) )
        lb.add( Resource(uri='b',lastmod='2002-02-02',length=56789) )
        lb.add( Resource(uri='c',lastmod='2003-03-03',length=0) )
        lb.md['from']=None #avoid now being added
        self.assertEqual( lb.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="unknown" /><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length="1234" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length="56789" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md length="0" /></url></urlset>' )

    def test02_print_iter(self):
        r = [ Resource(uri='a',lastmod='2001-01-01',length=1234),
              Resource(uri='b',lastmod='2002-02-02',length=56789),
              Resource(uri='c',lastmod='2003-03-03',length=0) ]
        # without setting count will barf on len() attempt
        lb = ListBaseWithIndex( resources=iter(r) )
        self.assertRaises( TypeError, lb.as_xml )
        # set explicit count larger than max_sitemap_entiries and as_xml will throw exception
        lb = ListBaseWithIndex( resources=iter(r), count=3 )
        lb.max_sitemap_entries = 2
        self.assertRaises( ListBaseIndexError, lb.as_xml )
        # set explicit count and all will be OK
        lb = ListBaseWithIndex( resources=iter(r), count=3 )
        lb.md['from']=None #avoid now being added
        self.assertEqual( lb.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="unknown" /><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length="1234" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length="56789" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md length="0" /></url></urlset>' )

    def test03_parse_2(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="unknown" from="2013-02-12T14:09:00Z" />\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" /></url>\
</urlset>'
        lb=ListBaseWithIndex()
        lb.parse(fh=io.StringIO(xml))
        self.assertEqual( len(lb.resources), 2, 'got 2 resources')
        
    def test16_as_xml(self):
        r = [ Resource(uri='a',lastmod='2014-04-14',length=14),
              Resource(uri='b',lastmod='2015-05-15',length=15),
              Resource(uri='c',lastmod='2016-06-16',length=16) ]
        lb=ListBaseWithIndex( resources=r )
        lb.max_sitemap_entries = 3
        # One file
        xml = lb.as_xml()
        self.assertTrue( re.search(r'<urlset ',xml) ) 
        self.assertTrue( re.search(r'<loc>a</loc>',xml) )
        self.assertTrue( re.search(r'<loc>b</loc>',xml) )
        self.assertTrue( re.search(r'<loc>c</loc>',xml) )
        # Needs multifile bit not allowed
        lb.max_sitemap_entries = 1
        self.assertRaises( ListBaseIndexError, lb.as_xml )
        # Allow multifile...
        xml = lb.as_xml( allow_multifile=True )
        self.assertTrue( re.search(r'<sitemapindex', xml) ) 
        self.assertTrue( re.search(r'<loc>/tmp/sitemap00001.xml</loc>', xml) )
        self.assertTrue( re.search(r'<loc>/tmp/sitemap00002.xml</loc>', xml) )
        self.assertFalse( re.search(r'<loc>/tmp/sitemap00003.xml</loc>', xml) )

    def test17_as_xml_index(self):
        r = [ Resource(uri='a',lastmod='2006-01-01',length=12),
              Resource(uri='b',lastmod='2007-02-02',length=34),
              Resource(uri='c',lastmod='2008-03-03',length=56) ]
        lb=ListBaseWithIndex( resources=r )
        lb.max_sitemap_entries = 2
        xml = lb.as_xml_index()
        self.assertTrue( re.search(r'<loc>/tmp/sitemap00001.xml</loc>', xml) )
        self.assertFalse( re.search(r'<loc>/tmp/sitemap00002.xml</loc>', xml) )
        # Index not required
        lb.max_sitemap_entries = 3
        self.assertRaises( ListBaseIndexError, lb.as_xml_index )

    def test18_as_xml_part(self):
        r = [ Resource(uri='a',lastmod='2006-01-01',length=12),
              Resource(uri='b',lastmod='2007-02-02',length=34),
              Resource(uri='c',lastmod='2008-03-03',length=56) ]
        lb=ListBaseWithIndex( resources=r )
        # Allow unlimited entries, part makes no sense
        lb.max_sitemap_entries = None
        self.assertRaises( ListBaseIndexError, lb.as_xml_part )
        # Request after end
        lb.max_sitemap_entries = 1
        self.assertRaises( ListBaseIndexError, lb.as_xml_part, part_number=9 )
        # Allow only 1 entry
        lb.max_sitemap_entries = 1
        xml = lb.as_xml_part( part_number=1 )
        self.assertFalse( re.search(r'<loc>a</loc>',xml) )
        self.assertTrue( re.search(r'<loc>b</loc>',xml) )
        self.assertFalse( re.search(r'<loc>c</loc>',xml) )
        # Request truncated
        lb.max_sitemap_entries = 2
        xml = lb.as_xml_part( part_number=1 )
        self.assertFalse( re.search(r'<loc>a</loc>',xml) )
        self.assertFalse( re.search(r'<loc>b</loc>',xml) )
        self.assertTrue( re.search(r'<loc>c</loc>',xml) )

    def test20_index_as_xml(self):
        # Check XML for empty case
        lb=ListBaseWithIndex()
        self.assertEqual( lb.index_as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="unknown" /></sitemapindex>' )
        # Add a resource and make sure we find that
        lb.add( Resource(uri='a',lastmod='2001-01-01',length=1234) )
        xml = lb.index_as_xml()
        self.assertTrue( re.search(r'<loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod>',xml) )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestListBaseWithIndex)
    unittest.TextTestRunner(verbosity=2).run(suite)
