import unittest
import re
import os
import time
from resync.resource_list_builder import ResourceListBuilder
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
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        rl.md['modified']=None #don't write so we can test output easily
        self.assertEqual(rl.as_xml(),'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="resourcelist" /><url><loc>http://example.org/t/file_a</loc><lastmod>2012-07-25T17:13:46Z</lastmod><rs:md length=\"20\" /></url><url><loc>http://example.org/t/file_b</loc><lastmod>2001-09-09T01:46:40Z</lastmod><rs:md length=\"45\" /></url></urlset>' )

    def test2_pretty_output(self):
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        rl.md['modified']=None #don't write so we can test output easily
        self.assertEqual(rl.as_xml(pretty_xml=True),'<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\n<rs:md capability="resourcelist" />\n<url><loc>http://example.org/t/file_a</loc><lastmod>2012-07-25T17:13:46Z</lastmod><rs:md length=\"20\" /></url>\n<url><loc>http://example.org/t/file_b</loc><lastmod>2001-09-09T01:46:40Z</lastmod><rs:md length=\"45\" /></url>\n</urlset>' )

    def test3_with_md5(self):
        rlb = ResourceListBuilder(do_md5=True)
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        xml = rl.as_xml()
        self.assertNotEqual( None, re.search('<loc>http://example.org/t/file_a</loc><lastmod>[\w\:\-]+Z</lastmod><rs:md hash=\"md5:a/Jv1mYBtSjS4LR\+qoft/Q==\" length=\"20\" />',xml) ) #must escape + in md5
        self.assertNotEqual( None, re.search('<loc>http://example.org/t/file_b</loc><lastmod>[\w\:\-]+Z</lastmod><rs:md hash=\"md5:RS5Uva4WJqxdbnvoGzneIQ==\" length=\"45\" />',xml) )

    def test4_data(self):
        rlb = ResourceListBuilder(do_md5=True)
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual( len(rl), 2)
        r1 = rl.resources.get('http://example.org/t/file_a')
        self.assertTrue( r1 is not None )
        self.assertEqual( r1.uri, 'http://example.org/t/file_a' )
        self.assertEqual( r1.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r1.md5, 'a/Jv1mYBtSjS4LR+qoft/Q==' )
        self.assertEqual( r1.path, 'resync/test/testdata/dir1/file_a' ) 

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceListBuilder)
    unittest.TextTestRunner(verbosity=2).run(suite)
