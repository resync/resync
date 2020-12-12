import subprocess
import sys
import unittest
try:  # python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import BytesIO as io
except ImportError:  # python3
    import io


def run_resync_explorer(args):
    args.insert(0, 'bin/resync-explorer')
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate()
    return(out, err)


class TestClientLinkOptions(unittest.TestCase):

    def test01_help(self):
        """Check that it runs with -h."""
        txt = run_resync_explorer(['-h'])[0]
        self.assertTrue(txt.startswith(b'Usage: resync-explorer [options] uri'))

    def test02_error(self):
        """Bad parameter."""
        err = run_resync_explorer([])[1]
        self.assertRegex(err, b'FatalError: No source information')
