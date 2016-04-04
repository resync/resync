from tests.capture_stdout import capture_stdout

import unittest
import re
import logging
import sys

from resync.client import Client, ClientFatalError
from resync.capability_list import CapabilityList
from resync.explorer import Explorer, XResource, HeadResponse, ExplorerQuit
from resync.resource import Resource


class TestExplorer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)

    def test01_create(self):
        # dumb test that we can create Exporer object
        e = Explorer()
        self.assertTrue( e )

    def test01_xresource(self):
        x = XResource( uri='abc', acceptable_capabilities=[1,2],
                       checks=[3,4], context='http://example.org/def' )
        self.assertEqual( x.uri, 'http://example.org/abc' )
        self.assertEqual( x.acceptable_capabilities, [1,2] )
        self.assertEqual( x.checks, [3,4] )

    def test02_head_response(self):
        hr = HeadResponse()
        self.assertEqual( hr.status_code, None )
        self.assertEqual( len(hr.headers), 0)

    def test03_explorer_quit(self):
        eq = ExplorerQuit()
        self.assertTrue( isinstance(eq, Exception) )

    def test04_explore(self):
        e = Explorer()
        e.sitemap_name = 'tests/testdata/explore1/caps1.xml'
        with capture_stdout() as capturer:
            # IOError generated from attempt to read stdin
            e.fake_input = 'q'
            e.explore()
        self.assertTrue( re.search(r'resync-explorer done', capturer.result) )

    def test05_explore_uri(self):
        e = Explorer()
        with capture_stdout() as capturer:
            e.fake_input = 'q'
            self.assertRaises( ExplorerQuit, e.explore_uri,
                               XResource('tests/testdata/explore1/caps1.xml') )
        self.assertTrue( re.search(r'Reading tests/testdata/explore1/caps1.xml',
                                   capturer.result) )
        self.assertTrue( re.search(r'Parsed capabilitylist document with 4 entries:',
                                   capturer.result) )

    def test06_explore_show_summary(self):
        e = Explorer()
        # file that exists with matching
        with capture_stdout() as capturer:
            e.explore_show_summary( list=CapabilityList() )
        self.assertTrue( re.search(r'Parsed \(unknown capability\) document with 0 entries:',
                                   capturer.result) )
        # dummy capabilities object and display
        cl = CapabilityList()
        cl.add( Resource('uri:resourcelist') )
        cl.add( Resource('uri:changelist') )
        with capture_stdout() as capturer:
            e.explore_show_summary(cl,False,[])
        self.assertTrue( re.search(r'Parsed \(unknown capability\) document with 2 entries:',capturer.result) )
        self.assertTrue( re.search(r'\[1\] uri:changelist',capturer.result) )
        self.assertTrue( re.search(r'\[2\] uri:resourcelist',capturer.result) )
 
    def test07_explore_show_head(self):
        e = Explorer()
        # file that exists with matching
        with capture_stdout() as capturer:
            e.explore_show_head( uri='tests/testdata/dir1/file_a',
                                 check_headers={ 'content-length': 20,
                                                'unknown': 'abc' } )
        self.assertTrue( re.search(r'HEAD tests/testdata/dir1/file_a', capturer.result) )
        self.assertTrue( re.search(r'content-length: 20 MATCHES EXPECTED VALUE', capturer.result) )
        # same file, bad header check
        with capture_stdout() as capturer:
            e.explore_show_head( 'tests/testdata/dir1/file_a',
                                 check_headers={ 'content-length': 99 } )
        self.assertTrue( re.search(r'HEAD tests/testdata/dir1/file_a', capturer.result) )
        self.assertTrue( re.search(r'content-length: 20 EXPECTED 99', capturer.result) )
        # file that does not exist
        with capture_stdout() as capturer:
            e.explore_show_head( 'tests/testdata/does_not_exist' )
        self.assertTrue( re.search(r'HEAD tests/testdata/does_not_exist', capturer.result) )
        self.assertTrue( re.search(r'status: 404', capturer.result) )

    def test08_head_on_file(self):
        e = Explorer()
        r1 = e.head_on_file('tests/testdata/does_not_exist')
        self.assertEqual( r1.status_code, '404' )
        r2 = e.head_on_file('tests/testdata/dir1/file_a')
        self.assertEqual( r2.status_code, '200' )
        self.assertTrue( re.match(r'^\d\d\d\d\-\d\d\-\d\d', r2.headers['last-modified']) )
        self.assertEqual( r2.headers['content-length'], 20 )

    def test09_allowed_entries(self):
        e = Explorer()
        self.assertEqual( e.allowed_entries('capabilitylistindex'), [] )
        self.assertEqual( e.allowed_entries('resourcelistindex'), ['resourcelist'] )
        self.assertEqual( e.allowed_entries('changelist-archive'), ['changelist'] )
        self.assertEqual( e.allowed_entries('description'),['capabilitylist'] )
        self.assertEqual( len(e.allowed_entries('capabilitylist')), 8 )
        self.assertEqual( e.allowed_entries('unknown'),[] )

    def test10_expand_relative_uri(self):
        e = Explorer()
        with capture_stdout() as capturer:
            uri = e.expand_relative_uri('https://example.org/ctx','abc')
        self.assertEqual( uri, 'https://example.org/abc' )
        self.assertTrue( re.search(r'expanded relative URI', capturer.result) )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExplorer)
    unittest.TextTestRunner(verbosity=2).run(suite)
