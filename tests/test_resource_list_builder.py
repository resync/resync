import unittest
import re
import os
from testfixtures import LogCapture
import time

from resync.resource_list_builder import ResourceListBuilder
from resync.resource_list import ResourceList
from resync.resource import Resource
from resync.mapper import Mapper, MapperError


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
        self.assertEqual(r.md5, '6bf26fd66601b528d2e0b47eaa87edfd')
        self.assertEqual(r.length, 20)
        self.assertEqual(r.path, None)
        r = next(rli)
        self.assertEqual(r.uri, 'http://example.org/t/file_b')
        self.assertEqual(r.lastmod, '2001-09-09T01:46:40Z')
        self.assertEqual(r.md5, '452e54bdae1626ac5d6e7be81b39de21')
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
        self.assertEqual(r.md5, '6bf26fd66601b528d2e0b47eaa87edfd')
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

    def test10_add_exclude_patterns(self):
        """Test add_exclude_patterns method."""
        rlb = ResourceListBuilder()
        self.assertEqual(len(rlb.exclude_patterns), 0)
        rlb.add_exclude_patterns(['aaa', 'bbb'])
        self.assertIn('aaa', rlb.exclude_patterns)
        self.assertIn('bbb', rlb.exclude_patterns)

    def test11_compile_excludes(self):
        """Test _compile_excludes method."""
        rlb = ResourceListBuilder()
        self.assertEqual(len(rlb.compiled_exclude_patterns), 0)
        rlb.exclude_patterns = [r'aaa\d+', r'bbb']
        rlb._compile_excludes()
        self.assertEqual(len(rlb.compiled_exclude_patterns), 2)
        # Error case
        rlb.exclude_patterns.append('bad regex \\')
        self.assertRaises(ValueError, rlb._compile_excludes)

    def test12_exclude(self):
        """Test _exclude method."""
        rlb = ResourceListBuilder()
        rlb.add_exclude_patterns(['.*frog.*'])
        rlb._compile_excludes()
        self.assertTrue(rlb._exclude('a frog'))
        self.assertFalse(rlb._exclude('toad'))

    def test13_from_disk_add_path(self):
        """Test from_disk_add_path method."""
        # Check sanity check - must have path, resource_list and mapper
        rlb = ResourceListBuilder(mapper=Mapper())
        self.assertRaises(ValueError, rlb.from_disk_add_path, path='aaa')
        self.assertRaises(ValueError, rlb.from_disk_add_path, resource_list=ResourceList())
        rlb = ResourceListBuilder()
        self.assertRaises(ValueError, rlb.from_disk_add_path, path='aaa', resource_list=ResourceList())
        # Check log message
        rlb = ResourceListBuilder(mapper=Mapper(['http://example.org/', 'tests']))
        rlb.log_count_increment = 2
        rl = ResourceList()
        with LogCapture() as lc:
            rlb.from_disk_add_path(path='tests/testdata/dir1', resource_list=rl)
            self.assertIn('from_disk_add_path: 2 files...', lc.records[-1].msg)
        # text excluding dirs -- just one file under find2 not excluced
        rlb = ResourceListBuilder(mapper=Mapper(['http://example.org/', 'tests']))
        rl = ResourceList()
        rlb.add_exclude_patterns(['find1', 'find3'])
        rlb._compile_excludes()
        rlb.from_disk_add_path(path='tests/testdata/find', resource_list=rl)
        self.assertEqual(len(rl), 1)

    def test14_add_file(self):
        """Test add_file method."""
        rlb = ResourceListBuilder(mapper=Mapper(['http://example.org/', 'tests']))
        rl = ResourceList()
        rlb.add_exclude_patterns(['.*ro'])
        with LogCapture() as lc:
            # escluded
            rlb.add_file(resource_list=rl, file='frog')
            self.assertIn("Excluding file 'frog'", lc.records[-1].msg)
            # mapper error
            self.assertRaises(MapperError, rlb.add_file, resource_list=rl, file='i-dont-exist')
            # map OK but doesn't exist
            rlb.add_file(resource_list=rl, file='tests/i-dont-exist')
            self.assertIn("Ignoring file 'tests/i-dont-exist'", lc.records[-1].msg)
            # ignore symlink by default
            rlb.add_file(resource_list=rl, file='tests/testdata/symlink/dir2/a_file.txt')
            self.assertIn("Ignoring symlink 'tests/testdata/symlink/dir2/a_file.txt'", lc.records[-1].msg)
            # ...or not
            rl = ResourceList()
            rlb.include_symlinks = True
            rlb.add_file(resource_list=rl, file='tests/testdata/symlink/dir2/a_file.txt')
            self.assertEqual(len(rl), 1)
        # Check hashing
        rlb = ResourceListBuilder(mapper=Mapper(['http://example.org/', 'tests/testdata/dir1/']),
                                  set_hashes=['md5', 'sha-1', 'sha-256'])
        rl = ResourceList()
        rlb.add_file(resource_list=rl, file='tests/testdata/dir1/file_a')
        self.assertEqual(rl['http://example.org/file_a'].md5, '6bf26fd66601b528d2e0b47eaa87edfd')
        self.assertEqual(rl['http://example.org/file_a'].sha1, 'c60a598a5d9e489cf50533eeead6d70f15eafcf8')
        self.assertEqual(rl['http://example.org/file_a'].sha256, '1c6291bfac0322752c4632ebd69bf6d81d53985fbf5ee54de5cc1fefba6566b6')
