import unittest
import resync.utils


class TestUtill(unittest.TestCase):

    def test1_string(self):
        self.assertEqual(resync.utils.compute_md5_for_string('A file\n'),
                         'j912liHgA/48DCHpkptJHg==')

    def test2_file(self):
        # Should be same as the string above
        self.assertEqual(resync.utils.compute_md5_for_file('tests/testdata/a'),
                         'j912liHgA/48DCHpkptJHg==')

if __name__ == '__main__':
    unittest.main()
