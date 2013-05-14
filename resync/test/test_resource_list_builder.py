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

    def test01_simple_scan(self):
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual( len(rl), 2 )
        rli = iter(rl)
        r = rli.next()
        self.assertEqual( r.uri, 'http://example.org/t/file_a' )
        self.assertEqual( r.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r.md5, None )
        self.assertEqual( r.length, 20 )
        self.assertEqual( r.path, None )
        r = rli.next()
        self.assertEqual( r.uri, 'http://example.org/t/file_b' )
        self.assertEqual( r.lastmod, '2001-09-09T01:46:40Z' )
        self.assertEqual( r.md5, None )
        self.assertEqual( r.length, 45 )
        self.assertEqual( r.path, None )

    def test02_no_length(self):
        rlb = ResourceListBuilder(set_length=False)
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual( len(rl), 2 )
        rli = iter(rl)
        r = rli.next()
        self.assertEqual( r.uri, 'http://example.org/t/file_a' )
        self.assertEqual( r.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r.md5, None )
        self.assertEqual( r.length, None )
        self.assertEqual( r.path, None )
        r = rli.next()
        self.assertEqual( r.uri, 'http://example.org/t/file_b' )
        self.assertEqual( r.lastmod, '2001-09-09T01:46:40Z' )
        self.assertEqual( r.md5, None )
        self.assertEqual( r.length, None )
        self.assertEqual( r.path, None )

    def test03_set_md5(self):
        rlb = ResourceListBuilder(set_md5=True)
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual( len(rl), 2 )
        rli = iter(rl)
        r = rli.next()
        self.assertEqual( r.uri, 'http://example.org/t/file_a' )
        self.assertEqual( r.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r.md5, 'a/Jv1mYBtSjS4LR+qoft/Q==' )
        self.assertEqual( r.length, 20 )
        self.assertEqual( r.path, None )
        r = rli.next()
        self.assertEqual( r.uri, 'http://example.org/t/file_b' )
        self.assertEqual( r.lastmod, '2001-09-09T01:46:40Z' )
        self.assertEqual( r.md5, 'RS5Uva4WJqxdbnvoGzneIQ==' )
        self.assertEqual( r.length, 45 )
        self.assertEqual( r.path, None )

    def test04_data(self):
        rlb = ResourceListBuilder(set_path=True,set_md5=True)
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual( len(rl), 2)
        r = rl.resources.get('http://example.org/t/file_a')
        self.assertTrue( r is not None )
        self.assertEqual( r.uri, 'http://example.org/t/file_a' )
        self.assertEqual( r.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r.md5, 'a/Jv1mYBtSjS4LR+qoft/Q==' )
        self.assertEqual( r.path, 'resync/test/testdata/dir1/file_a' ) 

    def test05_from_disk_paths(self):
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata/dir1'])
        # no path, should get no resources
        rl = rlb.from_disk(paths=[])
        self.assertEqual( len(rl), 0)
        # full path, 2 resources
        rl = rlb.from_disk(paths=['resync/test/testdata/dir1'])
        self.assertEqual( len(rl), 2)
        # new object with mapper covering larger space of disk
        rlb = ResourceListBuilder(set_path=True)
        rlb.mapper = Mapper(['http://example.org/t','resync/test/testdata'])
        # same path with 2 resources
        rl = rlb.from_disk(paths=['resync/test/testdata/dir1'])
        self.assertEqual( len(rl), 2)
        # same path with 2 resources
        rl = rlb.from_disk(paths=['resync/test/testdata/dir1','resync/test/testdata/dir2'])
        self.assertEqual( len(rl), 3)
        # path that is just a single file
        rl = rlb.from_disk(paths=['resync/test/testdata/dir1/file_a'])
        self.assertEqual( len(rl), 1)
        rli = iter(rl)
        r = rli.next()
        self.assertTrue( r is not None )
        self.assertEqual( r.uri, 'http://example.org/t/dir1/file_a' )
        self.assertEqual( r.lastmod, '2012-07-25T17:13:46Z' )
        self.assertEqual( r.md5, None )
        self.assertEqual( r.length, 20 )
        self.assertEqual( r.path, 'resync/test/testdata/dir1/file_a' ) 

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceListBuilder)
    unittest.TextTestRunner(verbosity=2).run(suite)
