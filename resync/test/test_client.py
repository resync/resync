import unittest
import re
import logging
import sys, StringIO, contextlib

from resync.client import Client, ClientFatalError

# From http://stackoverflow.com/questions/2654834/capturing-stdout-within-the-same-process-in-python
class Data(object):
    pass

@contextlib.contextmanager
def capture_stdout():
    old = sys.stdout
    capturer = StringIO.StringIO()
    sys.stdout = capturer
    data = Data()
    yield data
    sys.stdout = old
    data.result = capturer.getvalue()


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)

    def test01_make_resource_list_empty(self):
        c = Client()
        # No mapping is error
        # 
        def wrap_resource_list_property_call(c):
            # do this because assertRaises( ClientFatalError, c.resource_list ) doesn't work
            return(c.resource_list)
        self.assertRaises( ClientFatalError, wrap_resource_list_property_call, c )

    def test02_bad_source_uri(self):
        c = Client()
        self.assertRaises( ClientFatalError, c.baseline_or_audit )
        c.set_mappings( ['http://example.org/bbb','/tmp/this_does_not_exist'] )
        self.assertRaises( ClientFatalError, c.baseline_or_audit )

    def test06_write_capability_list(self):
        c = Client()
        with capture_stdout() as capturer:
            c.write_capability_list( { 'a':'uri_a', 'b':'uri_b' } )
        self.assertTrue( re.search(r'<urlset ',capturer.result) )
        self.assertTrue( re.search(r'<rs:md capability="capabilitylist" modified=',capturer.result) )
        self.assertTrue( re.search(r'<url><loc>uri_a</loc><rs:md capability="a"',capturer.result) )
        self.assertTrue( re.search(r'<url><loc>uri_b</loc><rs:md capability="b"',capturer.result) )

    def test07_write_capability_list_index(self):
        c = Client()
        with capture_stdout() as capturer:
            c.write_capability_list_index( [ 'a','b','c' ] )
        self.assertTrue( re.search(r'<sitemapindex ',capturer.result) )
        self.assertTrue( re.search(r'<rs:md capability="capabilitylist" modified=',capturer.result) )
        #print capturer.result
        self.assertTrue( re.search(r'<sitemap><loc>a</loc></sitemap>',capturer.result) )
        self.assertTrue( re.search(r'<sitemap><loc>b</loc></sitemap>',capturer.result) )

    def test20_parse_document(self):
        # Key property of the parse_document() method is that it parses the
        # document and identifies its type
        c = Client()
        with capture_stdout() as capturer:
            c.sitemap_name='resync/test/testdata/examples_from_spec/resourcesync_ex_2_1.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed resourcelist document with 2 entries',capturer.result) )
        with capture_stdout() as capturer:
            c.sitemap_name='resync/test/testdata/examples_from_spec/resourcesync_ex_5_1.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed resourcedump document with 3 entries',capturer.result) )
        with capture_stdout() as capturer:
            c.sitemap_name='resync/test/testdata/examples_from_spec/resourcesync_ex_6_1.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed changelist document with 4 entries',capturer.result) )
        with capture_stdout() as capturer:
            c.sitemap_name='resync/test/testdata/examples_from_spec/resourcesync_ex_7_1.xml'
            c.parse_document()
        self.assertTrue( re.search(r'Parsed changedump document with 3 entries',capturer.result) )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
