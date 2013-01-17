import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resourcelist import ResourceList
from resync.sitemap import Sitemap

class TestSitemap(unittest.TestCase):

    def test_ex2_1(self):
        """ex2_1 is a simple resourcelist with 2 resources, no metadata"""
        s=Sitemap()
        fh=open('resync/test/testdata/examples_from_spec/ex2_1.xml')
        si = s.resourcelist_parse_xml( fh=fh )
        self.assertEqual( len(si.resources), 2, '2 resources')
        sms = sorted(si.resources.keys())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( si.resources['http://example.com/res1'].lastmod, None )

    def test_ex2_2(self):
        """ex2_2 is a simple resourcelist with 2 resources, some metadata"""
        s=Sitemap()
        fh=open('resync/test/testdata/examples_from_spec/ex2_2.xml')
        si = s.resourcelist_parse_xml( fh=fh )
        self.assertEqual( len(si.resources), 2, '2 resources')
        sms = sorted(si.resources.keys())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( si.resources['http://example.com/res1'].lastmod, '2013-01-02T14:00:00Z' )
        self.assertEqual( si.resources['http://example.com/res2'].lastmod, '2013-01-02T13:00:00Z' )
        self.assertEqual( si.resources['http://example.com/res1'].md5, '1584abdf8ebdc9802ac0c6a7402c03b6' )
        self.assertEqual( si.resources['http://example.com/res2'].md5, '1e0d5cb8ef6ba40c99b14c0237be735e' )

    def test_ex2_3(self):
        """ex2_3 is a simple changelist with 2 resources"""
        s=Sitemap()
        fh=open('resync/test/testdata/examples_from_spec/ex2_3.xml')
        si = s.resourcelist_parse_xml( fh=fh )
        self.assertEqual( len(si.resources), 2, '2 resources')
        sms = sorted(si.resources.keys())
        self.assertEqual( sms, ['http://example.com/res2.pdf','http://example.com/res3.tiff'] )
        self.assertEqual( si.resources['http://example.com/res2.pdf'].lastmod, '2013-01-02T18:00:00Z' )
        self.assertEqual( si.resources['http://example.com/res3.tiff'].lastmod, '2013-01-02T13:00:00Z' )
        self.assertEqual( si.resources['http://example.com/res2.pdf'].change, 'updated' )
        self.assertEqual( si.resources['http://example.com/res3.tiff'].change, 'deleted' )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSitemap)
    unittest.TextTestRunner(verbosity=2).run(suite)
