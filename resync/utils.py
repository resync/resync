"""util.py: A collection of utility functions for source and/or client."""
import base64
import hashlib

"""Compute digests for ResourceSync.

These are all base64 encoded according to the rules of
http://www.ietf.org/rfc/rfc4648.txt

MD5

ResourceSync defined to be the same as for Content-MD5 in HTTP,
http://www.ietf.org/rfc/rfc2616.txt which, in turn, defined the
digest string as the "base64 of 128 bit MD5 digest as per RFC 1864"
http://www.ietf.org/rfc/rfc1864.txt

Unfortunately, RFC1864 is rather vague and contains only and example
which doesn't use encoding characters for 62 or 63. It points to
RFC1521 to describe base64 which is explicit that the encoding alphabet
is [A-Za-z0-9+/] with = to pad.

The above corresponds with the alphabet of "3. Base 64 Encoding" in RFC3548
http://www.ietf.org/rfc/rfc3548.txt
and not the url safe version, "Base 64 Encoding with URL and Filename Safe
Alphabet" which replaces + and / with - and _ respectively.

This is the same as the alphabet of "4. Base 64 Encoding" in RFC4648
http://www.ietf.org/rfc/rfc4648.txt.

This algorithm is implemented by base64.standard_b64encode() or
base64.b64encode() with no altchars specified. Available in python2.4 and
up [http://docs.python.org/library/base64.html]
"""


def compute_md5_for_string(str):
    """Compute MD5 digest over some string or byte payload.

    Returns a string containing the digest.
    """
    if (not isinstance(str, bytes)):
        str = str.encode('utf-8')  # make bytes
    return base64.b64encode(hashlib.md5(str).digest()).decode('utf-8')


def compute_md5_for_file(file, block_size=2**14):
    """Compute MD5 digest for a file.

    Returns a string containing the digest. Optional block_size parameter
    controls memory used to do MD5 calculation. This should be a multiple
    of 128 bytes.
    """
    f = open(file, 'rb')
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    f.close()
    return base64.b64encode(md5.digest()).decode('utf-8')
