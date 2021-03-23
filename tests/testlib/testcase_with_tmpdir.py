"""Extension of unittest.TestCase to create a temp directory tmpdir."""
import sys
import os.path
import unittest
import tempfile
import shutil


class TestCase(unittest.TestCase):
    """Adds setUpClass an tearDownClass that create and destroy tmpdir."""

    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        """Create tmp dir to write to and check."""
        cls._tmpdir = tempfile.mkdtemp()
        if (not os.path.isdir(cls._tmpdir)):
            raise Exception("Failed to create tempdir to use for dump tests")
        try:
            cls.extraSetUpClass()
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        """Cleanup."""
        if (not os.path.isdir(cls._tmpdir)):
            raise Exception("Ooops, no tempdir (%s) to clean up?" % (cls._tmpdir))
        shutil.rmtree(cls._tmpdir)
        try:
            cls.extraTearUpClass()
        except Exception:
            pass

    @property
    def tmpdir(self):
        """Read-only access to _tmpdir, just in case... The rmtree scares me."""
        return(self._tmpdir)
