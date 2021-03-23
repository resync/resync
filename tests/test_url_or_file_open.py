"""Tests for resync.url_or_file_open."""
from .testlib import TestCase, webserver
import time

from resync.url_or_file_open import NUM_REQUESTS, CONFIG, set_url_or_file_open_config, url_or_file_open


class TestUrlOrFileOpen(TestCase):

    def test_set_url_or_file_open_config(self):
        """Test set_url_or_file_open_config function."""
        self.assertEqual(CONFIG['bearer_token'], None)
        self.assertEqual(CONFIG['delay'], None)
        self.assertNotIn('my_thing', CONFIG)
        set_url_or_file_open_config('bearer_token', 'open seasame')
        self.assertEqual(CONFIG['bearer_token'], 'open seasame')
        set_url_or_file_open_config('my_thing', 'special')
        self.assertEqual(CONFIG['my_thing'], 'special')

    def test_url_or_file_open(self):
        """Test basic operation of url_or_file_open function."""
        # Open file
        fh = url_or_file_open('tests/testdata/dir1/file_a')
        self.assertIn(b'I am file a', fh.read())
        fh.close()
        with url_or_file_open('file:tests/testdata/dir1/file_b') as fh:
            self.assertIn(b'I am file b', fh.read())
        # Open URL
        with webserver('tests/testdata', 'localhost', 9999):
            with url_or_file_open('http://localhost:9999/dir2/file_x') as fh:
                self.assertIn(b'I am the mysterious file_x', fh.read())
            # test delay of 0.1s
            set_url_or_file_open_config('delay', 0.1)
            before = time.time()
            with url_or_file_open('http://localhost:9999/dir1/file_a') as fh:
                self.assertIn(b'I am file a', fh.read())
            self.assertGreater(time.time() - before, 0.099)
