import unittest
import re
import os
import time
from resync.resource_list_builder import ResourceListBuilder
from resync.sitemap import Sitemap
from resync.mapper import Mapper

class TestResourceListBuilder(unittest.TestCase):

    def setUp(self):
        # Set timestamps (mtime) for test data. Timestamps on disk are
        # in UTC so no conversion issues.
        # Test case file_a: 1343236426 = 2012-07-25T17:13:46Z
        # Test case file_b: 1000000000 = 2001-09-09T01:46:40Z
        os.utime( "resync/test/testdata/dir1/file_a", (0, 1343236426 ) )
        os.utime( "resync/test/testdata/dir1/file_b", (0, 1000000000 ) )

    def test1_simple_output(self):
        ib = ResourceListBuilder()
        ib.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        i = ib.from_disk()
        self.assertEqual(Sitemap().resources_as_xml(i),'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><url><loc>http://example.org/t/file_a</loc><lastmod>2012-07-25T17:13:46Z</lastmod><rs:md length=\"20\" /></url><url><loc>http://example.org/t/file_b</loc><lastmod>2001-09-09T01:46:40Z</lastmod><rs:md length=\"45\" /></url></urlset>' )

    def test2_pretty_output(self):
        ib = ResourceListBuilder()
        ib.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        i = ib.from_disk()
        s = Sitemap()
        s.pretty_xml=True
        self.assertEqual(s.resources_as_xml(i),'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\n<url><loc>http://example.org/t/file_a</loc><lastmod>2012-07-25T17:13:46Z</lastmod><rs:md length=\"20\" /></url>\n<url><loc>http://example.org/t/file_b</loc><lastmod>2001-09-09T01:46:40Z</lastmod><rs:md length=\"45\" /></url>\n</urlset>' )

    def test3_with_md5(self):
        ib = ResourceListBuilder(do_md5=True)
        ib.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        i = ib.from_disk()
        s = Sitemap()
        xml = s.resources_as_xml(i)
        self.assertNotEqual( None, re.search('<loc>http://example.org/t/file_a</loc><lastmod>[\w\:\-]+Z</lastmod><rs:md hash=\"md5:a/Jv1mYBtSjS4LR\+qoft/Q==\" length=\"20\" />',xml) ) #must escape + in md5
        self.assertNotEqual( None, re.search('<loc>http://example.org/t/file_b</loc><lastmod>[\w\:\-]+Z</lastmod><rs:md hash=\"md5:RS5Uva4WJqxdbnvoGzneIQ==\" length=\"45\" />',xml) )

    def test4_data(self):
        ib = ResourceListBuilder(do_md5=True)
        ib.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        i = ib.from_disk()
        self.assertEqual( len(i), 2)
        r1 = i.resources.get('http://example.org/t/file_a')
        self.assertTrue( r1 is not None )
        self.assertEqual( r1.uri, 'http://example.org/t/file_a' )
        self.assertEqual( r1.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r1.md5, 'a/Jv1mYBtSjS4LR+qoft/Q==' )
        self.assertEqual( r1.path, 'resync/test/testdata/dir1/file_a' ) 

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceListBuilder)
    unittest.TextTestRunner(verbosity=2).run(suite)
