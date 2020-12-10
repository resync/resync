"""Provide capture_stdout as context manager."""

import sys
import contextlib
try:  # python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError:  # python3
    import io

# From
# http://stackoverflow.com/questions/2654834/capturing-stdout-within-the-same-process-in-python


class Data(object):
    """Object for captured data."""

    pass


@contextlib.contextmanager
def capture_stdout():
    """Capture and return stdout as context manager."""
    old = sys.stdout
    capturer = io.StringIO()
    sys.stdout = capturer
    data = Data()
    yield data
    sys.stdout = old
    data.result = capturer.getvalue()
