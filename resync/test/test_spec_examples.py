import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.inventory import Inventory
from resync.sitemap import Sitemap

class TestSitemap(unittest.TestCase):

    def test_ex2_1(self):
        s=Sitemap()
        fh=open('resync/test/testdata/examples_from_spec/ex2_1.xml')
        si = s.inventory_parse_xml( fh=fh )
        self.assertEqual( len(si.resources), 2, '2 resources')
        sms = sorted(si.resources.keys())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( si.resources['http://example.com/res1'].lastmod, None )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSitemap)
    unittest.TextTestRunner(verbosity=2).run(suite)
