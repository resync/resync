import sys
import unittest
import StringIO

sys.path.insert(0, '.')

from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.sitemap import Sitemap, SitemapIndexError, SitemapParseError

import subprocess

def run_resync(args):
    args.insert(0,'bin/resync')
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    return(out)

class TestClientLinkOptions(unittest.TestCase):

    def test01_no_links(self):
        xml = run_resync(['--resourcelist',
                          'http://example.org/t','resync/test/testdata/dir1'])
        rl = ResourceList()
        rl.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(rl), 2 )
        self.assertEqual( rl.link('describedby'), None )

    def test02_no_links(self):
        xml = run_resync(['--resourcelist','--describedby-link=a',
                          '--capabilities-link=b','--up-link=c',
                          'http://example.org/t','resync/test/testdata/dir1'])
        rl = ResourceList()
        rl.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(rl), 2 )
        self.assertNotEqual( rl.link('describedby'), None )
        self.assertEqual( rl.link('describedby')['href'], 'a' )
        self.assertNotEqual( rl.link('resourcesync'), None )
        self.assertEqual( rl.link('resourcesync')['href'], 'b' )
        self.assertNotEqual( rl.link('up'), None )
        self.assertEqual( rl.link('up')['href'], 'c' )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientLinkOptions)
    unittest.TextTestRunner(verbosity=2).run(suite)
