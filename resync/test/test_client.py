import unittest
import logging
from resync.client import Client, ClientFatalError

class TestResource(unittest.TestCase):

    def test1_make_inventory_empty(self):
        c = Client()
        # No mapping is error
        # 
        def wrap_inventory_property_call(c):
            # do this because assertRaises( ClientFatalError, c.inventory ) doesn't work
            return(c.inventory)
        self.assertRaises( ClientFatalError, wrap_inventory_property_call, c )

    def test2_bad_source_uri(self):
        c = Client()
        self.assertRaises( ClientFatalError, c.baseline_or_audit )
        c.set_mappings( ['http://example.org/bbb','/tmp/this_does_not_exist'] )
        self.assertRaises( ClientFatalError, c.baseline_or_audit )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientResource)
    unittest.TextTestRunner(verbosity=2).run(suite)
