import unittest
from resync.dump import Dump, DumpError
from resync.resourcelist import ResourceList
from resync.resource import Resource

class TestDump(unittest.TestCase):

    def test00_dump_creation(self):
        i=ResourceList()
        i.add( Resource('http://ex.org/a', size=1, path='resync/test/testdata/a') )
        i.add( Resource('http://ex.org/b', size=2, path='resync/test/testdata/b') )
        d=Dump()
        d.check_files(resourcelist=i)
        self.assertEqual(d.total_size, 28)
        
    #FIXME -- need some code to actually write and read dump

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestDump)
    unittest.TextTestRunner(verbosity=2).run(suite)
