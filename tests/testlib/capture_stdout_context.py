"""Provide capture_stdout as context manager."""

import contextlib
import io
import sys

# From
# http://stackoverflow.com/questions/2654834/capturing-stdout-within-the-same-process-in-python


class Data(object):
    """Object for captured data."""

    def __init__(self):
        """Container for result."""
        self.result = ''


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
