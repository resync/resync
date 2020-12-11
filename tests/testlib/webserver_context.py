"""Provides context manager that runs local webserver."""

import contextlib
import os
import posixpath
import requests
import time
from multiprocessing import Process
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Copy of SimpleHTTPRequestHandler with cls._base_path setting."""

    base_dir = '/tmp'

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        **Based on code in http.server.SimpleHTTPRequestHandler with
        modification of base path to come from self.base_dir**
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
        # Now make path from self.base_dir and words
        tpath = self.base_dir
        for word in words:
            if word != '..':
                tpath = os.path.join(tpath, word)
        if trailing_slash:
            tpath += '/'
        # print("Translated %s -> %s" % (path, tpath))
        return tpath


def run_webserver(host, port):
    """Run webserver at given host & port."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MyHTTPRequestHandler)
    httpd.serve_forever()


@contextlib.contextmanager
def webserver(dir='/tmp', host='localhost', port=9999):
    """Context Manager that provides a webserver serving files from dir."""
    MyHTTPRequestHandler.base_dir = dir
    # print("Set MyHTTPRequestHandler.base_dir = %s" % (MyHTTPRequestHandler.base_dir))
    p = Process(target=run_webserver, args=(host, port))
    p.start()

    # Wait for the server to be launched
    base_url = 'http://%s:%d/' % (host, port)
    for j in range(0, 10):
        try:
            requests.get(base_url, timeout=0.1)
            break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.1)
    else:
        print("Failed to start test webserver from %s at host=%s port=%d" % (dir, host, port))

    try:
        yield
    finally:
        # Closing the server
        p.terminate()


if __name__ == '__main__':
    print('Will start webserver at localhost:9999 serving from /tmp')
    with webserver():
        print('Started...')
        time.sleep(10)
        # Things with server go in here
    print('Exited server')
