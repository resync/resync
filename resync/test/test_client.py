import unittest
import re
from resync.client import Client, ClientFatalError

import sys, StringIO, contextlib

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

    def test1_make_resource_list_empty(self):
        c = Client()
        # No mapping is error
        # 
        def wrap_resource_list_property_call(c):
            # do this because assertRaises( ClientFatalError, c.resource_list ) doesn't work
            return(c.resource_list)
        self.assertRaises( ClientFatalError, wrap_resource_list_property_call, c )

    def test2_bad_source_uri(self):
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

    def test06_write_capability_list_index(self):
        c = Client()
        with capture_stdout() as capturer:
            c.write_capability_list_index( [ 'a','b','c' ] )
        self.assertTrue( re.search(r'<sitemapindex ',capturer.result) )
        self.assertTrue( re.search(r'<rs:md capability="capabilitylist" modified=',capturer.result) )
        #print capturer.result
        self.assertTrue( re.search(r'<sitemap><loc>a</loc></sitemap>',capturer.result) )
        self.assertTrue( re.search(r'<sitemap><loc>b</loc></sitemap>',capturer.result) )
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
