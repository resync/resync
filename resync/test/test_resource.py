import unittest
import re
from resync.resource import Resource, ChangeTypeError

class TestResource(unittest.TestCase):

    def test01a_same(self):
        r1 = Resource('a')
        r2 = Resource('a')
        self.assertEqual( r1, r1 )
        self.assertEqual( r1, r2 )

    def test01b_same(self):
        r1 = Resource(uri='a',timestamp=1234.0)
        r2 = Resource(uri='a',timestamp=1234.0)
        self.assertEqual( r1, r1 )
        self.assertEqual( r1, r2 )

    def test01c_same(self):
        """Same with lastmod instead of direct timestamp"""
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
                     '2012-01-01T00:00:00.000000000001Z', #below resolution
                     '2012-01-01T00:00:00.00+00:00',
                     '2012-01-01T00:00:00.00-00:00',
                     '2012-01-01T02:00:00.00-02:00',
                     '2011-12-31T23:00:00.00+01:00'
                     ):
            r2.lastmod = r2lm
            self.assertEqual( r1.timestamp, r2.timestamp, ('%s (%f) == %s (%f)' % (r1lm,r1.timestamp,r2lm,r2.timestamp)) )
            self.assertEqual( r1, r2 )

    def test01d_same(self):
        """Same with slight timestamp diff"""
        r1 = Resource('a')
        r1.lastmod='2012-01-02T01:02:03Z'
        r2 = Resource('a')
        r2.lastmod='2012-01-02T01:02:03.99Z'
        self.assertNotEqual( r1.timestamp, r2.timestamp )
        self.assertEqual( r1, r2 )

    def test02a_diff(self):
        r1 = Resource('a')
        r2 = Resource('b')
        self.assertNotEqual(r1,r2)

    def test02b_diff(self):
        r1 = Resource('a',lastmod='2012-01-11')
        r2 = Resource('a',lastmod='2012-01-22')
        #print 'r1 == r2 : '+str(r1==r2)
        self.assertNotEqual( r1, r2 )

    def test04_bad_lastmod(self):
        def setlastmod(r,v):
            r.lastmod=v
        r = Resource('4')
        # Bad formats
        self.assertRaises( ValueError, setlastmod, r, "bad_lastmod" )
        self.assertRaises( ValueError, setlastmod, r, "" )
        self.assertRaises( ValueError, setlastmod, r, "2012-13-01" )
        self.assertRaises( ValueError, setlastmod, r, "2012-12-32" )
        self.assertRaises( ValueError, setlastmod, r, "2012-11-01T10:10:60" )
        self.assertRaises( ValueError, setlastmod, r, "2012-11-01T10:10:59.9x" )
        # Valid ISO8601 but not alloed in W3C Datetime
        self.assertRaises( ValueError, setlastmod, r, "2012-11-01T01:01:01" )
        self.assertRaises( ValueError, setlastmod, r, "2012-11-01 01:01:01Z" )
        self.assertRaises( ValueError, setlastmod, r, "2012-11-01T01:01:01+0000" )
        self.assertRaises( ValueError, setlastmod, r, "2012-11-01T01:01:01-1000" )
   
    def test05_lastmod_roundtrips(self):
        r = Resource('a')
        r.lastmod='2012-03-14'
        self.assertEqual( r.lastmod, '2012-03-14T00:00:00Z' )
        r.lastmod='2012-03-14T00:00:00+00:00'
        #print r.timestamp
        self.assertEqual( r.lastmod, '2012-03-14T00:00:00Z' )
        r.lastmod='2012-03-14T00:00:00-00:00'
        #print r.timestamp
        self.assertEqual( r.lastmod, '2012-03-14T00:00:00Z' )
        r.lastmod='2012-03-14T18:37:36Z'
        #print r.timestamp
        self.assertEqual( r.lastmod, '2012-03-14T18:37:36Z' )

    def test06_str(self):
        r1 = Resource('abc',lastmod='2012-01-01')
        self.assertTrue( re.match( r"\[ abc \| 2012-01-01T", str(r1) ) )

    def test07_repr(self):
        r1 = Resource('def',lastmod='2012-01-01')
        self.assertEqual( repr(r1), "{'uri': 'def', 'timestamp': 1325376000}" )

    def test08_multiple_hashes(self):
        r1 = Resource('abcd')
        r1.md5 = "some_md5"
        r1.sha1 = "some_sha1"
        r1.sha256 = "some_sha256"
        self.assertEqual( r1.md5, "some_md5" )
        self.assertEqual( r1.sha1, "some_sha1" )
        self.assertEqual( r1.sha256, "some_sha256" )
        self.assertEqual( r1.hash, "md5:some_md5 sha-1:some_sha1 sha-256:some_sha256" )
        r2 = Resource('def')
        r2.hash = "md5:ddd"
        self.assertEqual( r2.md5, 'ddd' )
        self.assertEqual( r2.sha1, None )
        r2.hash = "sha-1:eee"
        self.assertEqual( r2.md5, None )
        self.assertEqual( r2.sha1, 'eee' )
        r2.hash = "md5:fff sha-1:eee sha-256:ggg"
        self.assertEqual( r2.md5, 'fff' )
        self.assertEqual( r2.sha1, 'eee' )
        self.assertEqual( r2.sha256, 'ggg' )

    def test09_changetypeerror(self):
        r1 = Resource('a')
        self.assertEqual( r1.change, None )
        r1.change = 'deleted'
        self.assertEqual( r1.change, 'deleted' )
        self.assertRaises( ChangeTypeError, Resource, 'a', change="bad" )
        # disable checking
        Resource.CHANGE_TYPES = False
        r1 = Resource( 'a', change="bad" )
        self.assertEqual( r1.change, 'bad' )

    def test10_md_at_roundtrips(self):
        r = Resource('a')
        r.md_at='2013-03-14'
        self.assertEqual( r.md_at, '2013-03-14T00:00:00Z' )
        r.md_at='2013-03-14T00:00:00+00:00'
        self.assertEqual( r.md_at, '2013-03-14T00:00:00Z' )
        r.md_at='2013-03-14T00:00:00-00:00'
        self.assertEqual( r.md_at, '2013-03-14T00:00:00Z' )
        r.md_at='2013-03-14T18:37:36Z'
        self.assertEqual( r.md_at, '2013-03-14T18:37:36Z' )

    def test11_md_completed_roundtrips(self):
        r = Resource('a')
        r.md_completed='2013-04-14'
        self.assertEqual( r.md_completed, '2013-04-14T00:00:00Z' )
        r.md_completed='2013-04-14T00:00:00+00:00'
        self.assertEqual( r.md_completed, '2013-04-14T00:00:00Z' )
        r.md_completed='2013-04-14T00:00:00-00:00'
        self.assertEqual( r.md_completed, '2013-04-14T00:00:00Z' )
        r.md_completed='2013-04-14T18:37:36Z'
        self.assertEqual( r.md_completed, '2013-04-14T18:37:36Z' )

    def test12_timevalues(self):
        r = Resource(uri='tv',
                     lastmod="2000-01-01",
                     md_at="2000-01-02",
                     md_completed="2000-01-03",
                     md_from="2000-01-04",
                     md_until="2000-01-05")
        self.assertEqual( r.lastmod,   '2000-01-01T00:00:00Z' )
        self.assertEqual( r.md_at,        '2000-01-02T00:00:00Z' )
        self.assertEqual( r.md_completed, '2000-01-03T00:00:00Z' )
        self.assertEqual( r.md_from,      '2000-01-04T00:00:00Z' )
        self.assertEqual( r.md_until,     '2000-01-05T00:00:00Z' )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResource)
    unittest.TextTestRunner(verbosity=2).run(suite)
