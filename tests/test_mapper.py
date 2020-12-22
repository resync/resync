"""Tests for resync.mapper."""
import unittest
from resync.mapper import Mapper, MapperError, Map


class TestMapper(unittest.TestCase):

    def test00_mapper_creation(self):
        m1 = Mapper(['http://e.org/p/', '/tmp/q/'])
        self.assertEqual(len(m1), 1)
        m2 = Mapper(mappings=['http://e.org/p', '/tmp/q'])
        self.assertEqual(len(m2), 1)
        self.assertEqual(str(m1), str(m2))
        m3 = Mapper(['http://e.org/p/=/tmp/q/'])
        self.assertEqual(len(m3), 1)
        self.assertEqual(str(m1), str(m3))
        m4 = Mapper(['http://e.org/p/=/tmp/q/', 'http://e.org/r/=/tmp/s/'])
        m5 = Mapper(['http://e.org/r/=/tmp/s/', 'http://e.org/p/=/tmp/q/'])
        self.assertEqual(len(m4), 2)
        self.assertEqual(len(m5), 2)
        self.assertNotEqual(str(m4), str(m5))
        # error cases
        m6 = Mapper()
        # too many equals
        self.assertRaises(MapperError, m6.parse, ['a=b=c'])
        self.assertRaises(MapperError, m6.parse, ['a=b=c=d'])
        # dupes
        self.assertRaises(MapperError, m6.parse, ['a=b', 'a=c'])
        self.assertRaises(MapperError, m6.parse, ['x=z', 'y=z'])

    def test01_mapper_src_to_dst(self):
        m = Mapper(['http://e.org/p/', '/tmp/q/'])
        self.assertEqual(m.src_to_dst('http://e.org/p/'), '/tmp/q/')
        self.assertEqual(m.src_to_dst('http://e.org/p/aa'), '/tmp/q/aa')
        self.assertEqual(m.src_to_dst('http://e.org/p/aa/bb'), '/tmp/q/aa/bb')
        self.assertEqual(m.src_to_dst('http://e.org/p/aa/bb/'), '/tmp/q/aa/bb/')
        self.assertEqual(m.src_to_dst('http://e.org/p'), '/tmp/q/')
        self.assertRaises(MapperError, m.src_to_dst, 'http://e.org/pa')
        self.assertRaises(MapperError, m.src_to_dst, 'nomatch')

    def test02_mapper_dst_to_src(self):
        m = Mapper(['http://e.org/p/', '/tmp/q/'])
        self.assertEqual(m.dst_to_src('/tmp/q/'), 'http://e.org/p/')
        self.assertEqual(m.dst_to_src('/tmp/q/bb'), 'http://e.org/p/bb')
        self.assertEqual(m.dst_to_src('/tmp/q/bb/cc'), 'http://e.org/p/bb/cc')
        self.assertEqual(m.dst_to_src('/tmp/q'), 'http://e.org/p/')
        self.assertRaises(MapperError, m.dst_to_src, '/tmp/qa')
        self.assertRaises(MapperError, m.dst_to_src, 'nomatch')

    def test03_mapper2_src_to_dst(self):
        m = Mapper(['http://e.org/p=/tmp/q', 'http://e.org/r=/tmp/s'])
        self.assertEqual(m.src_to_dst('http://e.org/p/'), '/tmp/q/')
        self.assertEqual(m.src_to_dst('http://e.org/p/aa'), '/tmp/q/aa')
        self.assertEqual(m.src_to_dst('http://e.org/r/'), '/tmp/s/')
        self.assertEqual(m.src_to_dst('http://e.org/r/aa'), '/tmp/s/aa')

    def test04_mapper2_dst_to_src(self):
        m = Mapper(['http://e.org/p=/tmp/q', 'http://e.org/r=/tmp/s'])
        self.assertEqual(m.dst_to_src('/tmp/q/'), 'http://e.org/p/')
        self.assertEqual(m.dst_to_src('/tmp/q/bb'), 'http://e.org/p/bb')
        self.assertEqual(m.dst_to_src('/tmp/s/'), 'http://e.org/r/')
        self.assertEqual(m.dst_to_src('/tmp/s/bb'), 'http://e.org/r/bb')

    def test05_path_from_uri(self):
        m = Mapper()
        self.assertEqual(m.path_from_uri('a_file'), 'a_file')
        self.assertEqual(m.path_from_uri(
            'some_path/a_file'), 'some_path/a_file')
        self.assertEqual(m.path_from_uri('http://localhost/p'), 'localhost_p')
        self.assertEqual(m.path_from_uri(
            'http://localhost:8888/p'), 'localhost_8888_p')
        self.assertEqual(m.path_from_uri(
            'https://localhost:8888/p'), 'localhost_8888_p')
        self.assertEqual(m.path_from_uri('http://example.com'), 'example.com')
        self.assertEqual(m.path_from_uri('http://example.com/'), 'example.com')
        self.assertEqual(m.path_from_uri(
            'http://example.com/ex1'), 'example.com_ex1')
        self.assertEqual(m.path_from_uri(
            'http://example.com/ex1/'), 'example.com_ex1')

    def test06_mapper_unsafe(self):
        self.assertFalse(Mapper(['http://example.com/=/tmp/a']).unsafe())
        self.assertFalse(
            Mapper(['http://example.com/=http://example.com/']).unsafe())
        self.assertFalse(Mapper(['http://example.com/'],
                                use_default_path=True).unsafe())
        # Following hits case of single local arg supplied
        self.assertTrue(Mapper(['/tmp/a'], use_default_path=True).unsafe())
        # One good, one bad -> bad
        self.assertTrue(
            Mapper(['http://example.com/=/tmp/a', '/tmp/a=/tmp']).unsafe())

    def test07_default_src_uri(self):
        self.assertEqual(Mapper(['a=b']).default_src_uri(), 'a')
        self.assertEqual(Mapper(['a=b', 'b=c']).default_src_uri(), 'a')
        self.assertRaises(MapperError, Mapper().default_src_uri)


