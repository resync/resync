import unittest
import re
from resync.w3c_datetime import str_to_datetime, datetime_to_str

def rt(dts):
    """ Do simple round-trip """
    return( datetime_to_str(str_to_datetime( dts )) )

class TestW3cDatetime(unittest.TestCase):

    def test1_datetime_to_str(self):
        """Writing..."""
        self.assertEqual( datetime_to_str(0), "1970-01-01T00:00:00Z" )
        self.assertEqual( datetime_to_str(0.000001), "1970-01-01T00:00:00.000001Z" )
        self.assertEqual( datetime_to_str(0.1), "1970-01-01T00:00:00.100000Z" )
        self.assertEqual( datetime_to_str(1), "1970-01-01T00:00:01Z" )
        self.assertEqual( datetime_to_str(60), "1970-01-01T00:01:00Z" )
        self.assertEqual( datetime_to_str(60*60), "1970-01-01T01:00:00Z" )
        self.assertEqual( datetime_to_str(60*60*24), "1970-01-02T00:00:00Z" )
        self.assertEqual( datetime_to_str(60*60*24*31), "1970-02-01T00:00:00Z" )
        self.assertEqual( datetime_to_str(60*60*24*365), "1971-01-01T00:00:00Z" )
        #
        self.assertEqual( datetime_to_str(1234567890), "2009-02-13T23:31:30Z" )

    def test2_str_to_datetime(self):
        """Reading..."""
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00Z"), 0 )
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00.000Z"), 0 )
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00+00:00"), 0 )
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00-00:00"), 0 )
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00.000001Z"), 0.000001 )
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00.1Z"), 0.1 )
        self.assertEqual( str_to_datetime("1970-01-01T00:00:00.100000Z"), 0.1 )
        #
        self.assertEqual( str_to_datetime("2009-02-13T23:31:30Z"), 1234567890 )

    def test2_same(self):
        """Datetime values that are the same"""
        astr = '2012-01-01T00:00:00Z'
        a = str_to_datetime( astr )
        for bstr in ('2012',
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
            b =  str_to_datetime( bstr )
            self.assertEqual( a, b, ('%s (%f) == %s (%f)' % (astr,a,bstr,b)) )

    def test4_bad_str(self):
        # Bad formats
        self.assertRaises( ValueError, str_to_datetime, "bad_lastmod" )
        self.assertRaises( ValueError, str_to_datetime, "" )
        self.assertRaises( ValueError, str_to_datetime, "2012-13-01" )
        self.assertRaises( ValueError, str_to_datetime, "2012-12-32" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T10:10:60" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T10:10:59.9x" )
        # Valid ISO8601 but not allowed in W3C Datetime
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T01:01:01" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01 01:01:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T01:01:01+0000" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T01:01:01-1000" )
        # Bad values
        self.assertRaises( ValueError, str_to_datetime, "2012-00-01T01:01:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-13-01T01:01:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-00T01:01:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-32T01:01:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-13-01T24:01:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-13-01T00:60:01Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-13-01T00:00:60Z" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T01:01:01+99:00" )
        self.assertRaises( ValueError, str_to_datetime, "2012-11-01T01:01:01-25:00" )
   
    def test5_roundtrips(self):
        self.assertEqual( rt('2012-03-14T00:00:00+00:00'),
                             '2012-03-14T00:00:00Z')
        self.assertEqual( rt('2012-03-14T00:00:00-00:00'),
                             '2012-03-14T00:00:00Z')
        self.assertEqual( rt('2012-03-14T11:00:00-11:00' ),
                             '2012-03-14T00:00:00Z')
        self.assertEqual( rt('2012-03-14T18:37:36Z' ),
                             '2012-03-14T18:37:36Z' )
        self.assertEqual( rt('2012-03-14T18:37:36+00:10' ),
                             '2012-03-14T18:47:36Z' )
        self.assertEqual( rt('2012-03-14T18:37:36-01:01' ),
                             '2012-03-14T17:36:36Z' )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestW3cDatetime)
    unittest.TextTestRunner(verbosity=2).run(suite)
