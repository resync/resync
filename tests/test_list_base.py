from tests.testcase_with_tmpdir import TestCase

import sys
import os.path
import unittest
try:  # python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError:  # python3
    import io

from resync.resource import Resource
from resync.list_base import ListBase
from resync.sitemap import Sitemap, SitemapIndexError

# etree gives ParseError in 2.7, ExpatError in 2.6
etree_error_class = None
if (sys.version_info < (2, 7)):
    from xml.parsers.expat import ExpatError
    etree_error_class = ExpatError
else:
    from xml.etree.ElementTree import ParseError
    etree_error_class = ParseError


class TestListBase(TestCase):

    def test01_len_count(self):
        # count sets explicit number of resources, len(resources) not used
        lb = ListBase()
        self.assertEqual(len(lb), 0)
        lb.add(Resource('a'))
        self.assertEqual(len(lb), 1)
        lb = ListBase(count=100)
        self.assertEqual(len(lb), 100)

    def test02_print(self):
        lb = ListBase()
        lb.add(Resource(uri='a', lastmod='2001-01-01', length=1234))
        lb.add(Resource(uri='b', lastmod='2002-02-02', length=56789))
        lb.add(Resource(uri='c', lastmod='2003-03-03', length=0))
        lb.md['from'] = None  # avoid now being added
        x = lb.as_xml()
        self.assertEqual(x, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="unknown" /><url><loc>a</loc><lastmod>2001-01-01T00:00:00Z</lastmod><rs:md length="1234" /></url><url><loc>b</loc><lastmod>2002-02-02T00:00:00Z</lastmod><rs:md length="56789" /></url><url><loc>c</loc><lastmod>2003-03-03T00:00:00Z</lastmod><rs:md length="0" /></url></urlset>')

    def test03_read(self):
        # just does parse
        lb = ListBase()
        lb.read(uri='tests/testdata/unknown/unknown1.xml')
        self.assertEqual(len(lb.resources), 2)

    def test04_parse(self):
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="unknown" from="2013-02-12T14:09:00Z" />\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" /></url>\
</urlset>'
        # parse from string
        lb1 = ListBase()
        lb1.parse(str_data=xml)
        self.assertEqual(len(lb1.resources), 2, 'got 2 resources')
        # parse from fh
        lb2 = ListBase()
        lb2.parse(fh=io.StringIO(xml))
        self.assertEqual(len(lb2.resources), 2, 'got 2 resources')
        # parse from string (LEGACY parameter name, to be removed)
        lb3 = ListBase()
        lb3.parse(str=xml)
        self.assertEqual(len(lb3.resources), 2, 'got 2 resources')
        # file that doesn't exits
        lb4 = ListBase()
        self.assertRaises(Exception, lb4.parse,
                          uri='tests/testdata/does_not_exist')
        # nothing
        self.assertRaises(Exception, lb4.parse)

    def test04_write(self):
        lb = ListBase(capability_name='special')
        lb.add(Resource(uri='http://example.org/lemon'))
        lb.add(Resource(uri='http://example.org/orange'))
        basename = os.path.join(self.tmpdir, 'lb.xml')
        lb.write(basename=basename)
        self.assertTrue(os.path.exists(basename))
        # and now parse back
        fh = open(basename, 'r')
        lb2 = ListBase(capability_name='special')
        lb2.parse(fh=fh)
        self.assertEqual(lb2.capability, 'special')
        self.assertEqual(len(lb2), 2)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestListBase)
    unittest.TextTestRunner(verbosity=2).run(suite)
