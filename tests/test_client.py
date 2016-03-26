from tests.testcase_with_tmpdir import TestCase
from tests.capture_stdout import capture_stdout

import unittest
import re
import logging
from testfixtures import LogCapture
import sys
import os.path

from resync.client import Client, ClientFatalError
from resync.change_list import ChangeList

class TestClient(TestCase):

    @classmethod
    def extraSetUpClass(cls):
        logging.basicConfig(level=logging.INFO)

    def test01_make_resource_list_empty(self):
        c = Client()
        # No mapping is an error
        self.assertRaises( ClientFatalError, c.build_resource_list )

    def test02_bad_source_uri(self):
        c = Client()
        self.assertRaises( ClientFatalError, c.baseline_or_audit )
        c.set_mappings( ['http://example.org/bbb','/tmp/this_does_not_exist'] )
        self.assertRaises( ClientFatalError, c.baseline_or_audit )

    def test03_sitemap_uri(self):
        c = Client()
        c.set_mappings( ['http://example.org/c','/tmp/not_there_at_all'] )
        self.assertEqual( c.sitemap_uri('abcd1'), 'http://example.org/c/abcd1' )
        self.assertEqual( c.sitemap_uri('/abcd2'), '/abcd2' )
        self.assertEqual( c.sitemap_uri('scheme:/abcd3'), 'scheme:/abcd3' )

    def test06_write_capability_list(self):
        c = Client()
        with capture_stdout() as capturer:
            c.write_capability_list( { 'a':'uri_a', 'b':'uri_b' } )
        self.assertTrue( re.search(r'<urlset ',capturer.result) )
        self.assertTrue( re.search(r'<rs:md capability="capabilitylist" />',capturer.result) )
        self.assertTrue( re.search(r'<url><loc>uri_a</loc><rs:md capability="a"',capturer.result) )
        self.assertTrue( re.search(r'<url><loc>uri_b</loc><rs:md capability="b"',capturer.result) )

    def test07_write_source_description(self):
        c = Client()
        with capture_stdout() as capturer:
            c.write_source_description( [ 'a','b','c' ] )
        #print capturer.result
        self.assertTrue( re.search(r'<urlset ',capturer.result) )
        self.assertTrue( re.search(r'<rs:md capability="description" />',capturer.result) )
        self.assertTrue( re.search(r'<url><loc>a</loc><rs:md capability="capabilitylist" /></url>',capturer.result) )
        self.assertTrue( re.search(r'<url><loc>b</loc><rs:md capability="capabilitylist" /></url>',capturer.result) )

    def test20_parse_document(self):
        # Key property of the parse_document() method is that it parses the
        # document and identifies its type
        c = Client()
        with capture_stdout() as capturer:
            c.sitemap_name='tests/testdata/examples_from_spec/resourcesync_ex_1.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed resourcelist document with 2 entries',capturer.result) )
        with capture_stdout() as capturer:
            c.sitemap_name='tests/testdata/examples_from_spec/resourcesync_ex_17.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed resourcedump document with 3 entries',capturer.result) )
        with capture_stdout() as capturer:
            c.sitemap_name='tests/testdata/examples_from_spec/resourcesync_ex_19.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed changelist document with 4 entries',capturer.result) )
        with capture_stdout() as capturer:
            c.sitemap_name='tests/testdata/examples_from_spec/resourcesync_ex_22.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed changedump document with 3 entries',capturer.result) )

    def test40_write_resource_list_mappings(self):
        c = Client()
        c.set_mappings( ['http://example.org/','tests/testdata/'] )
        # with no explicit paths seting the mapping will be used
        with capture_stdout() as capturer:
            c.write_resource_list()
        #sys.stderr.write(capturer.result)
        self.assertTrue( re.search(r'<rs:md at="\S+" capability="resourcelist"', capturer.result ) )
        self.assertTrue( re.search(r'<url><loc>http://example.org/dir1/file_a</loc>', capturer.result ) )
        self.assertTrue( re.search(r'<url><loc>http://example.org/dir1/file_b</loc>', capturer.result ) )
        self.assertTrue( re.search(r'<url><loc>http://example.org/dir2/file_x</loc>', capturer.result ) )

    def test41_write_resource_list_path(self):
        c = Client()
        c.set_mappings( ['http://example.org/','tests/testdata/'] )
        # with an explicit paths setting only the specified paths will be included
        with capture_stdout() as capturer:
            c.write_resource_list(paths='tests/testdata/dir1')
        self.assertTrue( re.search(r'<rs:md at="\S+" capability="resourcelist"', capturer.result ) )
        self.assertTrue( re.search(r'<url><loc>http://example.org/dir1/file_a</loc>', capturer.result ) )
        self.assertTrue( re.search(r'<url><loc>http://example.org/dir1/file_b</loc>', capturer.result ) )
        self.assertFalse( re.search(r'<url><loc>http://example.org/dir2/file_x</loc>', capturer.result ) )
        # Travis CI does not preserve timestamps from github so test here for the file
        # size but not the datestamp
        #self.assertTrue( re.search(r'<url><loc>http://example.org/dir1/file_a</loc><lastmod>[\w\-:]+</lastmod><rs:md length="20" /></url>', capturer.result ) )
        #self.assertTrue( re.search(r'<url><loc>http://example.org/dir1/file_b</loc><lastmod>[\w\-:]+</lastmod><rs:md length="45" /></url>', capturer.result ) )

    def test46_write_capability_list(self):
        c = Client()
        caps = {'resourcelist': 'http://a.b/rl',
                'changelist': 'http://a.b/cl'}
        # to STDOUT
        with capture_stdout() as capturer:
            c.write_capability_list(capabilities=caps)
        self.assertTrue( re.search(r'http://a.b/rl', capturer.result ) )
        # to file (just check that something is written)
        outfile = os.path.join(self.tmpdir,'cl_out.xml')
        c.write_capability_list(capabilities=caps, outfile=outfile)
        self.assertTrue( os.path.getsize(outfile)>100 )

    def test47_write_source_description(self):
        c = Client()
        # to STDOUT
        with capture_stdout() as capturer:
            c.write_source_description(capability_lists=['http://a.b/'], links=[{'rel':'c','href':'d'}])
        self.assertTrue( re.search(r'http://a.b/', capturer.result ) )
        # to file (just check that something is written)
        outfile = os.path.join(self.tmpdir,'sd_out.xml')
        c.write_source_description(capability_lists=['http://a.b/'], outfile=outfile, links=[{'rel':'c','href':'d'}])
        self.assertTrue( os.path.getsize(outfile)>100 )

    def test48_write_dump_if_requested(self):
        c = Client()
        # no dump file
        self.assertFalse( c.write_dump_if_requested( ChangeList(), None ) )
        # with dump file
        with capture_stdout() as capturer:
            c.write_dump_if_requested(ChangeList(),'/tmp/a_file')
        self.assertTrue( re.search(r'FIXME', capturer.result) )

    def test49_read_reference_resource_list(self):
        c = Client()
        with capture_stdout() as capturer:
            rl = c.read_reference_resource_list('tests/testdata/examples_from_spec/resourcesync_ex_1.xml')
        self.assertEqual( len(rl), 2 )
        self.assertEqual( '', capturer.result )
        c.verbose = True
        with capture_stdout() as capturer:
            rl = c.read_reference_resource_list('tests/testdata/examples_from_spec/resourcesync_ex_1.xml')
        self.assertEqual( len(rl), 2 )
        self.assertTrue( re.search(r'http://example.com/res2', capturer.result) )
        c.verbose = True
        c.max_sitemap_entries = 1
        with capture_stdout() as capturer:
            rl = c.read_reference_resource_list('tests/testdata/examples_from_spec/resourcesync_ex_1.xml')
        self.assertEqual( len(rl), 2 )
        self.assertTrue( re.search(r'http://example.com/res1', capturer.result) )
        self.assertTrue( re.search(r'Showing first 1 entries', capturer.result) )
        self.assertFalse( re.search(r'http://example.com/res2', capturer.result) )

    def test50_log_status(self):
        c = Client()
        with LogCapture() as lc:
            c.logger = logging.getLogger('resync.client')
            c.log_status()
            self.assertEqual( lc.records[-1].msg,
                              'Status:         IN SYNC (created=0, updated=0, deleted=0)' )
            c.log_status(created=123,updated=456,deleted=789)
            self.assertEqual( lc.records[-1].msg,
                              'Status:         IN SYNC (created=123, updated=456, deleted=789)' )
            c.log_status(incremental=True)
            self.assertEqual( lc.records[-1].msg,
                              'Status:      NO CHANGES (created=0, updated=0, deleted=0)' )
            c.log_status(audit=True)
            self.assertEqual( lc.records[-1].msg,
                              'Status:         IN SYNC (to create=0, to update=0, to delete=0)' )
            c.log_status(in_sync=False, audit=True)
            self.assertEqual( lc.records[-1].msg,
                              'Status:     NOT IN SYNC (to create=0, to update=0, to delete=0)' )
            c.log_status(in_sync=False, audit=False, to_delete=1)
            self.assertEqual( lc.records[-1].msg,
                              'Status:     PART SYNCED (created=0, updated=0, to delete (--delete)=1)' )
            c.log_status(in_sync=False, audit=False, to_delete=1, incremental=1)
            self.assertEqual( lc.records[-1].msg,
                              'Status:    PART APPLIED (created=0, updated=0, to delete (--delete)=1)' )
            c.log_status(in_sync=False)
            self.assertEqual( lc.records[-1].msg,
                              'Status:          SYNCED (created=0, updated=0, deleted=0)' )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
