import unittest
import re
from resync.resource import Resource

class TestResource(unittest.TestCase):

    def test1a_same(self):
        r1 = Resource('a')
        r2 = Resource('a')
        self.assertEqual( r1, r1 )
        self.assertEqual( r1, r2 )

    def test1b_same(self):
        r1 = Resource(uri='a',timestamp=1234.0)
        r2 = Resource(uri='a',timestamp=1234.0)
        self.assertEqual( r1, r1 )
        self.assertEqual( r1, r2 )

    def test1c_same(self):
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

    def test1d_same(self):
        """Same with slight timestamp diff"""
        r1 = Resource('a')
        r1.lastmod='2012-01-02T01:02:03Z'
        r2 = Resource('a')
        r2.lastmod='2012-01-02T01:02:03.99Z'
        self.assertNotEqual( r1.timestamp, r2.timestamp )
        self.assertEqual( r1, r2 )

    def test2a_diff(self):
        r1 = Resource('a')
        r2 = Resource('b')
        self.assertNotEqual(r1,r2)

    def test2b_diff(self):
        r1 = Resource('a',lastmod='2012-01-11')
        r2 = Resource('a',lastmod='2012-01-22')
        #print 'r1 == r2 : '+str(r1==r2)
        self.assertNotEqual( r1, r2 )

    def test4_bad_lastmod(self):
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
   
    def test5_lastmod_roundtrips(self):
        r = Resource('a')
        r.lastmod='2012-03-14'
        self.assertEqual( r.lastmod, '2012-03-14T00:00:00Z' )
        r.lastmod='2012-03-14T00:00:00+00:00'
        print r.timestamp
        self.assertEqual( r.lastmod, '2012-03-14T00:00:00Z' )
        r.lastmod='2012-03-14T00:00:00-00:00'
        print r.timestamp
        self.assertEqual( r.lastmod, '2012-03-14T00:00:00Z' )
        r.lastmod='2012-03-14T18:37:36Z'
        print r.timestamp
        self.assertEqual( r.lastmod, '2012-03-14T18:37:36Z' )

    def test6_str(self):
        r1 = Resource('abc',lastmod='2012-01-01')
        self.assertTrue( re.match( r"\[ abc \| 2012-01-01T", str(r1) ) )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResource)
    unittest.TextTestRunner(verbosity=2).run(suite)
