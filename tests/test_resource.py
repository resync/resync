"""Tests for resync.resource."""
import unittest
import re
from resync.resource import Resource, ChangeTypeError


class TestResource(unittest.TestCase):

    def test01_init(self):
        """Test __init__ method."""
        # No uri = error
        self.assertRaises(ValueError, Resource)
        self.assertRaises(ValueError, Resource, timestamp=12)
        # Create with many params
        r1 = Resource(uri='a', timestamp=0, length=123,
                      md5='aaa', sha1='bbb', sha256='ccc',
                      mime_type='text/plain', change='updated',
                      ts_datetime=1000, path='/a/b/c', ln={'x': 'y'},
                      ts_at=2000, ts_completed=3000, ts_from=4000,
                      ts_until=5000)
        self.assertEqual(r1.uri, 'a')
        self.assertEqual(r1.timestamp, 0)
        self.assertEqual(r1.length, 123)
        self.assertEqual(r1.md5, 'aaa')
        self.assertEqual(r1.sha1, 'bbb')
        self.assertEqual(r1.sha256, 'ccc')
        self.assertEqual(r1.mime_type, 'text/plain')
        self.assertEqual(r1.change, 'updated')
        self.assertEqual(r1.ts_datetime, 1000)
        self.assertEqual(r1.path, '/a/b/c')
        self.assertEqual(r1.ln, {'x': 'y'})
        self.assertEqual(r1.ts_at, 2000)
        self.assertEqual(r1.ts_completed, 3000)
        self.assertEqual(r1.ts_from, 4000)
        self.assertEqual(r1.ts_until, 5000)
        # Create r2 like r1
        r2 = Resource(resource=r1)
        self.assertEqual(r2.uri, 'a')
        self.assertEqual(r2.timestamp, 0)
        self.assertEqual(r2.length, 123)
        self.assertEqual(r2.md5, 'aaa')
        self.assertEqual(r2.sha1, 'bbb')
        self.assertEqual(r2.sha256, 'ccc')
        self.assertEqual(r2.mime_type, 'text/plain')
        self.assertEqual(r2.change, 'updated')
        self.assertEqual(r2.ts_datetime, 1000)
        self.assertEqual(r2.path, '/a/b/c')
        self.assertEqual(r2.ln, {'x': 'y'})

    def test02_equal(self):
        """Test equal method via = operator."""
        # just uri
        r1 = Resource('a')
        r2 = Resource('a')
        self.assertEqual(r1, r1)
        self.assertEqual(r1, r2)
        # with timestamps
        r1 = Resource(uri='a', timestamp=1234.0)
        r2 = Resource(uri='a', timestamp=1234.0)
        self.assertEqual(r1, r1)
        self.assertEqual(r1, r2)
        # with lastmod instead of direct timestamp
        r1 = Resource('a')
        r1lm = '2012-01-01T00:00:00Z'
        r1.lastmod = r1lm
        r2 = Resource('a')
        for r2lm in ('2012',
                     '2012-01',
                     '2012-01-01',
                     '2012-01-01T00:00Z',
                     '2012-01-01T00:00:00Z',
                     '2012-01-01T00:00:00.000000Z',
                     '2012-01-01T00:00:00.000000000000Z',
                     '2012-01-01T00:00:00.000000000001Z',  # below resolution
                     '2012-01-01T00:00:00.00+00:00',
                     '2012-01-01T00:00:00.00-00:00',
                     '2012-01-01T02:00:00.00-02:00',
                     '2011-12-31T23:00:00.00+01:00'
                     ):
            r2.lastmod = r2lm
            self.assertEqual(r1.timestamp, r2.timestamp, ('%s (%f) == %s (%f)' % (
                r1lm, r1.timestamp, r2lm, r2.timestamp)))
            self.assertEqual(r1, r2)
        # with slight timestamp diff
        r1 = Resource('a')
        r1.lastmod = '2012-01-02T01:02:03Z'
        r2 = Resource('a')
        r2.lastmod = '2012-01-02T01:02:03.99Z'
        self.assertNotEqual(r1.timestamp, r2.timestamp)
        self.assertEqual(r1, r2)
        # now with too much time diff
        r1 = Resource('a', lastmod='2012-01-11')
        r2 = Resource('a', lastmod='2012-01-22')
        self.assertNotEqual(r1, r2)
        # different uris
        r1 = Resource('a')
        r2 = Resource('b')
        self.assertNotEqual(r1, r2)
        # same and different lengths
        r1 = Resource('a', length=1234)
        r2 = Resource('a', length=4321)
        self.assertNotEqual(r1, r2)
        r2.length = r1.md5
        self.assertEqual(r1, r2)
        # same and different md5
        r1.md5 = "3006f84272f2653a6cf5ec3af8f0d773"
        r2.md5 = "3006f84272f2653a6cf5ec3af8f00000"
        self.assertNotEqual(r1, r2)
        r2.md5 = r1.md5
        self.assertEqual(r1, r2)
        # same and different sha1
        r1.sha1 = "3be0f3af2aa4656ce38e0cef305c6eb2af4385d4"
        r2.sha1 = "555"
        self.assertNotEqual(r1, r2)
        r2.sha1 = r1.sha1
        self.assertEqual(r1, r2)
        # same and different sha256
        r1.sha256 = "f41094ad47ef3e93ec1021bfa40f4bf0185f1bf897533638ae5358b61713f84a"
        r2.sha256 = "fab"
        self.assertNotEqual(r1, r2)
        r2.sha256 = r1.sha256
        self.assertEqual(r1, r2)

    def test04_bad_lastmod(self):
        def setlastmod(r, v):
            r.lastmod = v
        r = Resource('4')
        # Bad formats
        self.assertRaises(ValueError, setlastmod, r, "bad_lastmod")
        self.assertRaises(ValueError, setlastmod, r, "")
        self.assertRaises(ValueError, setlastmod, r, "2012-13-01")
        self.assertRaises(ValueError, setlastmod, r, "2012-12-32")
        self.assertRaises(ValueError, setlastmod, r, "2012-11-01T10:10:60")
        self.assertRaises(ValueError, setlastmod, r, "2012-11-01T10:10:59.9x")
        # Valid ISO8601 but not alloed in W3C Datetime
        self.assertRaises(ValueError, setlastmod, r, "2012-11-01T01:01:01")
        self.assertRaises(ValueError, setlastmod, r, "2012-11-01 01:01:01Z")
        self.assertRaises(ValueError, setlastmod, r, "2012-11-01T01:01:01+0000")
        self.assertRaises(ValueError, setlastmod, r, "2012-11-01T01:01:01-1000")

    def test05_lastmod_roundtrips(self):
        r = Resource('a')
        r.lastmod = '2012-03-14'
        self.assertEqual(r.lastmod, '2012-03-14T00:00:00Z')
        r.lastmod = '2012-03-14T00:00:00+00:00'
        # print r.timestamp
        self.assertEqual(r.lastmod, '2012-03-14T00:00:00Z')
        r.lastmod = '2012-03-14T00:00:00-00:00'
        # print r.timestamp
        self.assertEqual(r.lastmod, '2012-03-14T00:00:00Z')
        r.lastmod = '2012-03-14T18:37:36Z'
        # print r.timestamp
        self.assertEqual(r.lastmod, '2012-03-14T18:37:36Z')

    def test06_str(self):
        r1 = Resource('abc', lastmod='2012-01-01')
        self.assertTrue(re.match(r"\[ abc \| 2012-01-01T", str(r1)))

    def test07_repr(self):
        r1 = Resource('def', lastmod='2012-01-01')
        self.assertEqual(repr(r1), "{'uri': 'def', 'timestamp': 1325376000}")

    def test08_hash(self):
        """Test hash getter and setters."""
        r1 = Resource('abcd')
        r1.md5 = "some_md5"
        r1.sha1 = "some_sha1"
        r1.sha256 = "some_sha256"
        self.assertEqual(r1.md5, "some_md5")
        self.assertEqual(r1.sha1, "some_sha1")
        self.assertEqual(r1.sha256, "some_sha256")
        self.assertEqual(r1.hash, "md5:some_md5 sha-1:some_sha1 sha-256:some_sha256")
        r2 = Resource('def')
        r2.hash = "md5:ddd"
        self.assertEqual(r2.md5, 'ddd')
        self.assertEqual(r2.sha1, None)
        r2.hash = "sha-1:eee"
        self.assertEqual(r2.md5, None)
        self.assertEqual(r2.sha1, 'eee')
        r2.hash = "md5:fff sha-1:eee sha-256:ggg"
        self.assertEqual(r2.md5, 'fff')
        self.assertEqual(r2.sha1, 'eee')
        self.assertEqual(r2.sha256, 'ggg')
        # bogus value will reset
        r2.hash = 11
        self.assertEqual(r2.md5, None)
        self.assertEqual(r2.sha1, None)
        self.assertEqual(r2.sha256, None)
        # string withough : will raise error
        with self.assertRaises(ValueError):
            r2.hash = "no-colon"
        # dupe
        with self.assertRaises(ValueError):
            r2.hash = "md5:aaa md5:bbb"
        # unknown
        with self.assertRaises(ValueError):
            r2.hash = "sha999:aaa"

    def test09_changetypeerror(self):
        r1 = Resource('a')
        self.assertEqual(r1.change, None)
        r1.change = 'deleted'
        self.assertEqual(r1.change, 'deleted')
        self.assertRaises(ChangeTypeError, Resource, 'a', change="bad")
        # disable checking
        ct = Resource.CHANGE_TYPES
        Resource.CHANGE_TYPES = False
        r1 = Resource('a', change="bad")
        self.assertEqual(r1.change, 'bad')
        Resource.CHANGE_TYPES = ct

    def test10_md_at_roundtrips(self):
        r = Resource('a')
        r.md_at = '2013-03-14'
        self.assertEqual(r.md_at, '2013-03-14T00:00:00Z')
        r.md_at = '2013-03-14T00:00:00+00:00'
        self.assertEqual(r.md_at, '2013-03-14T00:00:00Z')
        r.md_at = '2013-03-14T00:00:00-00:00'
        self.assertEqual(r.md_at, '2013-03-14T00:00:00Z')
        r.md_at = '2013-03-14T18:37:36Z'
        self.assertEqual(r.md_at, '2013-03-14T18:37:36Z')

    def test11_md_completed_roundtrips(self):
        r = Resource('a')
        r.md_completed = '2013-04-14'
        self.assertEqual(r.md_completed, '2013-04-14T00:00:00Z')
        r.md_completed = '2013-04-14T00:00:00+00:00'
        self.assertEqual(r.md_completed, '2013-04-14T00:00:00Z')
        r.md_completed = '2013-04-14T00:00:00-00:00'
        self.assertEqual(r.md_completed, '2013-04-14T00:00:00Z')
        r.md_completed = '2013-04-14T18:37:36Z'
        self.assertEqual(r.md_completed, '2013-04-14T18:37:36Z')

    def test12_timevalues(self):
        r = Resource(uri='tv',
                     lastmod="2000-01-01",
                     md_at="2000-01-02",
                     md_completed="2000-01-03",
                     md_from="2000-01-04",
                     md_until="2000-01-05")
        self.assertEqual(r.lastmod, '2000-01-01T00:00:00Z')
        self.assertEqual(r.md_at, '2000-01-02T00:00:00Z')
        self.assertEqual(r.md_completed, '2000-01-03T00:00:00Z')
        self.assertEqual(r.md_from, '2000-01-04T00:00:00Z')
        self.assertEqual(r.md_until, '2000-01-05T00:00:00Z')

    def test13_mime_type(self):
        r = Resource(uri='tv1', mime_type='text/plain')
        self.assertEqual(r.mime_type, 'text/plain')
        r.mime_type = None
        self.assertEqual(r.mime_type, None)
        r = Resource(uri='tv2')
        self.assertEqual(r.mime_type, None)

    def test14_datetime(self):
        # v1.1 adds a datetime attribute
        r = Resource(uri='dt1')
        self.assertEqual(r.datetime, None)
        r = Resource(uri='dt2', datetime='2000-01-04T00:00:00Z')
        self.assertEqual(r.datetime, '2000-01-04T00:00:00Z')

    def test15_link(self):
        """Test link link_href and link_set methods."""
        r = Resource(uri='ln1')
        self.assertEqual(r.link('up'), None)
        self.assertEqual(r.link_href('up'), None)
        r.link_set('up', 'uri:up')
        self.assertEqual(r.link('up'), {'rel': 'up', 'href': 'uri:up'})
        self.assertEqual(r.link_href('up'), 'uri:up')
        r.link_set('down', 'uri:down')
        self.assertEqual(r.link('down'), {'rel': 'down', 'href': 'uri:down'})
        self.assertEqual(r.link_href('down'), 'uri:down')
        r.link_set('up', 'uri:up2')
        self.assertEqual(r.link('up'), {'rel': 'up', 'href': 'uri:up2'})
        r.link_add('up', 'uri:up3')
        self.assertEqual(r.link('up'), {'rel': 'up', 'href': 'uri:up2'})  # still get first
        self.assertEqual(r.ln, [{'rel': 'up', 'href': 'uri:up2'},
                                {'href': 'uri:down', 'rel': 'down'},
                                {'rel': 'up', 'href': 'uri:up3'}])

    def test16_specific_links(self):
        """Test setters/getters for specific link types."""
        r = Resource(uri='laughing')
        r.describedby = 'uri:db'
        self.assertEqual(r.describedby, 'uri:db')
        r.up = 'uri:up'
        self.assertEqual(r.up, 'uri:up')
        r.index = 'uri:index'
        self.assertEqual(r.index, 'uri:index')
        r.contents = 'uri:ct'
        self.assertEqual(r.contents, 'uri:ct')

    def test17_basename(self):
        """Test basename property derived from uri."""
        r = Resource(uri='http://example.org/any/complex/path/file')
        self.assertEqual(r.basename, 'file')
        r.uri = 'http://example.org/any/complex/path/'
        self.assertEqual(r.basename, '')
        r.uri = 'http://example.org'
        self.assertEqual(r.basename, '')

    def test18_str(self):
        """Test str method."""
        self.assertEqual(str(Resource('uri:a')),
                         '[ uri:a | None | None | None ]')
        self.assertEqual(str(Resource('uri:a', timestamp=0, length=999)),
                         '[ uri:a | 1970-01-01T00:00:00Z | 999 | None ]')
        self.assertEqual(str(Resource('uri:a', timestamp=0, length=999, sha256='abcdef123')),
                         '[ uri:a | 1970-01-01T00:00:00Z | 999 | abcdef123 ]')
        self.assertEqual(str(Resource('uri:a', change='updated', ts_datetime=3661)),
                         '[ uri:a | None | None | None | updated @ 1970-01-01T01:01:01Z ]')
        self.assertEqual(str(Resource('uri:a', path='/a/b/c')),
                         '[ uri:a | None | None | None | /a/b/c ]')

    def test19_change_type_error(self):
        """Test error from bad change type."""
        cte = ChangeTypeError('unk')
        self.assertIn('ChangeTypeError: got unk, expected one of ', str(cte))
