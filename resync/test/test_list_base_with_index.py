import sys
import unittest
import StringIO
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

    def test_08_print(self):
        lb = ListBaseWithIndex()
        lb.add( Resource(uri='a',lastmod='2001-01-01',length=1234) )
        lb.add( Resource(uri='b',lastmod='2002-02-02',length=56789) )
        lb.add( Resource(uri='c',lastmod='2003-03-03',length=0) )
        lb.md['modified']=None #avoid now being added
        #print lb
        self.assertEqual( lb.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="unknown" /><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length="1234" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length="56789" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md length="0" /></url></urlset>' )

    def test_08_print_iter(self):
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
        lb.md['modified']=None #avoid now being added
        #print lb
        self.assertEqual( lb.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="unknown" /><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length="1234" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length="56789" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md length="0" /></url></urlset>' )


    def test_11_parse_2(self):
        xml='<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="unknown" modified="2013-02-12T14:09:00Z" />\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" /></url>\
</urlset>'
        lb=ListBaseWithIndex()
        lb.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(lb.resources), 2, 'got 2 resources')

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestListBaseWithIndex)
    unittest.TextTestRunner(verbosity=2).run(suite)
