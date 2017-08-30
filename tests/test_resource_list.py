from tests.testcase_with_tmpdir import TestCase
import os.path
try:  # python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError:  # python3
    import io
import re

from resync.resource import Resource
from resync.resource_list import ResourceList, ResourceListDupeError
from resync.sitemap import Sitemap, SitemapParseError


class TestResourceList(TestCase):

    def test01_same(self):
        src = ResourceList()
        src.add(Resource('a', timestamp=1))
        src.add(Resource('b', timestamp=2))
        dst = ResourceList()
        dst.add(Resource('a', timestamp=1))
        dst.add(Resource('b', timestamp=2))
        (same, changed, deleted, added) = dst.compare(src)
        self.assertEqual(len(same), 2, "2 things unchanged")
        i = iter(same)
        self.assertEqual(next(i).uri, 'a', "first was a")
        self.assertEqual(next(i).uri, 'b', "second was b")
        self.assertEqual(len(changed), 0, "nothing changed")
        self.assertEqual(len(deleted), 0, "nothing deleted")
        self.assertEqual(len(added), 0, "nothing added")

    def test02_changed(self):
        src = ResourceList()
        src.add(Resource('a', timestamp=1))
        src.add(Resource('b', timestamp=2))
        dst = ResourceList()
        dst.add(Resource('a', timestamp=3))
        dst.add(Resource('b', timestamp=4))
        (same, changed, deleted, added) = dst.compare(src)
        self.assertEqual(len(same), 0, "0 things unchanged")
        self.assertEqual(len(changed), 2, "2 things changed")
        i = iter(changed)
        self.assertEqual(next(i).uri, 'a', "first was a")
        self.assertEqual(next(i).uri, 'b', "second was b")
        self.assertEqual(len(deleted), 0, "nothing deleted")
        self.assertEqual(len(added), 0, "nothing added")

    def test03_deleted(self):
        src = ResourceList()
        src.add(Resource('a', timestamp=1))
        src.add(Resource('b', timestamp=2))
        dst = ResourceList()
        dst.add(Resource('a', timestamp=1))
        dst.add(Resource('b', timestamp=2))
        dst.add(Resource('c', timestamp=3))
        dst.add(Resource('d', timestamp=4))
        (same, changed, deleted, added) = dst.compare(src)
        self.assertEqual(len(same), 2, "2 things unchanged")
        self.assertEqual(len(changed), 0, "nothing changed")
        self.assertEqual(len(deleted), 2, "c and d deleted")
        i = iter(deleted)
        self.assertEqual(next(i).uri, 'c', "first was c")
        self.assertEqual(next(i).uri, 'd', "second was d")
        self.assertEqual(len(added), 0, "nothing added")

    def test04_added(self):
        src = ResourceList()
        src.add(Resource('a', timestamp=1))
        src.add(Resource('b', timestamp=2))
        src.add(Resource('c', timestamp=3))
        src.add(Resource('d', timestamp=4))
        dst = ResourceList()
        dst.add(Resource('a', timestamp=1))
        dst.add(Resource('c', timestamp=3))
        (same, changed, deleted, added) = dst.compare(src)
        self.assertEqual(len(same), 2, "2 things unchanged")
        self.assertEqual(len(changed), 0, "nothing changed")
        self.assertEqual(len(deleted), 0, "nothing deleted")
        self.assertEqual(len(added), 2, "b and d added")
        i = iter(added)
        self.assertEqual(next(i).uri, 'b', "first was b")
        self.assertEqual(next(i).uri, 'd', "second was d")

    def test05_add(self):
        r1 = Resource(uri='a', length=1)
        r2 = Resource(uri='b', length=2)
        i = ResourceList()
        i.add(r1)
        self.assertRaises(ResourceListDupeError, i.add, r1)
        i.add(r2)
        self.assertRaises(ResourceListDupeError, i.add, r2)
        # allow dupes
        r1d = Resource(uri='a', length=10)
        i.add(r1d, replace=True)
        self.assertEqual(len(i), 2)
        self.assertEqual(i.resources['a'].length, 10)

    def test06_add_iterable(self):
        r1 = Resource(uri='a', length=1)
        r2 = Resource(uri='b', length=2)
        i = ResourceList()
        i.add([r1, r2])
        self.assertRaises(ResourceListDupeError, i.add, r1)
        self.assertRaises(ResourceListDupeError, i.add, r2)
        # allow dupes
        r1d = Resource(uri='a', length=10)
        i.add([r1d], replace=True)
        self.assertEqual(len(i), 2)
        self.assertEqual(i.resources['a'].length, 10)

    def test07_hashes(self):
        r1 = Resource(uri='a')
        r2 = Resource(uri='b')
        i = ResourceList()
        self.assertEqual(i.hashes(), set())
        i.add(r1)
        i.add(r2)
        self.assertEqual(i.hashes(), set())
        r1.md5 = "aabbcc"
        self.assertEqual(i.hashes(), set(['md5']))
        r2.sha1 = "ddeeff"
        self.assertEqual(i.hashes(), set(['md5', 'sha-1']))

    def test08_iter(self):
        i = ResourceList()
        i.add(Resource('a', timestamp=1))
        i.add(Resource('b', timestamp=2))
        i.add(Resource('c', timestamp=3))
        i.add(Resource('d', timestamp=4))
        resources = []
        for r in i:
            resources.append(r)
        self.assertEqual(len(resources), 4)
        self.assertEqual(resources[0].uri, 'a')
        self.assertEqual(resources[3].uri, 'd')

    def test20_as_xml(self):
        rl = ResourceList()
        rl.add(Resource('a', timestamp=1))
        rl.add(Resource('b', timestamp=2))
        xml = rl.as_xml()
        self.assertTrue(
            re.search(r'<rs:md .*capability="resourcelist"', xml), 'XML has capability')
        self.assertTrue(re.search(
            r'<url><loc>a</loc><lastmod>1970-01-01T00:00:01Z</lastmod></url>', xml), 'XML has resource a')

    def test30_parse(self):
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md at="2013-08-07" capability="resourcelist" completed="2013-08-08" />\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="updated" length="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md length="32" /></url>\
</urlset>'
        rl = ResourceList()
        rl.parse(fh=io.StringIO(xml))
        self.assertEqual(len(rl.resources), 2, 'got 2 resources')
        self.assertEqual(rl.md['capability'], 'resourcelist', 'capability set')
        self.assertEqual(rl.md_at, '2013-08-07')
        self.assertEqual(rl.md_completed, '2013-08-08')

    def test31_parse_no_capability(self):
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\
<url><loc>http://example.com/res1</loc><lastmod>2012-03-14T18:37:36Z</lastmod></url>\
</urlset>'
        rl = ResourceList()
        rl.parse(fh=io.StringIO(xml))
        self.assertEqual(len(rl.resources), 1, 'got 1 resource')
        self.assertEqual(rl.md['capability'], 'resourcelist',
                         'capability set by reading routine')
        self.assertFalse('from' in rl.md)

    def test32_parse_bad_capability(self):
        # the <rs:md capability="bad_capability".. should give error
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="bad_capability" from="2013-01-01"/>\
<url><loc>http://example.com/bad_res_1</loc><lastmod>2012-03-14T18:37:36Z</lastmod></url>\
</urlset>'
        rl = ResourceList()
        self.assertRaises(SitemapParseError, rl.parse, fh=io.StringIO(xml))

    def test33_write(self):
        # ResourceList
        rl = ResourceList()

        rl.add(Resource(uri='http://example.com/test/a', timestamp=1))
        rl.add(Resource(uri='http://example.com/test/b', timestamp=1))
        rl.add(Resource(uri='http://example.com/test/c', timestamp=1))

        rl_filename = os.path.join(self.tmpdir, 'test33_write_resourcelist.xml')
        rl.write(basename=rl_filename)

        with open(rl_filename, 'r') as f:
            s = Sitemap()
            s.parse_xml(fh=f)
            self.assertFalse(s.parsed_index)

        # ResourceListIndex
        rli = ResourceList()

        rli.add(Resource(uri='http://example.com/test/resourcelist00000.xml', timestamp=1))
        rli.add(Resource(uri='http://example.com/test/resourcelist00001.xml', timestamp=1))
        rli.add(Resource(uri='http://example.com/test/resourcelist00002.xml', timestamp=1))
        rli.sitemapindex = True

        rli_filename = os.path.join(self.tmpdir, 'test33_write_resourcelist-index.xml')
        rli.write(basename=rli_filename)

        with open(rli_filename, 'r') as f:
            s = Sitemap()
            s.parse_xml(fh=f)
            self.assertTrue(s.parsed_index)
