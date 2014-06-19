import unittest
from resync.dump import Dump, DumpError
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.resource import Resource
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.change_dump_manifest import ChangeDumpManifest

class TestDump(unittest.TestCase):

    def test00_dump_zip_resource_list(self):
        rl=ResourceDumpManifest()
        rl.add( Resource('http://ex.org/a', length=7, path='resync/test/testdata/a') )
        rl.add( Resource('http://ex.org/b', length=21, path='resync/test/testdata/b') )
        d=Dump()
        d.write_zip(rl,"test00_dump.zip")

    def test01_dump_zip_change_list(self):
        cl=ChangeDumpManifest()
        cl.add( Resource('http://ex.org/a', length=7, path='resync/test/testdata/a', change="updated") )
        cl.add( Resource('http://ex.org/b', length=21, path='resync/test/testdata/b', change="updated") )
        d=Dump()
        d.write_zip(cl,"test00_dump.zip")

    def test02_dump_check_files(self):
        cl=ChangeList()
        cl.add( Resource('http://ex.org/a', length=7, path='resync/test/testdata/a', change="updated") )
        cl.add( Resource('http://ex.org/b', length=21, path='resync/test/testdata/b', change="updated") )
        d=Dump(resources=cl)
        self.assertTrue(d.check_files())
        self.assertEqual(d.total_size, 28)
        
    #FIXME -- need some code to actually write and read dump


    def test10_no_path(self):
        rl=ResourceList()
        rl.add( Resource('http://ex.org/a', length=7, path='resync/test/testdata/a') )
        rl.add( Resource('http://ex.org/b', length=21 ) )
        d=Dump(rl)
        self.assertRaises( DumpError, d.check_files )

    def test11_bad_size(self):
        rl=ResourceList()
        rl.add( Resource('http://ex.org/a', length=9999, path='resync/test/testdata/a') )
        d=Dump(rl)
        self.assertTrue( d.check_files(check_length=False) )
        self.assertRaises( DumpError, d.check_files )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestDump)
    unittest.TextTestRunner(verbosity=2).run(suite)
