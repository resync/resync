from tests.testcase_with_tmpdir import TestCase

import os.path
import unittest
import sys
import zipfile

from resync.dump import Dump, DumpError
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.resource import Resource
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.change_dump_manifest import ChangeDumpManifest


class TestDump(TestCase):

    def test00_dump_zip_resource_list(self):
        rl = ResourceDumpManifest()
        rl.add(Resource('http://ex.org/a', length=7, path='tests/testdata/a'))
        rl.add(Resource('http://ex.org/b', length=21, path='tests/testdata/b'))
        d = Dump()
        zipf = os.path.join(self.tmpdir, "test00_dump.zip")
        d.write_zip(resources=rl, dumpfile=zipf)  # named args
        self.assertTrue(os.path.exists(zipf))
        self.assertTrue(zipfile.is_zipfile(zipf))
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(len(zo.namelist()), 3)
        zo.close()
        os.unlink(zipf)

    def test01_dump_zip_change_list(self):
        cl = ChangeDumpManifest()
        cl.add(Resource('http://ex.org/a', length=7,
                        path='tests/testdata/a', change="updated"))
        cl.add(Resource('http://ex.org/b', length=21,
                        path='tests/testdata/b', change="updated"))
        d = Dump()
        zipf = os.path.join(self.tmpdir, "test01_dump.zip")
        d.write_zip(cl, zipf)  # positional args
        self.assertTrue(os.path.exists(zipf))
        self.assertTrue(zipfile.is_zipfile(zipf))
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(len(zo.namelist()), 3)
        zo.close()
        os.unlink(zipf)

    def test02_dump_check_files(self):
        cl = ChangeList()
        cl.add(Resource('http://ex.org/a', length=7,
                        path='tests/testdata/a', change="updated"))
        cl.add(Resource('http://ex.org/b', length=21,
                        path='tests/testdata/b', change="updated"))
        d = Dump(resources=cl)
        self.assertTrue(d.check_files())
        self.assertEqual(d.total_size, 28)

    def test03_dump_multi_file_max_size(self):
        rl = ResourceList()
        for letter in map(chr, range(ord('a'), ord('l') + 1)):
            uri = 'http://ex.org/%s' % (letter)
            fname = 'tests/testdata/a_to_z/%s' % (letter)
            rl.add(Resource(uri, path=fname))
        self.assertEqual(len(rl), 12)
        # d=Dump(rl)
        # tmpdir=tempfile.mkdtemp()
        # tmpbase=os.path.join(tmpdir,'base')
        # d.max_size=2000 # start new zip after size exceeds 2000 bytes
        # n=d.write(tmpbase)
        # self.assertEqual( n, 2, 'expect to write 2 dump files' )
        #
        # Now repeat with large size limit but small number of files limit
        d2 = Dump(rl)
        tmpbase = os.path.join(self.tmpdir, 'test03_')
        d2.max_files = 4
        n = d2.write(tmpbase)
        self.assertEqual(n, 3, 'expect to write 3 dump files')
        self.assertTrue(os.path.isfile(tmpbase + '00000.zip'))
        self.assertTrue(os.path.isfile(tmpbase + '00001.zip'))
        self.assertTrue(os.path.isfile(tmpbase + '00002.zip'))
        # Look at the first file in detail
        zipf = tmpbase + '00000.zip'
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(zo.namelist(), ['manifest.xml', 'a', 'b', 'c', 'd'])
        # self.assertEqual( zo.getinfo('manifest.xml').file_size, 470 )
        self.assertEqual(zo.getinfo('a').file_size, 9)
        self.assertEqual(zo.getinfo('b').file_size, 1116)
        self.assertEqual(zo.getinfo('c').file_size, 32)
        self.assertEqual(zo.getinfo('d').file_size, 13)
        zo.close()
        os.unlink(zipf)
        # Check second and third files have expected contents
        zipf = tmpbase + '00001.zip'
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(zo.namelist(), ['manifest.xml', 'e', 'f', 'g', 'h'])
        zo.close()
        os.unlink(zipf)
        zipf = tmpbase + '00002.zip'
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(zo.namelist(), ['manifest.xml', 'i', 'j', 'k', 'l'])
        zo.close()
        os.unlink(zipf)

    def test04_dump_multi_file_max_size(self):
        rl = ResourceList()
        for letter in map(chr, range(ord('a'), ord('l') + 1)):
            uri = 'http://ex.org/%s' % (letter)
            fname = 'tests/testdata/a_to_z/%s' % (letter)
            rl.add(Resource(uri, path=fname))
        self.assertEqual(len(rl), 12)
        d2 = Dump(rl)
        tmpbase = os.path.join(self.tmpdir, 'test0f_')
        d2.max_size = 2000
        n = d2.write(tmpbase)
        self.assertEqual(n, 2, 'expect to write 2 dump files')
        self.assertTrue(os.path.isfile(tmpbase + '00000.zip'))
        self.assertTrue(os.path.isfile(tmpbase + '00001.zip'))
        # Look at the first file in detail
        zipf = tmpbase + '00000.zip'
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(
            zo.namelist(), ['manifest.xml', 'a', 'b', 'c', 'd', 'e', 'f'])
        # self.assertEqual( zo.getinfo('manifest.xml').file_size, 470 )
        self.assertEqual(zo.getinfo('a').file_size, 9)
        self.assertEqual(zo.getinfo('b').file_size, 1116)
        self.assertEqual(zo.getinfo('c').file_size, 32)
        self.assertEqual(zo.getinfo('d').file_size, 13)
        self.assertEqual(zo.getinfo('e').file_size, 20)
        self.assertEqual(zo.getinfo('f').file_size, 1625)
        zo.close()
        os.unlink(zipf)
        # Check second and third files have expected contents
        zipf = tmpbase + '00001.zip'
        zo = zipfile.ZipFile(zipf, 'r')
        self.assertEqual(
            zo.namelist(), ['manifest.xml', 'g', 'h', 'i', 'j', 'k', 'l'])
        zo.close()
        os.unlink(zipf)

    def test10_no_path(self):
        rl = ResourceList()
        rl.add(Resource('http://ex.org/a', length=7, path='tests/testdata/a'))
        rl.add(Resource('http://ex.org/b', length=21))
        d = Dump(rl)
        self.assertRaises(DumpError, d.check_files)

    def test11_bad_size(self):
        rl = ResourceList()
        rl.add(Resource('http://ex.org/a', length=9999, path='tests/testdata/a'))
        d = Dump(rl)
        self.assertTrue(d.check_files(check_length=False))
        self.assertRaises(DumpError, d.check_files)

    def test10_no_path(self):
        rl = ResourceList()
        rl.add(Resource('http://ex.org/a', length=7, path='tests/testdata/a'))
        rl.add(Resource('http://ex.org/b', length=21))
        d = Dump(rl)
        self.assertRaises(DumpError, d.check_files)

    def test11_bad_size(self):
        rl = ResourceList()
        rl.add(Resource('http://ex.org/a', length=9999, path='tests/testdata/a'))
        d = Dump(rl)
        self.assertTrue(d.check_files(check_length=False))
        self.assertRaises(DumpError, d.check_files)
