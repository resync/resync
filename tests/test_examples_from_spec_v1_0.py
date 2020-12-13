"""Tests on the examples in the specification documents
"""
import re
import sys

from resync.resource import Resource
from resync.source_description import SourceDescription
from resync.capability_list import CapabilityList
from resync.resource_list import ResourceList, ResourceListOrdered
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.change_list import ChangeList
from resync.change_dump import ChangeDump
from resync.change_dump_manifest import ChangeDumpManifest
from resync.archives import ResourceListArchive, ResourceDumpArchive, ChangeListArchive, ChangeDumpArchive
from resync.sitemap import Sitemap

from .testlib.testcase_with_xml_comparison import TestCase


class TestExamplesFromSpec(TestCase):

    def _open_ex(self, ex):
        return open('tests/testdata/examples_from_spec_v1_0/%s.xml' % (ex), 'r')

    def test_all_simple_read(self):
        """Just try to read each one"""
        for ex in ('archives_ex_2_1', 'archives_ex_2_2',
                   'archives_ex_3_1', 'archives_ex_3_2',
                   'archives_ex_4_1',
                   'archives_ex_5_1',
                   'archives_ex_6_1',
                   'resourcesync_ex_1', 'resourcesync_ex_2', 'resourcesync_ex_3',
                   'resourcesync_ex_4', 'resourcesync_ex_5', 'resourcesync_ex_6',
                   'resourcesync_ex_7', 'resourcesync_ex_8', 'resourcesync_ex_12',
                   'resourcesync_ex_13', 'resourcesync_ex_14', 'resourcesync_ex_15',
                   'resourcesync_ex_16', 'resourcesync_ex_17', 'resourcesync_ex_18',
                   'resourcesync_ex_19', 'resourcesync_ex_20', 'resourcesync_ex_21',
                   'resourcesync_ex_22', 'resourcesync_ex_23', 'resourcesync_ex_24',
                   'resourcesync_ex_25', 'resourcesync_ex_26', 'resourcesync_ex_27',
                   'resourcesync_ex_28', 'resourcesync_ex_29', 'resourcesync_ex_30',
                   'resourcesync_ex_31', 'resourcesync_ex_32', 'resourcesync_ex_33'):
            s = Sitemap()
            fh = self._open_ex(ex)
            si = s.parse_xml(fh=fh)

    def test_ex_01(self):
        """resourcesync_ex_1 is a simple resource_list with 2 resources, no metadata"""
        rl = ResourceList(spec_version='1.0')
        rl.parse(uri='tests/testdata/examples_from_spec_v1_0/resourcesync_ex_1.xml')
        self.assertEqual(rl.capability, 'resourcelist')
        self.assertEqual(len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual(
            sms, ['http://example.com/res1', 'http://example.com/res2'])
        self.assertEqual(rl.resources['http://example.com/res1'].lastmod, None)

    def test_ex_02(self):
        """resourcesync_ex_2 is a simple resource_list with 2 resources, some metadata"""
        rl = ResourceList(spec_version='1.0')
        rl.parse(uri='tests/testdata/examples_from_spec_v1_0/resourcesync_ex_2.xml')
        self.assertEqual(len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual(
            sms, ['http://example.com/res1', 'http://example.com/res2'])
        self.assertEqual(
            rl.resources['http://example.com/res1'].lastmod, '2013-01-02T13:00:00Z')
        self.assertEqual(
            rl.resources['http://example.com/res2'].lastmod, '2013-01-02T14:00:00Z')
        self.assertEqual(
            rl.resources['http://example.com/res1'].md5, '1584abdf8ebdc9802ac0c6a7402c03b6')
        self.assertEqual(
            rl.resources['http://example.com/res2'].md5, '1e0d5cb8ef6ba40c99b14c0237be735e')

    def test_ex_03(self):
        """resourcesync_ex_3 is a simple change_list with 2 resources"""
        cl = ChangeList(spec_version='1.0')
        cl.parse('tests/testdata/examples_from_spec_v1_0/resourcesync_ex_3.xml')
        self.assertEqual(len(cl.resources), 2, '2 resources')
        sms = sorted(cl.uris())
        self.assertEqual(sms, ['http://example.com/res2.pdf', 'http://example.com/res3.tiff'])
        self.assertEqual(cl.resources[0].lastmod, '2013-01-02T13:00:00Z')
        self.assertEqual(cl.resources[1].lastmod, '2013-01-02T18:00:00Z')
        self.assertEqual(cl.resources[0].change, 'updated')
        self.assertEqual(cl.resources[1].change, 'deleted')

    def test_ex_04(self):
        """resourcesync_ex_4 is a simple resource dump with one ZIP listed"""
        rd = ResourceDump(spec_version='1.0')
        rd.parse('tests/testdata/examples_from_spec_v1_0/resourcesync_ex_4.xml')
        self.assertEqual(len(rd.resources), 1, '1 resources')
        self.assertTrue('http://example.com/resourcedump.zip' in rd.resources)
        self.assertEqual(rd.resources[
                         'http://example.com/resourcedump.zip'].lastmod, '2013-01-03T09:00:00Z')

    def test_ex_05(self):
        """resourcesync_ex_5 is a simple resource dump manifest with two files listed"""
        rdm = ResourceDumpManifest(spec_version='1.0')
        rdm.parse('tests/testdata/examples_from_spec_v1_0/resourcesync_ex_5.xml')
        self.assertEqual(len(rdm.resources), 2, '2 resources')
        sms = sorted(rdm.uris())
        self.assertEqual(
            sms, ['http://example.com/res1', 'http://example.com/res2'])
        self.assertEqual(
            rdm.resources['http://example.com/res1'].lastmod, '2013-01-03T03:00:00Z')
        self.assertEqual(rdm.resources[
                         'http://example.com/res1'].md5, '1584abdf8ebdc9802ac0c6a7402c03b6')
        self.assertEqual(
            rdm.resources['http://example.com/res1'].path, '/resources/res1')
        self.assertEqual(
            rdm.resources['http://example.com/res2'].lastmod, '2013-01-03T04:00:00Z')
        self.assertEqual(rdm.resources[
                         'http://example.com/res2'].md5, '1e0d5cb8ef6ba40c99b14c0237be735e')
        self.assertEqual(
            rdm.resources['http://example.com/res2'].path, '/resources/res2')

    def test_ex_06(self):
        """resourcesync_ex_6 is a simple capability list with three capabilities"""
        capl = CapabilityList(spec_version='1.0')
        capl.parse('tests/testdata/examples_from_spec_v1_0/resourcesync_ex_6.xml')
        self.assertEqual(len(capl.resources), 3, '3 capabilities')
        # What capabilities are present?
        self.assertTrue(capl.has_capability('resourcelist'))
        self.assertEqual(capl.capability_info('resourcelist').uri,
                         'http://example.com/dataset1/resourcelist.xml')
        self.assertTrue(capl.has_capability('resourcedump'))
        self.assertEqual(capl.capability_info('resourcedump').uri,
                         'http://example.com/dataset1/resourcedump.xml')
        self.assertTrue(capl.has_capability('changelist'))
        self.assertEqual(capl.capability_info('changelist').uri,
                         'http://example.com/dataset1/changelist.xml')
        # Check some that aren't
        self.assertFalse(capl.has_capability())
        self.assertFalse(capl.has_capability('bogus'))
        self.assertFalse(capl.has_capability('capabilitylist'))

    def text_ex_07(self):
        """resourcesync_ex_7 is a source description that list a single Capability List"""
        sd = SourceDescription(spec_version='1.0')
        sd.read(uri='tests/testdata/examples_from_spec_v1_0/resourcesync_ex_7.xml')
        self.assertEqual(len(sd.resources), 1, '1 capability list')
        cl = sd.resources[0]
        self.assertEqual(
            cl.uri, 'http://example.com/dataset1/capabilitylist.xml')
        self.assertEqual(cl.capability, 'resourcelist')
        self.assertEqual(
            cl.describedby, 'http://example.com/info_about_set1_of_resources.xml')

    def test_ex_08(self):
        """resourcesync_ex_8 is a simple Resource List Index with 2 Resource Lists"""
        rl = ResourceList(spec_version='1.0')
        rl.read(
            uri='tests/testdata/examples_from_spec_v1_0/resourcesync_ex_8.xml', index_only=True)
        self.assertEqual(rl.capability, 'resourcelist')
        self.assertEqual(rl.md_at, '2013-01-03T09:00:00Z')
        self.assertEqual(len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual(sms, ['http://example.com/resourcelist-part1.xml',
                               'http://example.com/resourcelist-part2.xml'])

    # Examples 9, 10, 11 in the spec are not XML documents

    def test_ex_12(self):
        """resourcesync_ex_12 is a Source Description that talks about 3 sets of resources"""
        sd = SourceDescription(spec_version='1.0')
        sd.read(uri='tests/testdata/examples_from_spec_v1_0/resourcesync_ex_12.xml')
        self.assertEqual(len(sd), 3)
        self.assertEqual(sd.uris(), ['http://example.com/capabilitylist1.xml',
                                     'http://example.com/capabilitylist2.xml',
                                     'http://example.com/capabilitylist3.xml'])
        cl1 = sd['http://example.com/capabilitylist1.xml']
        self.assertEqual(cl1.capability, 'capabilitylist')
        self.assertEqual(
            cl1.describedby, 'http://example.com/info_about_set1_of_resources.xml')

    def test_build_ex_01(self):
        """Simple Resource List document"""
        rl = ResourceList(spec_version='1.0')
        rl.md_at = '2013-01-03T09:00:00Z'
        rl.add(Resource('http://example.com/res1'))
        rl.add(Resource('http://example.com/res2'))
        ex_xml = self._open_ex('resourcesync_ex_1').read()
        self._assert_xml_equal(rl.as_xml(), ex_xml)

    def test_build_ex_02(self):
        """Slightly more complex Resource List document"""
        rl = ResourceList(spec_version='1.0')
        rl.md_at = '2013-01-03T09:00:00Z'
        rl.add(Resource(uri='http://example.com/res1',
                        lastmod='2013-01-02T13:00:00Z',
                        md5='1584abdf8ebdc9802ac0c6a7402c03b6'))
        r2 = Resource(uri='http://example.com/res2',
                      lastmod='2013-01-02T14:00:00Z',
                      md5='1e0d5cb8ef6ba40c99b14c0237be735e')
        r2.link_set(rel="duplicate", href="http://mirror.example.com/res2")
        rl.add(r2)
        ex_xml = self._open_ex('resourcesync_ex_2').read()
        self._assert_xml_equal(rl.as_xml(), ex_xml)

    def test_build_ex_03(self):
        """Simple Change List document """
        cl = ChangeList(spec_version='1.0')
        cl.md_from = '2013-01-02T00:00:00Z'
        cl.md_until = '2013-01-03T00:00:00Z'
        cl.add(Resource(uri='http://example.com/res2.pdf',
                        lastmod='2013-01-02T13:00:00Z',
                        change="updated"))
        cl.add(Resource(uri='http://example.com/res3.tiff',
                        lastmod='2013-01-02T18:00:00Z',
                        change='deleted'))
        ex_xml = self._open_ex('resourcesync_ex_3').read()
        self._assert_xml_equal(cl.as_xml(), ex_xml)

    def test_build_ex_04(self):
        """Simple Resource Dump document """
        rd = ResourceDump(spec_version='1.0')
        rd.md_at = '2013-01-03T09:00:00Z'
        rd.add(Resource(uri='http://example.com/resourcedump.zip',
                        lastmod='2013-01-03T09:00:00Z'))
        ex_xml = self._open_ex('resourcesync_ex_4').read()
        self._assert_xml_equal(rd.as_xml(), ex_xml)

    def test_build_ex_05(self):
        """Simple Resource Dump Manifest document """
        rdm = ResourceDumpManifest(spec_version='1.0')
        rdm.md_at = '2013-01-03T09:00:00Z'
        rdm.add(Resource(uri='http://example.com/res1',
                         lastmod='2013-01-03T03:00:00Z',
                         md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                         path='/resources/res1'))
        rdm.add(Resource(uri='http://example.com/res2',
                         lastmod='2013-01-03T04:00:00Z',
                         md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                         path='/resources/res2'))
        ex_xml = self._open_ex('resourcesync_ex_5').read()
        self._assert_xml_equal(rdm.as_xml(), ex_xml)

    def test_build_ex_06(self):
        """Simple Capability List document """
        cl = CapabilityList(spec_version='1.0')
        cl.describedby = 'http://example.com/info_about_set1_of_resources.xml'
        cl.up = 'http://example.com/resourcesync_description.xml'
        cl.add_capability(
            uri='http://example.com/dataset1/resourcelist.xml', name='resourcelist')
        cl.add_capability(
            uri='http://example.com/dataset1/resourcedump.xml', name='resourcedump')
        cl.add_capability(
            uri='http://example.com/dataset1/changelist.xml', name='changelist')
        ex_xml = self._open_ex('resourcesync_ex_6').read()
        self._assert_xml_equal(cl.as_xml(), ex_xml)

    def test_build_ex_07(self):
        """A Source Description document """
        sd = SourceDescription(spec_version='1.0')
        sd.describedby = 'http://example.com/info-about-source.xml'
        r = Resource(uri='http://example.com/dataset1/capabilitylist.xml',
                     capability='capabilitylist')
        r.link_set(rel='describedby',
                   href='http://example.com/info_about_set1_of_resources.xml')
        sd.add(r)
        ex_xml = self._open_ex('resourcesync_ex_7').read()
        self._assert_xml_equal(sd.as_xml(), ex_xml)

    def test_build_ex_08(self):
        """Simple Resource List Index document

        This is not something that would usually be created directly
        but instead would be created as part of the process of
        writing a large Resource List in multiple files. However,
        it is possible to create manually.
        """
        rli = ResourceList(spec_version='1.0')
        rli.sitemapindex = True
        rli.md_at = '2013-01-03T09:00:00Z'
        rli.add(Resource(uri='http://example.com/resourcelist-part1.xml'))
        rli.add(Resource(uri='http://example.com/resourcelist-part2.xml'))
        ex_xml = self._open_ex('resourcesync_ex_8').read()
        self._assert_xml_equal(rli.as_xml(), ex_xml)

    # Examples 9, 10, 11 in the spec are not XML documents

    def test_build_ex_12(self):
        """Source Description document with describedby links"""
        sd = SourceDescription(spec_version='1.0')
        sd.describedby = 'http://example.com/info_about_source.xml'
        cl1 = CapabilityList(uri='http://example.com/capabilitylist1.xml')
        cl1.describedby = 'http://example.com/info_about_set1_of_resources.xml'
        sd.add_capability_list(cl1)
        cl2 = CapabilityList(uri='http://example.com/capabilitylist2.xml')
        cl2.describedby = 'http://example.com/info_about_set2_of_resources.xml'
        sd.add_capability_list(cl2)
        cl3 = CapabilityList(uri='http://example.com/capabilitylist3.xml')
        cl3.describedby = 'http://example.com/info_about_set3_of_resources.xml'
        sd.add_capability_list(cl3)
        ex_xml = self._open_ex('resourcesync_ex_12').read()
        self._assert_xml_equal(sd.as_xml(), ex_xml)

    def test_build_ex_13(self):
        """Capability List document with 4 entries"""
        cl = CapabilityList(spec_version='1.0')
        cl.describedby = 'http://example.com/info_about_set1_of_resources.xml'
        cl.up = 'http://example.com/resourcesync_description.xml'
        cl.add_capability(capability=ResourceList(
            uri='http://example.com/dataset1/resourcelist.xml'))
        cl.add_capability(capability=ResourceDump(
            uri='http://example.com/dataset1/resourcedump.xml'))
        cl.add_capability(capability=ChangeList(
            uri='http://example.com/dataset1/changelist.xml'))
        cl.add_capability(capability=ChangeDump(
            uri='http://example.com/dataset1/changedump.xml'))
        ex_xml = self._open_ex('resourcesync_ex_13').read()
        self._assert_xml_equal(cl.as_xml(), ex_xml)

    def test_build_ex_14(self):
        """Resource List with 2 entries and some metadata"""
        rl = ResourceList(spec_version='1.0')
        rl.up = 'http://example.com/dataset1/capabilitylist.xml'
        rl.md_at = "2013-01-03T09:00:00Z"
        rl.md_completed = "2013-01-03T09:01:00Z"
        rl.add(Resource(uri='http://example.com/res1',
                        lastmod='2013-01-02T13:00:00Z',
                        md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                        length=8876,
                        mime_type="text/html"))
        rl.add(Resource(uri='http://example.com/res2',
                        lastmod='2013-01-02T14:00:00Z',
                        md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                        sha256='854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784',
                        length=14599,
                        mime_type="application/pdf"))
        ex_xml = self._open_ex('resourcesync_ex_14').read()
        self._assert_xml_equal(rl.as_xml(), ex_xml)

    def test_build_ex_15(self):
        """Resource List Index with metadata"""
        rl = ResourceList(
            resources_class=ResourceListOrdered,
            spec_version='1.0')  # order in example is non-canonical
        rl.sitemapindex = True
        rl.up = 'http://example.com/dataset1/capabilitylist.xml'
        rl.md_at = "2013-01-03T09:00:00Z"
        rl.md_completed = "2013-01-03T09:10:00Z"
        rl.add(Resource(uri='http://example.com/resourcelist1.xml',
                        md_at='2013-01-03T09:00:00Z'))
        rl.add(Resource(uri='http://example.com/resourcelist2.xml',
                        md_at='2013-01-03T09:03:00Z'))
        rl.add(Resource(uri='http://example.com/resourcelist3.xml',
                        md_at='2013-01-03T09:07:00Z'))
        ex_xml = self._open_ex('resourcesync_ex_15').read()
        self._assert_xml_equal(rl.as_xml(), ex_xml)

    def test_build_ex_16(self):
        rl = ResourceList(spec_version='1.0')
        rl.up = 'http://example.com/dataset1/capabilitylist.xml'
        rl.index = 'http://example.com/dataset1/resourcelist-index.xml'
        rl.md_at = "2013-01-03T09:00:00Z"
        rl.add(Resource(uri='http://example.com/res3',
                        lastmod='2013-01-02T13:00:00Z',
                        md5='1584abdf8ebdc9802ac0c6a7402c8753',
                        length=4385,
                        mime_type="application/pdf"))
        rl.add(Resource(uri='http://example.com/res4',
                        lastmod='2013-01-02T14:00:00Z',
                        md5='4556abdf8ebdc9802ac0c6a7402c9881',
                        length=883,
                        mime_type="image/png"))
        ex_xml = self._open_ex('resourcesync_ex_16').read()
        self._assert_xml_equal(rl.as_xml(), ex_xml)

    def test_build_ex_17(self):
        """Resource Dump with 3 entries and some metadata"""
        rd = ResourceDump(spec_version='1.0')
        rd.up = 'http://example.com/dataset1/capabilitylist.xml'
        rd.md_at = "2013-01-03T09:00:00Z"
        rd.md_completed = "2013-01-03T09:04:00Z"
        z1 = Resource(uri='http://example.com/resourcedump-part1.zip',
                      mime_type="application/zip",
                      length=4765,
                      md_at="2013-01-03T09:00:00Z",
                      md_completed="2013-01-03T09:02:00Z")
        z1.link_set(rel="contents",
                    href="http://example.com/resourcedump_manifest-part1.xml",
                    mime_type="application/xml")
        rd.add(z1)
        z2 = Resource(uri='http://example.com/resourcedump-part2.zip',
                      mime_type="application/zip",
                      length=9875,
                      md_at="2013-01-03T09:01:00Z",
                      md_completed="2013-01-03T09:03:00Z")
        z2.link_set(rel="contents",
                    href="http://example.com/resourcedump_manifest-part2.xml",
                    mime_type="application/xml")
        rd.add(z2)
        z3 = Resource(uri='http://example.com/resourcedump-part3.zip',
                      mime_type="application/zip",
                      length=2298,
                      md_at="2013-01-03T09:03:00Z",
                      md_completed="2013-01-03T09:04:00Z")
        z3.link_set(rel="contents",
                    href="http://example.com/resourcedump_manifest-part3.xml",
                    mime_type="application/xml")
        rd.add(z3)
        ex_xml = self._open_ex('resourcesync_ex_17').read()
        self._assert_xml_equal(rd.as_xml(), ex_xml)

    def test_build_ex_18(self):
        """Resource Dump Manifest with 2 entries and some metadata"""
        rdm = ResourceDumpManifest(spec_version='1.0')
        rdm.up = 'http://example.com/dataset1/capabilitylist.xml'
        rdm.md_at = "2013-01-03T09:00:00Z"
        rdm.md_completed = "2013-01-03T09:02:00Z"
        rdm.add(Resource(uri='http://example.com/res1',
                         lastmod='2013-01-02T13:00:00Z',
                         md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                         length=8876,
                         mime_type='text/html',
                         path='/resources/res1'))
        rdm.add(Resource(uri='http://example.com/res2',
                         lastmod='2013-01-02T14:00:00Z',
                         md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                         sha256='854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784',
                         length=14599,
                         mime_type='application/pdf',
                         path='/resources/res2'))
        ex_xml = self._open_ex('resourcesync_ex_18').read()
        self._assert_xml_equal(rdm.as_xml(), ex_xml)

    def test_build_ex_19(self):
        """Change List with 4 changes, 'open' as no until"""
        cl = ChangeList(spec_version='1.0')
        cl.up = 'http://example.com/dataset1/capabilitylist.xml'
        cl.md_from = "2013-01-03T00:00:00Z"
        cl.add(Resource(uri='http://example.com/res1.html',
                        lastmod='2013-01-03T11:00:00Z',
                        change='created'))
        cl.add(Resource(uri='http://example.com/res2.pdf',
                        lastmod='2013-01-03T13:00:00Z',
                        change='updated'))
        cl.add(Resource(uri='http://example.com/res3.tiff',
                        lastmod='2013-01-03T18:00:00Z',
                        change='deleted'))
        cl.add(Resource(uri='http://example.com/res2.pdf',
                        lastmod='2013-01-03T21:00:00Z',
                        change='updated'))
        ex_xml = self._open_ex('resourcesync_ex_19').read()
        self._assert_xml_equal(cl.as_xml(), ex_xml)

    def test_build_ex_20(self):
        """Change List Index listing 3 Change Lists, the last one 'open'"""
        cl = ChangeListArchive(
            resources_class=ResourceListOrdered,   # order in example is non-canonical
            spec_version='1.0')
        cl.sitemapindex = True
        cl.capability_name = 'changelist'
        cl.up = 'http://example.com/dataset1/capabilitylist.xml'
        cl.md_from = "2013-01-01T00:00:00Z"
        cl.add(Resource(uri='http://example.com/20130101-changelist.xml',
                        md_from='2013-01-01T00:00:00Z',
                        md_until='2013-01-02T00:00:00Z'))
        cl.add(Resource(uri='http://example.com/20130102-changelist.xml',
                        md_from='2013-01-02T00:00:00Z',
                        md_until='2013-01-03T00:00:00Z'))
        cl.add(Resource(uri='http://example.com/20130103-changelist.xml',
                        md_from='2013-01-03T00:00:00Z'))
        ex_xml = self._open_ex('resourcesync_ex_20').read()
        self._assert_xml_equal(cl.as_xml(), ex_xml)

    def test_build_ex_21(self):
        """Change List which points back to index"""
        cl = ChangeList(spec_version='1.0')
        cl.up = 'http://example.com/dataset1/capabilitylist.xml'
        cl.index = 'http://example.com/dataset1/changelist.xml'
        cl.md_from = "2013-01-02T00:00:00Z"
        cl.md_until = "2013-01-03T00:00:00Z"
        cl.add(Resource(uri='http://example.com/res7.html',
                        lastmod='2013-01-02T12:00:00Z',
                        change='created'))
        cl.add(Resource(uri='http://example.com/res9.pdf',
                        lastmod='2013-01-02T13:00:00Z',
                        change='updated'))
        cl.add(Resource(uri='http://example.com/res5.tiff',
                        lastmod='2013-01-02T19:00:00Z',
                        change='deleted'))
        cl.add(Resource(uri='http://example.com/res7.html',
                        lastmod='2013-01-02T20:00:00Z',
                        change='updated'))
        ex_xml = self._open_ex('resourcesync_ex_21').read()
        self._assert_xml_equal(cl.as_xml(), ex_xml)

    def test_build_ex_22(self):
        """Change Dump with three dump files"""
        cd = ChangeDump(spec_version='1.0')
        cd.up = 'http://example.com/dataset1/capabilitylist.xml'
        cd.md_from = "2013-01-01T00:00:00Z"
        z1 = Resource(uri='http://example.com/20130101-changedump.zip',
                      lastmod='2013-01-01T23:59:59Z',
                      length=3109,
                      md_from="2013-01-01T00:00:00Z",
                      md_until="2013-01-02T00:00:00Z",
                      mime_type="application/zip")
        z1.contents = 'http://example.com/20130101-changedump-manifest.xml'
        z2 = Resource(uri='http://example.com/20130102-changedump.zip',
                      lastmod='2013-01-02T23:59:59Z',
                      length=6629,
                      md_from="2013-01-02T00:00:00Z",
                      md_until="2013-01-03T00:00:00Z",
                      mime_type="application/zip")
        z2.contents = 'http://example.com/20130102-changedump-manifest.xml'
        z3 = Resource(uri='http://example.com/20130103-changedump.zip',
                      lastmod='2013-01-03T23:59:59Z',
                      length=8124,
                      md_from="2013-01-03T00:00:00Z",
                      md_until="2013-01-04T00:00:00Z",
                      mime_type="application/zip")
        z3.contents = 'http://example.com/20130103-changedump-manifest.xml'
        cd.add([z1, z2, z3])
        ex_xml = self._open_ex('resourcesync_ex_22').read()
        self._assert_xml_equal(cd.as_xml(), ex_xml)

    def test_build_ex_23(self):
        cdm = ChangeDumpManifest(spec_version='1.0')
        cdm.up = "http://example.com/dataset1/capabilitylist.xml"
        cdm.md_from = "2013-01-02T00:00:00Z"
        cdm.md_until = "2013-01-03T00:00:00Z"
        cdm.add(Resource(uri="http://example.com/res7.html",
                         lastmod="2013-01-02T12:00:00Z",
                         change="created",
                         md5="1c1b0e264fa9b7e1e9aa6f9db8d6362b",
                         length=4339,
                         mime_type="text/html",
                         path="/changes/res7.html"))
        cdm.add(Resource(uri="http://example.com/res9.pdf",
                         lastmod="2013-01-02T13:00:00Z",
                         change="updated",
                         md5="f906610c3d4aa745cb2b986f25b37c5a",
                         length=38297,
                         mime_type="application/pdf",
                         path="/changes/res9.pdf"))
        cdm.add(Resource(uri="http://example.com/res5.tiff",
                         lastmod="2013-01-02T19:00:00Z",
                         change="deleted"))
        cdm.add(Resource(uri="http://example.com/res7.html",
                         lastmod="2013-01-02T20:00:00Z",
                         change="updated",
                         md5="0988647082c8bc51778894a48ec3b576",
                         length="5426",  # should also take string
                         mime_type="text/html",
                         path="/changes/res7-v2.html"))
        self._assert_xml_equal_ex(cdm.as_xml(), 'resourcesync_ex_23')

    def test_build_ex_24(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://example.com/res1",
                      lastmod="2013-01-03T18:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="text/html")
        # Resource.link_set with add or change link depending on one with
        # the particular rel exists unless allow_duplicates=True.
        # Resource.link_add will always add. Test both here...
        c1.link_set(rel="duplicate",
                    href="http://mirror1.example.com/res1",
                    pri="1",
                    modified="2013-01-03T18:00:00Z")
        c1.link_set(rel="duplicate",
                    href="http://mirror2.example.com/res1",
                    pri="2",
                    modified="2013-01-03T18:00:00Z",
                    allow_duplicates=True)
        c1.link_add(rel="duplicate",
                    href="gsiftp://gridftp.example.com/res1",
                    pri="3",
                    modified="2013-01-03T18:00:00Z")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_24')

    def test_build_ex_25(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T11:00:00Z"
        c1 = Resource(uri="http://example.com/res1",
                      lastmod="2013-01-03T18:00:00Z",
                      change="updated")
        c1.link_add(rel="alternate",
                    href="http://example.com/res1.html",
                    modified="2013-01-03T18:00:00Z",
                    type="text/html")  # FIXME - inconsistent
        c1.link_add(rel="alternate",
                    href="http://example.com/res1.pdf",
                    modified="2013-01-03T18:00:00Z",
                    type="application/pdf")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_25')

    def test_build_ex_26(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://example.com/res1.html",
                      lastmod="2013-01-03T18:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876)
        c1.link_add(rel="canonical",
                    href="http://example.com/res1",
                    modified="2013-01-03T18:00:00Z")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_26')

    def test_build_ex_27(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://example.com/res4",
                      lastmod="2013-01-03T17:00:00Z",
                      change="updated",
                      sha256="f4OxZX_x_DFGFDgghgdfb6rtSx-iosjf6735432nklj",
                      length=56778,
                      mime_type="application/json")
        c1.link_set(rel="http://www.openarchives.org/rs/terms/patch",
                    href="http://example.com/res4-json-patch",
                    modified="2013-01-03T17:00:00Z",
                    hash="sha-256:y66dER_t_HWEIKpesdkeb7rtSc-ippjf9823742opld",  # FIXME - inconsistent
                    length=73,
                    type="application/json-patch")
        c2 = Resource(uri="http://example.com/res5-full.tiff",
                      lastmod="2013-01-03T18:00:00Z",
                      change="updated",
                      sha256="f4OxZX_x_FO5LcGBSKHWXfwtSx-j1ncoSt3SABJtkGk",
                      length="9788456778",
                      mime_type="image/tiff")
        c2.link_set(rel="http://www.openarchives.org/rs/terms/patch",
                    href="http://example.com/res5-diff",
                    modified="2013-01-03T18:00:00Z",
                    hash="sha-256:h986gT_t_87HTkjHYE76G558hY-jdfgy76t55sadJUYT",
                    length=4533,
                    type="application/x-tiff-diff")
        cl.add([c1, c2])
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_27')

    def test_build_ex_28(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://example.com/res2.pdf",
                      lastmod="2013-01-03T18:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="application/pdf")
        c1.link_set(rel="describedby",
                    href="http://example.com/res2_dublin-core_metadata.xml",
                    modified="2013-01-01T12:00:00Z",
                    type="application/xml")
        c2 = Resource(uri="http://example.com/res2_dublin-core_metadata.xml",
                      lastmod="2013-01-03T19:00:00Z",
                      change="updated",
                      mime_type="application/xml")
        c2.link_set(rel="describes",
                    href="http://example.com/res2.pdf",
                    modified="2013-01-03T18:00:00Z",
                    hash="md5:1584abdf8ebdc9802ac0c6a7402c03b6",
                    length="8876",
                    type="application/pdf")
        c2.link_set(rel="profile",
                    href="http://purl.org/dc/elements/1.1/")
        cl.add([c1, c2])
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_28')

    def test_build_ex_29(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://example.com/res1",
                      lastmod="2013-01-03T18:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="text/html")
        c1.link_add(rel="memento",
                    href="http://example.com/20130103070000/res1",
                    modified="2013-01-02T18:00:00Z",
                    hash="md5:1584abdf8ebdc9802ac0c6a7402c03b6",
                    length="8876",
                    type="text/html")
        c1.link_add(rel="timegate",
                    href="http://example.com/timegate/http://example.com/res1")
        c1.link_add(rel="timemap",
                    href="http://example.com/timemap/http://example.com/res1",
                    type="application/link-format")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_29')

    def test_build_ex_30(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://example.com/res1",
                      lastmod="2013-01-03T07:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="text/html")
        c1.link_add(rel="collection",
                    href="http://example.com/aggregation/0601007")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_30')

    def test_build_ex_31(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T00:00:00Z"
        c1 = Resource(uri="http://original.example.com/res1.html",
                      lastmod="2013-01-03T07:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="text/html")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_31')

    def test_build_ex_32(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://aggregator1.example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T11:00:00Z"
        c1 = Resource(uri="http://aggregator1.example.com/res1.html",
                      lastmod="2013-01-03T20:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="text/html")
        c1.link_add(rel="via",
                    href="http://original.example.com/res1.html",
                    modified="2013-01-03T07:00:00Z",
                    hash="md5:1584abdf8ebdc9802ac0c6a7402c03b6",
                    length="8876",
                    type="text/html")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_32')

    def test_build_ex_33(self):
        cl = ChangeList(spec_version='1.0')
        cl.up = "http://aggregator2.example.com/dataset1/capabilitylist.xml"
        cl.md_from = "2013-01-03T12:00:00Z"
        c1 = Resource(uri="http://aggregator2.example.com/res1.html",
                      lastmod="2013-01-04T09:00:00Z",
                      change="updated",
                      md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                      length=8876,
                      mime_type="text/html")
        c1.link_add(rel="via",
                    href="http://original.example.com/res1.html",
                    modified="2013-01-03T07:00:00Z",
                    hash="md5:1584abdf8ebdc9802ac0c6a7402c03b6",
                    length="8876",
                    type="text/html")
        cl.add(c1)
        self._assert_xml_equal_ex(cl.as_xml(), 'resourcesync_ex_33')

    # Archives tests

    def test_build_archives_ex_3_1(self):
        """Resource List Archive listing 3 Resource Lists"""
        rla = ResourceListArchive(spec_version='1.0')
        rla.up = 'http://example.com/dataset1/capabilitylist.xml'
        rla.add(Resource(uri='http://example.com/resourcelist1.xml',
                         md_at='2012-11-03T09:00:00Z'))
        rla.add(Resource(uri='http://example.com/resourcelist2.xml',
                         md_at='2012-12-03T09:00:00Z'))
        rla.add(Resource(uri='http://example.com/resourcelist3.xml',
                         md_at='2013-01-03T09:00:00Z'))
        ex_xml = self._open_ex('archives_ex_3_1').read()
        self._assert_xml_equal(rla.as_xml(), ex_xml)

    def test_build_archives_ex_3_2(self):
        """Resource List Archive Index listing 2 component Resource List Archives"""
        rlai = ResourceListArchive(spec_version='1.0')
        rlai.sitemapindex = True
        rlai.up = 'http://example.com/dataset1/capabilitylist.xml'
        rlai.add(Resource(uri='http://example.com/resourcelistarchive00001.xml'))
        rlai.add(Resource(uri='http://example.com/resourcelistarchive00002.xml'))
        ex_xml = self._open_ex('archives_ex_3_2').read()
        self._assert_xml_equal(rlai.as_xml(), ex_xml)

    def test_build_archives_ex_4_1(self):
        """Resource Dump Archive listing 2 Resource Dumps"""
        rda = ResourceDumpArchive(spec_version='1.0')
        rda.up = 'http://example.com/dataset1/capabilitylist.xml'
        rda.add(Resource(uri='http://example.com/resourcedump1.xml',
                         lastmod='2012-11-03T09:05:42Z',
                         md_at="2012-11-03T09:00:00Z",
                         md_completed="2012-11-03T09:05:01Z"))

        rda.add(Resource(uri='http://example.com/resourcedump2.xml',
                         lastmod='2012-12-03T09:06:12Z',
                         md_at="2012-12-03T09:00:00Z",
                         md_completed="2012-12-03T09:05:17Z"))
        ex_xml = self._open_ex('archives_ex_4_1').read()
        self._assert_xml_equal(rda.as_xml(), ex_xml)

    def test_build_archives_ex_5_1(self):
        """Change List Archive listing 3 Change Lists"""
        cla = ChangeListArchive(spec_version='1.0')
        cla.up = 'http://example.com/dataset1/capabilitylist.xml'
        cla.add(Resource(uri='http://example.com/changelist1.xml',
                         md_from='2013-01-01T09:00:00Z',
                         md_until='2013-01-02T09:00:00Z'))
        cla.add(Resource(uri='http://example.com/changelist2.xml',
                         md_from='2013-01-02T09:00:00Z',
                         md_until='2013-01-03T09:00:00Z'))
        cla.add(Resource(uri='http://example.com/changelist3.xml',
                         md_from='2013-01-03T09:00:00Z',
                         md_until='2013-01-04T09:00:00Z'))
        ex_xml = self._open_ex('archives_ex_5_1').read()
        self._assert_xml_equal(cla.as_xml(), ex_xml)

    def test_build_archives_ex_6_1(self):
        """Change Dump Archive listing 2 Change Dumps"""
        cda = ChangeDumpArchive(spec_version='1.0')
        cda.up = 'http://example.com/dataset1/capabilitylist.xml'
        cda.add(Resource(uri='http://example.com/changedump-w1.xml',
                         lastmod='2012-12-20T09:02:43Z',
                         md_from="2012-01-13T09:00:00Z",
                         md_until="2013-01-20T09:00:00Z"))
        cda.add(Resource(uri='http://example.com/changedump-w2.xml',
                         lastmod='2012-12-27T09:01:57Z',
                         md_from="2012-01-20T09:00:00Z",
                         md_until="2013-01-27T09:00:00Z"))
        ex_xml = self._open_ex('archives_ex_6_1').read()
        self._assert_xml_equal(cda.as_xml(), ex_xml)
