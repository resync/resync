import unittest
import resync.hashes


class TestUtill(unittest.TestCase):

    def test01_md5_sha1_file(self):
        h = resync.hashes.Hashes(['md5', 'sha-1'])
        h.compute_for_file('tests/testdata/a')
        self.assertEqual(h.md5, 'j912liHgA/48DCHpkptJHg==')
        self.assertEqual(h.sha1, '49844dd211aa33071a252d7cdc250a52cf39af33')
        self.assertEqual(h.sha256, None)
        h = resync.hashes.Hashes(['sha-256', 'sha-1'])
        h.compute_for_file('tests/testdata/a')
        self.assertEqual(h.md5, None)
        self.assertEqual(h.sha1, '49844dd211aa33071a252d7cdc250a52cf39af33')
        self.assertEqual(h.sha256, '69fe6314a94800456af959d380f5d6932052478ea03d5ccac7ba0a14bd5e67c6')

    def test02_bad_type(self):
        self.assertRaises(Exception, resync.hashes.Hashes, ['md5', 'xyz'])

if __name__ == '__main__':
    unittest.main()
