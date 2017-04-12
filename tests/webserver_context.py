"""Provides content manager that runs local webserver."""
import contextlib
import os
import posixpath
import requests
import signal
import time
from multiprocessing import Process
try:  # python3
    from http.server import HTTPServer, SimpleHTTPRequestHandler
except:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
try:  # python3
    from urllib.parse import unquote
except ImportError:  # python2
    from urlparse import unquote


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Copy of SimpleHTTPRequestHandler with cls._base_path setting."""

    _base_path = '/'

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        **Copied from http.server.SimpleHTTPRequestHandler with modification
        of path**
        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = unquote(path)
        path = posixpath.normpath(path)
        words = path.split('/')
        words = filter(None, words)
        path = self._base_path
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path


def run_webserver(host='', port=9999):
    """Run webserver at given host & port."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MyHTTPRequestHandler)
    httpd.serve_forever()


@contextlib.contextmanager
def webserver(dir='/tmp', host='', port=9999):
    """Context Manager that provides a webserver serving files from dir."""
    MyHTTPRequestHandler._base_path = dir
    p = Process(target=run_webserver, args=(host, port))
    p.start()

    # Wait for the server to be launched
    for j in range(0, 10):
        try:
            requests.get("http://localhost:9999/", timeout=0.1)
            break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.1)

    try:
        yield
    finally:
        # Closing the server
        p.terminate()


if __name__ == '__main__':
    with webserver():
        print('Started server...')
        # Things with server go in here
    print('Exited server')
