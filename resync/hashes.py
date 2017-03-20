"""util.py: A collection of utility functions for source and/or client."""
import base64
import hashlib

class Hashes(object):
    """Compute hash digests for ResourceSync.

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

    def __init__(self, hashes=None, file=None):
        """Initialize Hasher object with types of hash to caluclate.

        If file is supplied then compute for that file.
        """
        self.hashes = set()
        for hash in hashes:
            if (hash not in ['md5', 'sha-1', 'sha-256']):
                raise Exception("Hash type %s not supported" % (hash))
            self.hashes.add(hash)
        #
        self.md5_calc = None
        self.sha1_calc = None
        self.sha256_calc = None
        #
        if (file is not None):
            self.compute_for_file(file)

    def initialize_hashes(self):
        """Create new hashlib objects for each hash we are going to calculate."""
        if ('md5' in self.hashes):
            self.md5_calc = hashlib.md5()
        if ('sha-1' in self.hashes):
            self.sha1_calc = hashlib.sha1()
        if ('sha-256' in self.hashes):
            self.sha256_calc = hashlib.sha256()

    def compute_for_file(self, file, block_size=2**14):
        """Compute hash digests for a file.

        Calculate the hashes based on one read through the file.
        Optional block_size parameter controls memory used to do 
        calculations. This should be a multiple of 128 bytes.
        """
        self.initialize_hashes()
        f = open(file, 'rb')
        while True:
            data = f.read(block_size)
            if not data:
                break
            if (self.md5_calc is not None):
                self.md5_calc.update(data)
            if (self.sha1_calc is not None):
                self.sha1_calc.update(data)
            if (self.sha256_calc is not None):
                self.sha256_calc.update(data)
        f.close()

    @property
    def md5(self):
        """Return MD5 hash calculated."""
        if (self.md5_calc is None):
            return None
        return base64.b64encode(self.md5_calc.digest()).decode('utf-8')

    @property
    def sha1(self):
        """Return SHA-1 hash calculated."""
        if (self.sha1_calc is None):
            return None
        return self.sha1_calc.hexdigest()

    @property
    def sha256(self):
        """Return SHA-256 hash calculated."""
        if (self.sha256_calc is None):
            return None
        return self.sha256_calc.hexdigest()
