import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.sitemap import Sitemap

class TestSitemap(unittest.TestCase):

    def test_all_simple(self):
        """Just try to read each one"""
        for ex in ("ex_2_1.xml","ex_2_2.xml","ex_2_3.xml","ex_2_4.xml",
                   "ex_2_5.xml","ex_2_6.xml","ex_2_7.xml",
                   "ex_4_1.xml","ex_4_2.xml","ex_4_3.xml",
                   "ex_5_1.xml","ex_5_2.xml","ex_5_3.xml",
                   "ex_6_1.xml",
                   "ex_7_1.xml","ex_7_2.xml","ex_7_3.xml",
                   "ex_8_1.xml","ex_8_2.xml","ex_8_3.xml","ex_8_4.xml",
                   "ex_8_5.xml","ex_8_6.xml","ex_8_7.xml","ex_8_8.xml",
                   "ex_8_9.xml",
                   "ex_9_1.xml","ex_9_2.xml","ex_9_3.xml",
                   "ex_10_1.xml","ex_10_2.xml"):
            s=Sitemap()
            uri = 'resync/test/testdata/examples_from_spec/%s' % (ex)
            si = s.read( uri=uri, index_only=True )

    def test_ex_2_1(self):
        """ex2_1 is a simple resource_list with 2 resources, no metadata"""
        rl=ResourceList()
        rl.parse(uri='resync/test/testdata/examples_from_spec/ex_2_1.xml')
        self.assertEqual( rl.capability, 'resourcelist' )
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( rl.resources['http://example.com/res1'].lastmod, None )

    def test_ex_2_2(self):
        """ex_2_2 is a simple resource_list with 2 resources, some metadata"""
        rl=ResourceList()
        rl.parse(uri='resync/test/testdata/examples_from_spec/ex_2_2.xml')
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( rl.resources['http://example.com/res1'].lastmod, '2013-01-02T13:00:00Z' )
        self.assertEqual( rl.resources['http://example.com/res2'].lastmod, '2013-01-02T14:00:00Z' )
        self.assertEqual( rl.resources['http://example.com/res1'].md5, '1584abdf8ebdc9802ac0c6a7402c03b6' )
        self.assertEqual( rl.resources['http://example.com/res2'].md5, '1e0d5cb8ef6ba40c99b14c0237be735e' )

    def test_ex_2_3(self):
        """ex_2_3 is a simple change_list with 2 resources"""
        cl=ChangeList()
        cl.parse('resync/test/testdata/examples_from_spec/ex_2_3.xml')
        self.assertEqual( len(cl.resources), 2, '2 resources')
        sms = sorted(cl.uris())
        self.assertEqual( sms, ['http://example.com/res2.pdf','http://example.com/res3.tiff'] )
        self.assertEqual( cl.resources[0].lastmod, '2013-01-02T13:00:00Z' )
        self.assertEqual( cl.resources[1].lastmod, '2013-01-02T18:00:00Z' )
        self.assertEqual( cl.resources[0].change, 'updated' )
        self.assertEqual( cl.resources[1].change, 'deleted' )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSitemap)
    unittest.TextTestRunner(verbosity=2).run(suite)
