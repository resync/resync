import sys
import unittest
import StringIO
import tempfile
import os.path
import shutil

from resync.list_base_with_index import ListBaseIndexError
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
        rl.read('tests/testdata/sitemapindex2/sitemap.xml')
        self.assertEqual( len(rl.resources), 17, '17 resources from 3 sitemaps listed')
        sr = sorted(rl.uris())
        self.assertEqual( sr[0], 'http://localhost:8888/resources/1' )
        self.assertEqual( sr[1], 'http://localhost:8888/resources/10' )
        self.assertEqual( sr[2], 'http://localhost:8888/resources/100' )
        self.assertEqual( sr[3], 'http://localhost:8888/resources/1000' )
        self.assertEqual( sr[16], 'http://localhost:8888/resources/826' )

    def test_02_read_with_mapper(self):
        rl = ResourceList()
        rl.mapper = Mapper(['http://localhost/=tests/testdata/sitemapindex2/'])
        rl.read('tests/testdata/sitemapindex2/sitemap_mapper.xml')
        self.assertEqual( len(rl.resources), 17, '17 resources from 3 sitemaps listed')
        sr = sorted(rl.uris())
        self.assertEqual( sr[0], 'http://localhost:8888/resources/1' )
        self.assertEqual( sr[1], 'http://localhost:8888/resources/10' )
        self.assertEqual( sr[2], 'http://localhost:8888/resources/100' )
        self.assertEqual( sr[3], 'http://localhost:8888/resources/1000' )
        self.assertEqual( sr[16], 'http://localhost:8888/resources/826' )

    def test_11_write_multifile(self):
        tempdir = tempfile.mkdtemp(prefix='test_resource_list_multifile')
        rl = ResourceList()
        rl.mapper = Mapper(['http://localhost/=%s/' % (tempdir)])
        rl.add( Resource( uri='http://localhost/a' ) )
        rl.add( Resource( uri='http://localhost/b' ) )
        rl.add( Resource( uri='http://localhost/c' ) )
        rl.add( Resource( uri='http://localhost/d' ) )
        rl.max_sitemap_entries = 2
        # first try writing without mutlifile allowed
        rl.allow_multifile = False
        self.assertRaises( ListBaseIndexError, rl.write, basename=os.path.join(tempdir,'sitemap.xml') )
        # second actually do it
        rl.allow_multifile = True
        rl.write( basename = os.path.join(tempdir,'sitemap.xml') )
        # check the two component sitemaps
        rl1 = ResourceList()
        rl1.read( os.path.join(tempdir,'sitemap00000.xml') )
        self.assertEquals( len(rl1), 2 )
        self.assertEquals( rl1.capability, 'resourcelist' )
        self.assertFalse( rl1.sitemapindex )
        i = iter(rl1)
        self.assertEquals( i.next().uri, 'http://localhost/a' )
        self.assertEquals( i.next().uri, 'http://localhost/b' )
        rl2 = ResourceList()
        rl2.read( os.path.join(tempdir,'sitemap00001.xml') )
        self.assertEquals( len(rl2), 2 )
        i = iter(rl2)
        self.assertEquals( i.next().uri, 'http://localhost/c' )
        self.assertEquals( i.next().uri, 'http://localhost/d' )
        # check the sitemapindex (read just as index)
        rli = ResourceList()
        rli.read( os.path.join(tempdir,'sitemap.xml'), index_only=True )
        self.assertEquals( len(rli), 2 )
        i = iter(rli)
        self.assertEquals( rli.capability, 'resourcelist' )
        self.assertTrue( rli.sitemapindex )
        self.assertEquals( i.next().uri, 'http://localhost/sitemap00000.xml' )
        self.assertEquals( i.next().uri, 'http://localhost/sitemap00001.xml' )
        # check the sitemapindex and components
        rli = ResourceList( mapper=rl.mapper )
        rli.read( os.path.join(tempdir,'sitemap.xml') )
        self.assertEquals( len(rli), 4 )
        self.assertEquals( rli.capability, 'resourcelist' )
        self.assertFalse( rli.sitemapindex )
        i = iter(rli)
        self.assertEquals( i.next().uri, 'http://localhost/a' )
        self.assertEquals( i.next().uri, 'http://localhost/b' )
        self.assertEquals( i.next().uri, 'http://localhost/c' )
        self.assertEquals( i.next().uri, 'http://localhost/d' )
        # cleanup tempdir
        shutil.rmtree(tempdir)

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResourceListMultifile)
    unittest.TextTestRunner(verbosity=2).run(suite)
