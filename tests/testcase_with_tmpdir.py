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
        except:
            pass

    @classmethod
    def tearDownClass(cls):
        """Cleanup."""
        if (not os.path.isdir(cls._tmpdir)):
            raise Exception("Ooops, no tempdir (%s) to clean up?" % (cls._tmpdir))
        shutil.rmtree(cls._tmpdir)
        try:
            cls.extraTearUpClass()
        except:
            pass

    @property
    def tmpdir(self):
        """Read-only access to _tmpdir, just in case... The rmtree scares me."""
        #
        # FIXME - Hack to work on python2.6 where setUpClass is not called, will
        # FIXME - not have proper tidy as tearDownClass will not be called.
        # FIXME - Remove when 2.6 no longer supported
        if (not self._tmpdir and sys.version_info < (2, 7)):
            self.setUpClass()
        return(self._tmpdir)
