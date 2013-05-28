import unittest
from resync.client_utils import count_true_args,parse_links,parse_link,parse_capabilities,parse_capability_lists
from resync.client import ClientFatalError

class TestClientUtils(unittest.TestCase):

    def test01_count_true_args(self):
        self.assertEqual( count_true_args(), 0 )
        self.assertEqual( count_true_args(True), 1 )
        self.assertEqual( count_true_args(False), 0 )
        self.assertEqual( count_true_args(0,1,2,3), 3 )

    def test02_parse_links(self):
        self.assertEqual( parse_links( [] ), [] )
        self.assertEqual( parse_links( ['u,h'] ), [{'href': 'h', 'rel': 'u'}] )
        self.assertEqual( parse_links( ['u,h','v,i'] ), [{'href': 'h', 'rel': 'u'},{'href': 'i', 'rel': 'v'}] )
        self.assertRaises( ClientFatalError, parse_links, 'xx' )
        self.assertRaises( ClientFatalError, parse_links, ['u'] )
        self.assertRaises( ClientFatalError, parse_links, ['u,h','u'] )

    def test03_parse_link(self):
        # Input string of the form: rel,href,att1=val1,att2=val2
        self.assertEqual( parse_link('u,h'), {'href': 'h', 'rel': 'u'} )
        self.assertEqual( parse_link('u,h,a=b'), {'a': 'b', 'href': 'h', 'rel': 'u'} )
        self.assertEqual( parse_link('u,h,a=b,c=d'), {'a': 'b', 'c': 'd', 'href': 'h', 'rel': 'u'} )
        self.assertEqual( parse_link('u,h,a=b,a=d'), {'a': 'd', 'href': 'h', 'rel': 'u'} ) # desired??
        self.assertRaises( ClientFatalError, parse_link, '' )
        self.assertRaises( ClientFatalError, parse_link, 'u' )
        self.assertRaises( ClientFatalError, parse_link, 'u,' )
        self.assertRaises( ClientFatalError, parse_link, 'u,h,,' )
        self.assertRaises( ClientFatalError, parse_link, 'u,h,a' )
        self.assertRaises( ClientFatalError, parse_link, 'u,h,a=' )
        self.assertRaises( ClientFatalError, parse_link, 'u,h,a=b,=c' )

    def test04_parse_capabilities(self):
        # Input string of the form: cap_name=uri,cap_name=uri 
        self.assertRaises( ClientFatalError, parse_capabilities, 'a' )
        #self.assertRaises( ClientFatalError, parse_capabilities, 'a=' )
        self.assertRaises( ClientFatalError, parse_capabilities, 'a=b,' )
        #self.assertRaises( ClientFatalError, parse_capabilities, 'a=b,c=' )

    def test05_parse_capability_lists(self):
        # Input string of the form: uri,uri
        self.assertEqual( parse_capability_lists('a,b'), ['a','b'] )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestClientUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)
