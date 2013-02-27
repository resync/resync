import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.mapper import Mapper

# etree gives ParseError in 2.7, ExpatError in 2.6
etree_error_class = None
if (sys.version_info < (2,7)):
    from xml.parsers.expat import ExpatError
    etree_error_class = ExpatError
else:
    from xml.etree.ElementTree import ParseError
    etree_error_class = ParseError

class TestResourceListMultifile(unittest.TestCase):

    def test_01_read_local_filenames(self):
        rl = ResourceList()
        rl.read('resync/test/testdata/sitemapindex2/sitemap.xml')
        self.assertEqual( len(rl.resources), 17, '17 resources from 3 sitemaps listed')
        sr = sorted(rl.uris())
        self.assertEqual( sr[0], 'http://localhost:8888/resources/1' )
        self.assertEqual( sr[1], 'http://localhost:8888/resources/10' )
        self.assertEqual( sr[2], 'http://localhost:8888/resources/100' )
        self.assertEqual( sr[3], 'http://localhost:8888/resources/1000' )
        self.assertEqual( sr[16], 'http://localhost:8888/resources/826' )

    def test_02_read_with_mapper(self):
        rl = ResourceList()
        rl.mapper = Mapper(['http://localhost/=resync/test/testdata/sitemapindex2/'])
        rl.read('resync/test/testdata/sitemapindex2/sitemap_mapper.xml')
        self.assertEqual( len(rl.resources), 17, '17 resources from 3 sitemaps listed')
        sr = sorted(rl.uris())
        self.assertEqual( sr[0], 'http://localhost:8888/resources/1' )
        self.assertEqual( sr[1], 'http://localhost:8888/resources/10' )
        self.assertEqual( sr[2], 'http://localhost:8888/resources/100' )
        self.assertEqual( sr[3], 'http://localhost:8888/resources/1000' )
        self.assertEqual( sr[16], 'http://localhost:8888/resources/826' )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResourceListMultifile)
    unittest.TextTestRunner(verbosity=2).run(suite)
