import os.path
import unittest
import tempfile
import subprocess
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
        d=Dump(rl)
        zipfile="test00_dump.zip"
        d.write_zip("test00_dump.zip")
        self.assertTrue( os.path.exists(zipfile) )

    def test01_dump_zip_change_list(self):
        cl=ChangeDumpManifest()
        cl.add( Resource('http://ex.org/a', length=7, path='resync/test/testdata/a', change="updated") )
        cl.add( Resource('http://ex.org/b', length=21, path='resync/test/testdata/b', change="updated") )
        d=Dump(cl)
        d.write_zip("test00_dump.zip")

    def test02_dump_check_files(self):
        cl=ChangeList()
        cl.add( Resource('http://ex.org/a', length=7, path='resync/test/testdata/a', change="updated") )
        cl.add( Resource('http://ex.org/b', length=21, path='resync/test/testdata/b', change="updated") )
        d=Dump(resources=cl)
        self.assertTrue(d.check_files())
        self.assertEqual(d.total_size, 28)
        
    def test03_dump_multi_file(self):
        rl=ResourceList()
        for letter in map(chr,xrange(ord('a'),ord('l')+1)):
            uri='http://ex.org/%s' % (letter)
            fname='resync/test/testdata/a_to_z/%s' % (letter)
            rl.add( Resource(uri, path=fname) )
        self.assertEqual( len(rl), 12 )
        #d=Dump(rl) 
        #tmpdir=tempfile.mkdtemp()
        #tmpbase=os.path.join(tmpdir,'base')
        #d.max_size=2000 # start new zip after size exceeds 2000 bytes
        #n=d.write(tmpbase)
        #self.assertEqual( n, 2, 'expect to write 2 dump files' )
        # 
        # Now repeat with large size limit but small number of files limit
        d2=Dump(rl) 
        tmpdir=tempfile.mkdtemp()
        tmpbase=os.path.join(tmpdir,'basez')
        d2.max_files=4
        n=d2.write(tmpbase)
        self.assertEqual( n, 3, 'expect to write 3 dump files' )
        self.assertEqual( 'a', subprocess.check_output(['/bin/ls','-l',tmpdir]) )   
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
