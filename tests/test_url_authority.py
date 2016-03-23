import unittest

from resync.url_authority import UrlAuthority

class TestUrlAuthority(unittest.TestCase):

    def test01_strict_authority(self):
        # Default is server check only
        uauth = UrlAuthority( 'http://example.org/sitemap.xml', True )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/sitemap.xml' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/sitemap.xml?anything' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/sitemap.xml#frag' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/same_level' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/one/deeper' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/one/two/deeper' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/' ) )
        self.assertTrue( uauth.has_authority_over( 'http://sub.example.org/subdomain' ) )
        self.assertTrue( uauth.has_authority_over( 'http://sub.sub.example.org/subsubdomain' ) )

    def test02_strict_no_authority(self):
        uauth = UrlAuthority( 'http://example.org/dir/sitemap.xml', True )
        self.assertFalse( uauth.has_authority_over( 'http://example.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'http://sub.example.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'https://example.org/dir/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'unknown://example.org/dir/sitemap.xml' ) )

    def test03_strict_domains(self):
        uauth = UrlAuthority( 'http://a.example.org/sitemap.xml', True )
        self.assertTrue( uauth.has_authority_over( 'http://a.example.org/sitemap.xml' ) )
        self.assertTrue( uauth.has_authority_over( 'http://sub.a.example.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'http://b.example.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'http://sub.b.example.org/sitemap.xml' ) )

    def test04_lax_authority(self):
        # Default is server check only
        uauth = UrlAuthority( 'http://example.org/dir/sitemap.xml' )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/sitemap.xml' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/sitemap.xml?anything' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/sitemap.xml#frag' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/dir/same_level' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/dir/one/deeper' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/dir/one/two/deeper' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/shallower' ) )
        self.assertTrue( uauth.has_authority_over( 'http://example.org/' ) )
        self.assertTrue( uauth.has_authority_over( 'http://sub.example.org/subdomain' ) )
        self.assertTrue( uauth.has_authority_over( 'http://sub.sub.example.org/subsubdomain' ) )

    def test05_lax_no_authority(self):
        uauth = UrlAuthority( 'http://example.org/dir/sitemap.xml' )
        self.assertFalse( uauth.has_authority_over( 'http://other.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'unknown://example.org/dir/sitemap.xml' ) )

    def test06_lax_domains(self):
        uauth = UrlAuthority( 'http://a.example.org/sitemap.xml' )
        self.assertTrue( uauth.has_authority_over( 'http://a.example.org/sitemap.xml' ) )
        self.assertTrue( uauth.has_authority_over( 'http://sub.a.example.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'http://b.example.org/sitemap.xml' ) )
        self.assertFalse( uauth.has_authority_over( 'http://sub.b.example.org/sitemap.xml' ) )

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUrlAuthority)
    unittest.TextTestRunner(verbosity=2).run(suite)
