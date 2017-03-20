import unittest
import re
import os
import time
from resync.resource_list_builder import ResourceListBuilder
from resync.resource import Resource
from resync.mapper import Mapper


class TestResourceListBuilder(unittest.TestCase):

    def setUp(self):
        # Set timestamps (mtime) for test data. Timestamps on disk are
        # in UTC so no conversion issues.
        # Test case file_a: 1343236426 = 2012-07-25T17:13:46Z
        # Test case file_b: 1000000000 = 2001-09-09T01:46:40Z
        os.utime("tests/testdata/dir1/file_a", (0, 1343236426))
        os.utime("tests/testdata/dir1/file_b", (0, 1000000000))

    def test01_simple_scan(self):
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['http://example.org/t', 'tests/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual(len(rl), 2)
        rli = iter(rl)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_a')
        self.assertEqual(r.lastmod, '2012-07-25T17:13:46Z')
        self.assertEqual(r.md5, None)
        self.assertEqual(r.length, 20)
        self.assertEqual(r.path, None)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_b')
        self.assertEqual(r.lastmod, '2001-09-09T01:46:40Z')
        self.assertEqual(r.md5, None)
        self.assertEqual(r.length, 45)
        self.assertEqual(r.path, None)
        # Make sure at and completed were set
        self.assertTrue(rl.md_at is not None)
        self.assertTrue(rl.md_completed is not None)

    def test02_no_length(self):
        rlb = ResourceListBuilder(set_length=False)
        rlb.mapper = Mapper(['http://example.org/t', 'tests/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual(len(rl), 2)
        rli = iter(rl)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_a')
        self.assertEqual(r.lastmod, '2012-07-25T17:13:46Z')
        self.assertEqual(r.md5, None)
        self.assertEqual(r.length, None)
        self.assertEqual(r.path, None)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_b')
        self.assertEqual(r.lastmod, '2001-09-09T01:46:40Z')
        self.assertEqual(r.md5, None)
        self.assertEqual(r.length, None)
        self.assertEqual(r.path, None)

    def test03_set_hashes(self):
        rlb = ResourceListBuilder(set_hashes=['md5'])
        rlb.mapper = Mapper(['http://example.org/t', 'tests/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual(len(rl), 2)
        rli = iter(rl)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_a')
        self.assertEqual(r.lastmod, '2012-07-25T17:13:46Z')
        self.assertEqual(r.md5, 'a/Jv1mYBtSjS4LR+qoft/Q==')
        self.assertEqual(r.length, 20)
        self.assertEqual(r.path, None)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_b')
        self.assertEqual(r.lastmod, '2001-09-09T01:46:40Z')
        self.assertEqual(r.md5, 'RS5Uva4WJqxdbnvoGzneIQ==')
        self.assertEqual(r.length, 45)
        self.assertEqual(r.path, None)

    def test04_data(self):
        rlb = ResourceListBuilder(set_path=True, set_hashes=['md5'])
        rlb.mapper = Mapper(['http://example.org/t', 'tests/testdata/dir1'])
        rl = rlb.from_disk()
        self.assertEqual(len(rl), 2)
        r = rl.resources.get('http://example.org/t/file_a')
        self.assertTrue(r is not None)
        self.assertEqual(r.uri, 'http://example.org/t/file_a')
        self.assertEqual(r.lastmod, '2012-07-25T17:13:46Z')
        self.assertEqual(r.md5, 'a/Jv1mYBtSjS4LR+qoft/Q==')
        self.assertEqual(r.path, 'tests/testdata/dir1/file_a')

    def test05_from_disk_paths(self):
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['http://example.org/t', 'tests/testdata/dir1'])
        # no path, should get no resources
        rl = rlb.from_disk(paths=[])
        self.assertEqual(len(rl), 0)
        # full path, 2 resources
        rl = rlb.from_disk(paths=['tests/testdata/dir1'])
        self.assertEqual(len(rl), 2)
        # new object with mapper covering larger space of disk
        rlb = ResourceListBuilder(set_path=True)
        rlb.mapper = Mapper(['http://example.org/t', 'tests/testdata'])
        # same path with 2 resources
        rl = rlb.from_disk(paths=['tests/testdata/dir1'])
        self.assertEqual(len(rl), 2)
        # same path with 2 resources
        rl = rlb.from_disk(
            paths=['tests/testdata/dir1', 'tests/testdata/dir2'])
        self.assertEqual(len(rl), 3)
        # path that is just a single file
        rl = rlb.from_disk(paths=['tests/testdata/dir1/file_a'])
        self.assertEqual(len(rl), 1)
        rli = iter(rl)
        r = next(rli)
        self.assertTrue(r is not None)
        self.assertEqual(r.uri, 'http://example.org/t/dir1/file_a')
        self.assertEqual(r.lastmod, '2012-07-25T17:13:46Z')
        self.assertEqual(r.md5, None)
        self.assertEqual(r.length, 20)
        self.assertEqual(r.path, 'tests/testdata/dir1/file_a')

    def test06_odd_file_names(self):
        """Verfify we can read unicode file names properly."""
        rlb = ResourceListBuilder()
        rlb.mapper = Mapper(['x:', 'tests/testdata/odd_file_names'])
        rl = rlb.from_disk(paths=['tests/testdata/odd_file_names'])
        # Get list of URIs to test
        uris = [x.uri for x in rl]
        self.assertTrue('x:/not_odd.txt' in uris)
        self.assertTrue('x:/with&ampersand.txt' in uris)
        self.assertTrue('x:/with spaces.txt' in uris)
        # File names for accented chars represented with combining chars
        self.assertTrue(u'x:/Pi\u006e\u0303a_Colada.txt' in uris)
        self.assertFalse(u'x:/Pi\u00f1a_Colada.txt' in uris)
        self.assertTrue(u'x:/A_\u0041\u0303_tilde.txt' in uris)
        self.assertFalse(u'x:/A_\u00c3_tilde.txt' in uris)
        # Snowman is single char
        self.assertFalse(u'x:snowman_\u2603.txt' in uris)

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestResourceListBuilder)
    unittest.TextTestRunner(verbosity=2).run(suite)
