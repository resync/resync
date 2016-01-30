import sys
import unittest
import StringIO

sys.path.insert(0, '.')

from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.capability_list import CapabilityList
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
                          'http://example.org/t','tests/testdata/dir1'])
        rl = ResourceList()
        rl.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(rl), 2 )
        self.assertEqual( rl.link('describedby'), None )

    def test02_resource_list_links(self):
        xml = run_resync(['--resourcelist',
                          '--describedby-link=a',
                          '--sourcedescription-link=b', #will be ignored
                          '--capabilitylist-link=c',
                          'http://example.org/t','tests/testdata/dir1'])
        rl = ResourceList()
        rl.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(rl), 2 )
        self.assertNotEqual( rl.link('describedby'), None )
        self.assertEqual( rl.link('describedby')['href'], 'a' )
        self.assertNotEqual( rl.link('up'), None )
        self.assertEqual( rl.link('up')['href'], 'c' )

    def test03_capability_list_links(self):
        xml = run_resync(['--capabilitylist=resourcelist=rl,changedump=cd',
                          '--describedby-link=a',
                          '--sourcedescription-link=b',
                          '--capabilitylist-link=c' ]) #will be ignored
        capl = CapabilityList()
        capl.parse(fh=StringIO.StringIO(xml))
        self.assertEqual( len(capl), 2 )
        self.assertNotEqual( capl.link('describedby'), None )
        self.assertEqual( capl.link('describedby')['href'], 'a' )
        self.assertNotEqual( capl.link('up'), None )
        self.assertEqual( capl.link('up')['href'], 'b' )

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientLinkOptions)
    unittest.TextTestRunner(verbosity=2).run(suite)
