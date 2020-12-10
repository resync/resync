from .testlib import TestCase, capture_stdout, webserver

import unittest
import re
import logging
from testfixtures import LogCapture
import sys
import os.path

from resync.client import Client, ClientError, ClientFatalError
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.change_list import ChangeList

logging.basicConfig(level=logging.INFO)


class TestClient(TestCase):
    """Test cases for resync.client."""

    def test01_make_resource_list_empty(self):
        c = Client()
        # No mapping is an error
        self.assertRaises(ClientFatalError, c.build_resource_list)

    def test02_bad_source_uri(self):
        c = Client()
        self.assertRaises(ClientFatalError, c.baseline_or_audit)
        c.set_mappings(['http://example.org/bbb', '/tmp/this_does_not_exist'])
        self.assertRaises(ClientFatalError, c.baseline_or_audit)

    def test03_sitemap_uri(self):
        c = Client()
        c.set_mappings(['http://example.org/c', '/tmp/not_there_at_all'])
        self.assertEqual(c.sitemap_uri('abcd1'), 'http://example.org/c/abcd1')
        self.assertEqual(c.sitemap_uri('/abcd2'), '/abcd2')
        self.assertEqual(c.sitemap_uri('scheme:/abcd3'), 'scheme:/abcd3')

    def test04_read_resource_list(self):
        c = Client()
        rl = c.read_resource_list('tests/testdata/client/dir1/resourcelist.xml')
        self.assertEqual(len(rl), 3)
        rl = c.read_resource_list('file:tests/testdata/client/dir1/resourcelist.xml')
        self.assertEqual(len(rl), 3)
        self.assertEqual(len(rl), 3)
        self.assertRaises(ClientError, c.read_resource_list, 'file://tests/testdata/client/dir1/resourcelist.xml')
        self.assertRaises(ClientError, c.read_resource_list, 'file:///tests/testdata/client/dir1/resourcelist.xml')
        self.assertRaises(ClientError, c.read_resource_list, 'DOES_NOT_EXIST')

    def test05_find_resource_list(self):
        c = Client()
        # Filesystem tests
        c.set_mappings(['tests/testdata/find/find1', 'xxx'])
        self.assertEqual(c.find_resource_list().up, 'find1')
        c.set_mappings(['tests/testdata/find/find2', 'xxx'])
        self.assertEqual(c.find_resource_list().up, 'find2')
        c.set_mappings(['tests/testdata/find/find3', 'xxx'])
        self.assertEqual(c.find_resource_list().up, 'find3')
        # Tests requiring a server
        with webserver('tests/testdata/find', 'localhost', 9999):
            c.set_mappings(['http://localhost:9999/find1', 'xxx'])
            self.assertEqual(c.find_resource_list().up, 'find1')
            c.set_mappings(['http://localhost:9999/find2', 'xxx'])
            self.assertEqual(c.find_resource_list().up, 'find2')
            c.set_mappings(['http://localhost:9999/find3', 'xxx'])
            self.assertEqual(c.find_resource_list().up, 'find3')
        with webserver('tests/testdata/find/find1', 'localhost', 9999):
            c.set_mappings(['http://localhost:9999/data', 'xxx'])
            self.assertEqual(c.find_resource_list().up, 'find1')
        with webserver('tests/testdata/find/find3', 'localhost', 9999):
            c.set_mappings(['http://localhost:9999/data/data1', 'xxx'])
            self.assertEqual(c.find_resource_list().up, 'find3')

    def test10_baseline_or_audit(self):
        # FIXME - this is the guts of the client, tough to test, need to work
        # through more cases...
        c = Client()
        dst = os.path.join(self.tmpdir, 'dst_dir1')
        with webserver('tests/testdata/client', 'localhost', 9999):
            c.set_mappings(['http://localhost:9999/dir1', dst])
            # audit with empty dst, should say 3 to create
            with LogCapture() as lc:
                c.baseline_or_audit(audit_only=True)
                self.assertTrue(
                    re.match(r'Status:\s+NOT IN SYNC.*to create=3', lc.records[-2].msg))
                self.assertEqual(lc.records[-1].msg, 'Completed audit')
            # now do the sync
            with LogCapture() as lc:
                c.baseline_or_audit()
                self.assertTrue(
                    re.match(r'Status:\s+SYNCED.*created=3', lc.records[-2].msg))
                self.assertEqual(lc.records[-1].msg, 'Completed baseline sync')

    def test18_update_resource(self):
        c = Client()
        resource = Resource(uri='http://example.org/dir/2')
        filename = os.path.join(self.tmpdir, 'dir/resource2')
        # dryrun
        with LogCapture() as lc:
            c.dryrun = True
            c.logger = logging.getLogger('resync.client')
            n = c.update_resource(resource, filename)
            self.assertEqual(n, 0)
            self.assertTrue(
                lc.records[-1].msg.startswith('dryrun: would GET http://example.org/dir/2 '))
        c.dryrun = False
        with webserver('tests/testdata', 'localhost', 9999):
            # get from file uri that does not exist
            resource = Resource(uri='http://localhost:9999/i_do_not_exist')
            self.assertRaises(ClientFatalError,
                              c.update_resource, resource, filename)
            # get from file uri that does not exist but with c.ignore_failures to
            # log
            resource = Resource(uri='http://localhost:9999/i_do_not_exist')
            with LogCapture() as lc:
                c.logger = logging.getLogger('resync.client')
                c.ignore_failures = True
                n = c.update_resource(resource, filename)
                self.assertEqual(n, 0)
                self.assertTrue(
                    lc.records[-1].msg.startswith('Failed to GET http://localhost:9999/i_do_not_exist '))
            # get from file uri
            resource = Resource(uri='http://localhost:9999/examples_from_spec/resourcesync_ex_1.xml',
                                length=355, md5='abc',
                                timestamp=10)
            c.last_timestamp = 0
            with LogCapture() as lc:
                c.logger = logging.getLogger('resync.client')
                n = c.update_resource(resource, filename)
                self.assertEqual(n, 1)
                self.assertTrue(lc.records[-1].msg.startswith('Event: {'))
            # get from file uri with length and md5 warnings
            resource = Resource(uri='http://localhost:9999/examples_from_spec/resourcesync_ex_1.xml',
                                length=111, md5='abc',
                                timestamp=10)
            c.last_timestamp = 0
            with LogCapture() as lc:
                c.logger = logging.getLogger('resync.client')
                c.hashes = set(['md5'])
                n = c.update_resource(resource, filename)
                self.assertEqual(n, 1)
                self.assertTrue(lc.records[-1].msg.startswith('MD5 mismatch '))
                self.assertTrue(
                    lc.records[-2].msg.startswith('Downloaded size for '))
                self.assertTrue(lc.records[-3].msg.startswith('Event: {'))

    def test19_delete_resource(self):
        c = Client()
        resource = Resource(uri='http://example.org/1')
        filename = os.path.join(self.tmpdir, 'resource1')
        c.last_timestamp = 5
        # no delete, no timestamp update
        with LogCapture() as lc:
            c.logger = logging.getLogger('resync.client')
            n = c.delete_resource(resource, filename)
            self.assertEqual(n, 0)
            self.assertEqual(lc.records[-1].msg,
                             'nodelete: would delete http://example.org/1 (--delete to enable)')
            self.assertEqual(c.last_timestamp, 5)
        # no delete but timestamp update
        resource.timestamp = 10
        with LogCapture() as lc:
            c.logger = logging.getLogger('resync.client')
            n = c.delete_resource(resource, filename)
            self.assertEqual(n, 0)
            self.assertEqual(lc.records[-1].msg,
                             'nodelete: would delete http://example.org/1 (--delete to enable)')
            self.assertEqual(c.last_timestamp, 10)
        # allow delete but dryrun
        with LogCapture() as lc:
            c.dryrun = True
            c.logger = logging.getLogger('resync.client')
            n = c.delete_resource(resource, filename, allow_deletion=True)
            self.assertEqual(n, 0)
            self.assertTrue(
                lc.records[-1].msg.startswith('dryrun: would delete http://example.org/1'))
        c.dryrun = False
        # allow delete but no resource present
        with LogCapture() as lc:
            c.logger = logging.getLogger('resync.client')
            n = c.delete_resource(resource, filename, allow_deletion=True)
            self.assertEqual(n, 0)
            self.assertTrue(
                lc.records[-1].msg.startswith('Failed to DELETE http://example.org/1'))
        # successful deletion, first make file...
        with open(filename, 'w') as fh:
            fh.write('delete me')
            fh.close()
        with LogCapture() as lc:
            c.logger = logging.getLogger('resync.client')
            n = c.delete_resource(resource, filename, allow_deletion=True)
            self.assertEqual(n, 1)
            self.assertTrue(lc.records[-1].msg.startswith('Event: {'))
            self.assertTrue(
                lc.records[-2].msg.startswith('deleted: http://example.org/1 ->'))

    def test20_parse_document(self):
        # Key property of the parse_document() method is that it parses the
        # document and identifies its type
        c = Client()
        with capture_stdout() as capturer:
            c.sitemap_name = 'tests/testdata/examples_from_spec/resourcesync_ex_1.xml'
            c.parse_document()
        self.assertRegex(capturer.result, r'Parsed resourcelist document with 2 entries')
        with capture_stdout() as capturer:
            c.sitemap_name = 'tests/testdata/examples_from_spec/resourcesync_ex_17.xml'
            c.parse_document()
        self.assertRegex(capturer.result, r'Parsed resourcedump document with 3 entries')
        with capture_stdout() as capturer:
            c.sitemap_name = 'tests/testdata/examples_from_spec/resourcesync_ex_19.xml'
            c.parse_document()
        self.assertRegex(capturer.result, r'Parsed changelist document with 4 entries')
        with capture_stdout() as capturer:
            c.sitemap_name = 'tests/testdata/examples_from_spec/resourcesync_ex_22.xml'
            c.parse_document()
        self.assertRegex(capturer.result, r'Parsed changedump document with 3 entries')
        # Document that doesn't exist
        c.sitemap_name = '/does_not_exist'
        self.assertRaises(ClientFatalError, c.parse_document)
        # and verbose with truncation...
        with capture_stdout() as capturer:
            c.verbose = True
            c.sitemap_name = 'tests/testdata/examples_from_spec/resourcesync_ex_1.xml'
            c.max_sitemap_entries = 1
            c.parse_document()
        self.assertRegex(capturer.result, r'Showing first 1 entries')
        self.assertRegex(capturer.result, r'\[0\] ')
        self.assertNotRegex(capturer.result, r'\[1\] ')

    def test40_write_resource_list_mappings(self):
        c = Client()
        c.set_mappings(['http://example.org/d1=tests/testdata/dir1',
                        'http://example.org/d2=tests/testdata/dir2'])
        # with no explicit paths seting the mapping will be used
        with capture_stdout() as capturer:
            c.write_resource_list()
        # sys.stderr.write(capturer.result)
        self.assertRegex(capturer.result, r'<rs:md at="\S+" capability="resourcelist"')
        self.assertRegex(capturer.result, r'<url><loc>http://example.org/d1/file_a</loc>')
        self.assertRegex(capturer.result, r'<url><loc>http://example.org/d1/file_b</loc>')
        self.assertRegex(capturer.result, r'<url><loc>http://example.org/d2/file_x</loc>')

    def test41_write_resource_list_path(self):
        c = Client()
        c.set_mappings(['http://example.org/', 'tests/testdata/'])
        links = [{'rel': 'uri_c', 'href': 'uri_d'}]
        # with an explicit paths setting only the specified paths will be
        # included
        with capture_stdout() as capturer:
            c.write_resource_list(paths='tests/testdata/dir1', links=links)
        print("capturer.result: " + capturer.result)
        self.assertRegex(capturer.result, r'<rs:md at="\S+" capability="resourcelist"')
        self.assertRegex(capturer.result, r'<url><loc>http://example.org/dir1/file_a</loc>')
        self.assertRegex(capturer.result, r'<url><loc>http://example.org/dir1/file_b</loc>')
        self.assertNotRegex(capturer.result, r'<url><loc>http://example.org/dir2/file_x</loc>')
        # check link present
        self.assertRegex(capturer.result, r'rel="uri_c"')
        self.assertRegex(capturer.result, r'href="uri_d"')
        # Travis CI does not preserve timestamps from github so test here for the file
        # size but not the datestamp
        # self.assertRegex(capturer.result, r'<url><loc>http://example.org/dir1/file_a</loc><lastmod>[\w\-:]+</lastmod><rs:md length="20" /></url>')
        # self.assertRegex(capturer.result, r'<url><loc>http://example.org/dir1/file_b</loc><lastmod>[\w\-:]+</lastmod><rs:md length="45" /></url>')
        # to file
        outfile = os.path.join(self.tmpdir, 'rl_out.xml')
        c.write_resource_list(paths='tests/testdata/dir1', outfile=outfile)
        self.assertTrue(os.path.getsize(outfile) > 100)
        # dump instead (default file)
        c.default_resource_dump = os.path.join(self.tmpdir, 'rl_out_dump_def')
        outfile = c.default_resource_dump + '00000.zip'
        self.assertFalse(os.path.exists(outfile))
        c.write_resource_list(paths='tests/testdata/dir1', dump=True)
        self.assertTrue(os.path.getsize(outfile) > 100)
        # (specific file)
        outbase = os.path.join(self.tmpdir, 'rl_out_dump')
        outfile = outbase + '00000.zip'
        self.assertFalse(os.path.exists(outfile))
        c.write_resource_list(paths='tests/testdata/dir1',
                              dump=True, outfile=outbase)
        self.assertTrue(os.path.getsize(outfile) > 100)

    def test45_write_change_list(self):
        c = Client()
        ex1 = 'tests/testdata/examples_from_spec/resourcesync_ex_1.xml'
        with capture_stdout() as capturer:
            c.write_change_list(ref_sitemap=ex1, newref_sitemap=ex1)
        self.assertRegex(capturer.result, r'<rs:md capability="changelist"')
        # compare ex1 with testdata on disk
        c.set_mappings(['http://example.org/', 'tests/testdata/'])
        with capture_stdout() as capturer:
            c.write_change_list(ref_sitemap=ex1, paths='tests/testdata/dir1')
        self.assertRegex(capturer.result, r'<rs:md capability="changelist"')
        self.assertRegex(capturer.result, r'<url><loc>http://example.com/res1</loc><rs:md change="deleted" /></url>')
        # to file
        outfile = os.path.join(self.tmpdir, 'cl_out.xml')
        c.write_change_list(
            ref_sitemap=ex1, newref_sitemap=ex1, outfile=outfile)
        self.assertTrue(os.path.getsize(outfile) > 100)

    def test46_write_capability_list(self):
        c = Client()
        caps = {'a': 'uri_a', 'b': 'uri_b'}
        # simple case to STDOUT
        with capture_stdout() as capturer:
            c.write_capability_list(caps)
        self.assertRegex(capturer.result, r'<urlset ')
        self.assertRegex(capturer.result, r'<rs:md capability="capabilitylist" />')
        self.assertRegex(capturer.result, r'<url><loc>uri_a</loc><rs:md capability="a"')
        self.assertRegex(capturer.result, r'<url><loc>uri_b</loc><rs:md capability="b"')
        # to file (just check that something is written)
        outfile = os.path.join(self.tmpdir, 'caps_out.xml')
        c.write_capability_list(capabilities=caps, outfile=outfile)
        self.assertTrue(os.path.getsize(outfile) > 100)

    def test47_write_source_description(self):
        c = Client()
        # simple case to STDOUT
        with capture_stdout() as capturer:
            c.write_source_description(['a', 'b', 'c'])
        self.assertRegex(capturer.result, r'<urlset ')
        self.assertRegex(capturer.result, r'<rs:md capability="description" />')
        self.assertRegex(capturer.result, r'<url><loc>a</loc><rs:md capability="capabilitylist" /></url>')
        self.assertRegex(capturer.result, r'<url><loc>b</loc><rs:md capability="capabilitylist" /></url>')
        # more complex case to STDOUT
        with capture_stdout() as capturer:
            c.write_source_description(
                capability_lists=['http://a.b/'], links=[{'rel': 'c', 'href': 'd'}])
        self.assertRegex(capturer.result, r'http://a.b/')
        # to file (just check that something is written)
        outfile = os.path.join(self.tmpdir, 'sd_out.xml')
        c.write_source_description(capability_lists=[
                                   'http://a.b/'], outfile=outfile, links=[{'rel': 'c', 'href': 'd'}])
        self.assertTrue(os.path.getsize(outfile) > 100)

    def test48_write_dump_if_requested(self):
        c = Client()
        # no dump file
        self.assertFalse(c.write_dump_if_requested(ChangeList(), None))
        # with dump file
        with capture_stdout() as capturer:
            c.write_dump_if_requested(ChangeList(), '/tmp/a_file')
        self.assertRegex(capturer.result, r'FIXME')

    def test49_read_reference_resource_list(self):
        c = Client()
        with capture_stdout() as capturer:
            rl = c.read_reference_resource_list(
                'tests/testdata/examples_from_spec/resourcesync_ex_1.xml')
        self.assertEqual(len(rl), 2)
        self.assertEqual('', capturer.result)
        c.verbose = True
        with capture_stdout() as capturer:
            rl = c.read_reference_resource_list(
                'tests/testdata/examples_from_spec/resourcesync_ex_1.xml')
        self.assertEqual(len(rl), 2)
        self.assertRegex(capturer.result, r'http://example.com/res2')
        c.verbose = True
        c.max_sitemap_entries = 1
        with capture_stdout() as capturer:
            rl = c.read_reference_resource_list(
                'tests/testdata/examples_from_spec/resourcesync_ex_1.xml')
        self.assertEqual(len(rl), 2)
        self.assertRegex(capturer.result, r'http://example.com/res1')
        self.assertRegex(capturer.result, r'Showing first 1 entries')
        self.assertNotRegex(capturer.result, r'http://example.com/res2')

    def test50_log_status(self):
        c = Client()
        with LogCapture() as lc:
            c.logger = logging.getLogger('resync.client')
            c.log_status()
            self.assertEqual(lc.records[-1].msg,
                             'Status:         IN SYNC (created=0, updated=0, deleted=0)')
            c.log_status(created=123, updated=456, deleted=789)
            self.assertEqual(lc.records[-1].msg,
                             'Status:         IN SYNC (created=123, updated=456, deleted=789)')
            c.log_status(incremental=True)
            self.assertEqual(lc.records[-1].msg,
                             'Status:      NO CHANGES (created=0, updated=0, deleted=0)')
            c.log_status(audit=True)
            self.assertEqual(lc.records[-1].msg,
                             'Status:         IN SYNC (to create=0, to update=0, to delete=0)')
            c.log_status(in_sync=False, audit=True)
            self.assertEqual(lc.records[-1].msg,
                             'Status:     NOT IN SYNC (to create=0, to update=0, to delete=0)')
            c.log_status(in_sync=False, audit=False, to_delete=1)
            self.assertEqual(lc.records[-1].msg,
                             'Status:     PART SYNCED (created=0, updated=0, to delete (--delete)=1)')
            c.log_status(in_sync=False, audit=False,
                         to_delete=1, incremental=1)
            self.assertEqual(lc.records[-1].msg,
                             'Status:    PART APPLIED (created=0, updated=0, to delete (--delete)=1)')
            c.log_status(in_sync=False)
            self.assertEqual(lc.records[-1].msg,
                             'Status:          SYNCED (created=0, updated=0, deleted=0)')
