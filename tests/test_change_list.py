import unittest
try:  # python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError:  # python3
    import io
import re

from resync.resource import Resource
from resync.change_list import ChangeList, ChangeTypeError
from resync.resource_list import ResourceList
from resync.sitemap import SitemapParseError


class TestChangeList(unittest.TestCase):

    def test01_add_if_changed(self):
        cl = ChangeList()
        cl.add_if_changed(Resource('a', timestamp=1, change='updated'))
        self.assertEqual(len(cl), 1)
        self.assertRaises(ChangeTypeError, cl.add_if_changed,
                          Resource('c', timestamp=3))

    def test02_set_with_repeats(self):
        cl = ChangeList()
        cl.add(Resource('a', timestamp=1, change='updated'))
        cl.add(Resource('b', timestamp=1, change='created'))
        cl.add(Resource('c', timestamp=1, change='deleted'))
        cl.add(Resource('a', timestamp=2, change='deleted'))
        cl.add(Resource('b', timestamp=2, change='updated'))
        self.assertEqual(len(cl), 5, "5 changes in change_list")

    def test03_with_repeats_again(self):
        r1 = Resource(uri='a', length=1, change='created')
        r2 = Resource(uri='b', length=2, change='created')
        i = ChangeList()
        i.add(r1)
        i.add(r2)
        self.assertEqual(len(i), 2)
        # Can add another Resource with same URI
        r1d = Resource(uri='a', length=10, change='created')
        i.add(r1d)
        self.assertEqual(len(i), 3)

    def test04_change_list(self):
        cl = ChangeList()
        cl.add(Resource('a', timestamp=1, change='created'))
        cl.add(Resource('b', timestamp=2, change='created'))
        cl.add(Resource('c', timestamp=3, change='created'))
        cl.add(Resource('d', timestamp=4, change='created'))
        cl.add(Resource('e', timestamp=5, change='created'))
        self.assertEqual(len(cl), 5, "5 things in src")

    def test05_iter(self):
        i = ChangeList()
        i.add(Resource('a', timestamp=1, change='created'))
        i.add(Resource('b', timestamp=2, change='created'))
        i.add(Resource('c', timestamp=3, change='created'))
        i.add(Resource('d', timestamp=4, change='created'))
        resources = []
        for r in i:
            resources.append(r)
        self.assertEqual(len(resources), 4)
        self.assertEqual(resources[0].uri, 'a')
        self.assertEqual(resources[3].uri, 'd')

    def test06_add_changed_resources(self):
        added = ResourceList()
        added.add(Resource('a', timestamp=1, change='created'))
        added.add(Resource('d', timestamp=4, change='created'))
        self.assertEqual(len(added), 2, "2 things in added resource_list")
        changes = ChangeList()
        changes.add_changed_resources(added, change='created')
        self.assertEqual(len(changes), 2, "2 things added")
        i = iter(changes)
        first = next(i)
        self.assertEqual(first.uri, 'a', "changes[0].uri=a")
        self.assertEqual(first.timestamp, 1, "changes[0].timestamp=1")
        # , "changes[0].change=createdd")
        self.assertEqual(first.change, 'created')
        second = next(i)
        self.assertEqual(second.timestamp, 4, "changes[1].timestamp=4")
        self.assertEqual(second.change, 'created',
                         "changes[1].change=createdd")
        # Now add some with updated (one same, one diff)
        updated = ResourceList()
        updated.add(Resource('a', timestamp=5, change='created'))
        updated.add(Resource('b', timestamp=6, change='created'))
        self.assertEqual(len(updated), 2, "2 things in updated resource_list")
        changes.add_changed_resources(updated, change='updated')
        self.assertEqual(len(changes), 4, "4 = 2 old + 2 things updated")
        # Make new resource_list from the changes which should not have dupes
        dst = ResourceList()
        dst.add(changes, replace=True)
        self.assertEqual(len(dst), 3, "3 unique resources")
        # 5 was later in last the 1
        self.assertEqual(dst.resources['a'].timestamp, 5)
        self.assertEqual(dst.resources['a'].change, 'updated')
        self.assertEqual(dst.resources['b'].timestamp, 6)
        self.assertEqual(dst.resources['b'].change, 'updated')
        self.assertEqual(dst.resources['d'].timestamp, 4)
        self.assertEqual(dst.resources['d'].change, 'created')

    def test07_as_xml(self):
        cl = ChangeList()
        cl.md_from = '1970-01-01T00:00:00Z'
        cl.add(Resource('a', timestamp=1, change='updated'))
        cl.add(Resource('b', timestamp=2, change='updated'))
        xml = cl.as_xml()
        self.assertTrue(
            re.search(r'<rs:md .*capability="changelist"', xml), 'XML has capability')
        self.assertTrue(re.search(r'<rs:md .*from="\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\dZ"',
                                  xml), 'XML has from to seconds precision (and not more)')
        self.assertTrue(re.search(
            r'<url><loc>a</loc><lastmod>1970-01-01T00:00:01Z</lastmod>', xml), 'XML has resource a')

    def test08_parse(self):
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="changelist" from="2013-01-01"/>\
<url><loc>/tmp/rs_test/src/file_a</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="updated" length="12" /></url>\
<url><loc>/tmp/rs_test/src/file_b</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="deleted" length="32" /></url>\
</urlset>'
        cl = ChangeList()
        cl.parse(fh=io.StringIO(xml))
        self.assertEqual(len(cl.resources), 2, 'got 2 resources')
        self.assertEqual(cl.md['capability'], 'changelist', 'capability set')
        self.assertEqual(cl.md['md_from'], '2013-01-01')

    def test09_parse_no_capability(self):
        # missing capability is an error for changelist
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<url><loc>http://example.com/res1</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="updated"/></url>\
</urlset>'
        cl = ChangeList()
        self.assertRaises(SitemapParseError, cl.parse, fh=io.StringIO(xml))

    def test10_parse_bad_capability(self):
        # the <rs:md capability="bad_capability".. should give error
        xml = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n\
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/">\
<rs:md capability="bad_capability" from="2013-01-01"/>\
<url><loc>http://example.com/bad_res_1</loc><lastmod>2012-03-14T18:37:36Z</lastmod><rs:md change="updated"/></url>\
</urlset>'
        cl = ChangeList()
        self.assertRaises(SitemapParseError, cl.parse, fh=io.StringIO(xml))

    def test11_prune_updates_before(self):
        """Test prune_updates_before method."""
        # v1.0
        cl = ChangeList()
        cl.resources.append(Resource('a', timestamp=1))
        cl.resources.append(Resource('b', timestamp=2))
        cl.resources.append(Resource('c', timestamp=3))
        cl.resources.append(Resource('d', timestamp=4))
        cl.prune_updates_before(3, spec_version='1.0')
        self.assertEqual(len(cl.resources), 2)
        i = iter(cl)
        self.assertEqual(next(i).uri, 'c')
        self.assertEqual(next(i).uri, 'd')
        # put some more back out of order
        cl.resources.append(Resource('a', timestamp=1))
        cl.resources.append(Resource('b', timestamp=2))
        cl.resources.append(Resource('e', timestamp=1000))
        cl.prune_updates_before(3.5, spec_version='1.0')
        self.assertEqual(len(cl.resources), 2)
        i = iter(cl)
        self.assertEqual(next(i).uri, 'd')
        self.assertEqual(next(i).uri, 'e')
        # without a timestamp
        cl.resources.append(Resource('nt_1_0', ts_datetime=123))
        self.assertRaises(Exception, cl.prune_updates_before, 3.5, spec_version='1.0')
        # v1.1
        cl = ChangeList()
        cl.resources.append(Resource('aa', ts_datetime=1))
        cl.resources.append(Resource('bb', ts_datetime=2))
        cl.resources.append(Resource('cc', ts_datetime=3))
        cl.prune_updates_before(3, spec_version='1.1')
        self.assertEqual(len(cl.resources), 1)
        i = iter(cl)
        self.assertEqual(next(i).uri, 'cc')
        # put some more back out of order
        cl.resources.append(Resource('aa', ts_datetime=1))
        cl.resources.append(Resource('bb', ts_datetime=2))
        cl.resources.append(Resource('ee', ts_datetime=1000))
        cl.prune_updates_before(3.5, spec_version='1.1')
        self.assertEqual(len(cl.resources), 1)
        i = iter(cl)
        self.assertEqual(next(i).uri, 'ee')
        # without a ts_datetime
        cl.resources.append(Resource('nt_1_1', timestamp=456))
        self.assertRaises(Exception, cl.prune_updates_before, 3.5, spec_version='1.1')
