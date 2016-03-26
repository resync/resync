from tests.capture_stdout import capture_stdout

import unittest
import re
import logging
import sys

from resync.client import Client, ClientFatalError
from resync.capability_list import CapabilityList
from resync.explorer import Explorer
from resync.resource import Resource

class TestExplorer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)

    def test01_create(self):
        # dumb test that we can create Exporer object
        e = Explorer()
        self.assertTrue( e )

    def test02_explore_show_summary(self):
        # Create dummy capabilities object and display
        cl = CapabilityList()
        cl.add( Resource('uri:resourcelist') )
        cl.add( Resource('uri:changelist') )
        e = Explorer()
        with capture_stdout() as capturer:
            e.explore_show_summary(cl,False,[])
        self.assertTrue( re.search(r'Parsed \(unknown capability\) document with 2 entries:',capturer.result) )
        self.assertTrue( re.search(r'\[1\] uri:changelist',capturer.result) )
        self.assertTrue( re.search(r'\[2\] uri:resourcelist',capturer.result) )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExplorer)
    unittest.TextTestRunner(verbosity=2).run(suite)