class TestMap(unittest.TestCase):

    def test01_map_unsafe(self):
        """Test unsafe method."""
        self.assertFalse(Map('http://example.com/', 'path').unsafe())
        # Note the first is a URI and the second is a (silly) path in the
        # following
        self.assertFalse(Map('http://example.com/', 'http://example.com/').unsafe())
        self.assertFalse(Map('a', 'b').unsafe())
        self.assertFalse(Map('path/a', 'path/b').unsafe())
        # The following are unsafe
        self.assertTrue(Map('path', 'path').unsafe())
        self.assertTrue(Map('path/a', 'path').unsafe())
        self.assertTrue(Map('path', 'path/b').unsafe())

    def test02_dst_to_src(self):
        """Test dst_to_src method."""
        m = Map('uri:a/b', 'path/c')
        self.assertEqual(m.dst_to_src('path/c/file'), 'uri:a/b/file')
        self.assertEqual(m.dst_to_src('path/c/file/'), 'uri:a/b/file/')
        self.assertEqual(m.dst_to_src('path/c'), 'uri:a/b/')
        self.assertEqual(m.dst_to_src('path/c/'), 'uri:a/b/')
        self.assertEqual(m.dst_to_src('path/cliff'), None)
        # Note that trailing slashes on the map elements have no effect
        m = Map('uri:a/b/', 'path/c/')
        self.assertEqual(m.dst_to_src('path/c'), 'uri:a/b/')
        self.assertEqual(m.dst_to_src('path/c/'), 'uri:a/b/')
        self.assertEqual(m.dst_to_src('path/cliff'), None)
        # Failed maps return None
        self.assertEqual(m.dst_to_src('c/file'), None)
        self.assertEqual(m.dst_to_src(''), None)

    def test03_src_to_dst(self):
        """Test src_to_dst method."""
        m = Map('uri:x/', '/tmp/gg/')
        self.assertEqual(m.src_to_dst('uri:other'), None)
        self.assertEqual(m.src_to_dst('uri:x'), '/tmp/gg/')
        self.assertEqual(m.src_to_dst('uri:x/'), '/tmp/gg/')
        self.assertEqual(m.src_to_dst('uri:x/lizard'), '/tmp/gg/lizard')
        self.assertEqual(m.src_to_dst('uri:x/lizard/'), '/tmp/gg/lizard/')
