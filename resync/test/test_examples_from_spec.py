"""Tests on the examples in the specification documents
"""
import re
import sys
import unittest
from resync.resource import Resource
from resync.source_description import SourceDescription
from resync.capability_list import CapabilityList
from resync.resource_list import ResourceList,ResourceListOrdered
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.change_list import ChangeList
from resync.change_dump import ChangeDump
from resync.archives import ResourceListArchive,ResourceDumpArchive,ChangeListArchive,ChangeDumpArchive
from resync.sitemap import Sitemap

class TestExamplesFromSpec(unittest.TestCase):

    def test_all_simple_read(self):
        """Just try to read each one"""
        for ex in ('archives_ex_2_1','archives_ex_2_2',
                   'archives_ex_3_1','archives_ex_3_2',
                   'archives_ex_4_1',
                   'archives_ex_5_1',
                   'archives_ex_6_1',
                   'resourcesync_ex_2_1','resourcesync_ex_2_2','resourcesync_ex_2_3',
                   'resourcesync_ex_2_4','resourcesync_ex_2_5','resourcesync_ex_2_6',
                   'resourcesync_ex_2_7','resourcesync_ex_2_8',
                   'resourcesync_ex_6_1',
                   'resourcesync_ex_7_1',
                   'resourcesync_ex_8_1','resourcesync_ex_8_2','resourcesync_ex_8_3',
                   'resourcesync_ex_9_1','resourcesync_ex_9_2',
                   'resourcesync_ex_10_1','resourcesync_ex_10_2','resourcesync_ex_10_3',
                   'resourcesync_ex_11_1','resourcesync_ex_11_2',
                   'resourcesync_ex_12_1','resourcesync_ex_12_2','resourcesync_ex_12_3',
                   'resourcesync_ex_12_4','resourcesync_ex_12_5','resourcesync_ex_12_6',
                   'resourcesync_ex_12_7','resourcesync_ex_12_8','resourcesync_ex_12_9',
                   'resourcesync_ex_12_10' ):
            s=Sitemap()
            fh = self._open_ex(ex)
            si = s.parse_xml( fh=fh )

    def test_ex_2_1(self):
        """resourcesync_ex2_1 is a simple resource_list with 2 resources, no metadata"""
        rl=ResourceList()
        rl.parse(uri='resync/test/testdata/examples_from_spec/resourcesync_ex_2_1.xml')
        self.assertEqual( rl.capability, 'resourcelist' )
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( rl.resources['http://example.com/res1'].lastmod, None )

    def test_ex_2_2(self):
        """resourcesync_ex_2_2 is a simple resource_list with 2 resources, some metadata"""
        rl=ResourceList()
        rl.parse(uri='resync/test/testdata/examples_from_spec/resourcesync_ex_2_2.xml')
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( rl.resources['http://example.com/res1'].lastmod, '2013-01-02T13:00:00Z' )
        self.assertEqual( rl.resources['http://example.com/res2'].lastmod, '2013-01-02T14:00:00Z' )
        self.assertEqual( rl.resources['http://example.com/res1'].md5, '1584abdf8ebdc9802ac0c6a7402c03b6' )
        self.assertEqual( rl.resources['http://example.com/res2'].md5, '1e0d5cb8ef6ba40c99b14c0237be735e' )

    def test_ex_2_3(self):
        """resourcesync_ex_2_3 is a simple change_list with 2 resources"""
        cl=ChangeList()
        cl.parse('resync/test/testdata/examples_from_spec/resourcesync_ex_2_3.xml')
        self.assertEqual( len(cl.resources), 2, '2 resources')
        sms = sorted(cl.uris())
        self.assertEqual( sms, ['http://example.com/res2.pdf','http://example.com/res3.tiff'] )
        self.assertEqual( cl.resources[0].lastmod, '2013-01-02T13:00:00Z' )
        self.assertEqual( cl.resources[1].lastmod, '2013-01-02T18:00:00Z' )
        self.assertEqual( cl.resources[0].change, 'updated' )
        self.assertEqual( cl.resources[1].change, 'deleted' )

    def test_ex_2_4(self):
        """resourcesync_ex_2_4 is a simple resource dump with one ZIP listed"""
        rd=ResourceDump()
        rd.parse('resync/test/testdata/examples_from_spec/resourcesync_ex_2_4.xml')
        self.assertEqual( len(rd.resources), 1, '1 resources')
        self.assertTrue( 'http://example.com/resourcedump.zip' in rd.resources )
        self.assertEqual( rd.resources['http://example.com/resourcedump.zip'].lastmod, '2013-01-03T09:00:00Z' )

    def test_ex_2_5(self):
        """resourcesync_ex_2_5 is a simple resource dump manifest with two files listed"""
        rdm=ResourceDumpManifest()
        rdm.parse('resync/test/testdata/examples_from_spec/resourcesync_ex_2_5.xml')
        self.assertEqual( len(rdm.resources), 2, '2 resources')
        sms = sorted(rdm.uris())
        self.assertEqual( sms, ['http://example.com/res1','http://example.com/res2'] )
        self.assertEqual( rdm.resources['http://example.com/res1'].lastmod, '2013-01-03T03:00:00Z' )
        self.assertEqual( rdm.resources['http://example.com/res1'].md5, '1584abdf8ebdc9802ac0c6a7402c03b6' )
        self.assertEqual( rdm.resources['http://example.com/res1'].path, '/resources/res1' )
        self.assertEqual( rdm.resources['http://example.com/res2'].lastmod, '2013-01-03T04:00:00Z' )
        self.assertEqual( rdm.resources['http://example.com/res2'].md5, '1e0d5cb8ef6ba40c99b14c0237be735e' )
        self.assertEqual( rdm.resources['http://example.com/res2'].path, '/resources/res2' )

    def test_ex_2_6(self):
        """resourcesync_ex_2_6 is a simple capability list with three capabilities"""
        capl=CapabilityList()
        capl.parse('resync/test/testdata/examples_from_spec/resourcesync_ex_2_6.xml')
        self.assertEqual( len(capl.resources), 3, '3 capabilities')
        # What capabilities are present?
        self.assertTrue( capl.has_capability('resourcelist') )
        self.assertEqual( capl.capability_info('resourcelist').uri, 'http://example.com/dataset1/resourcelist.xml')
        self.assertTrue( capl.has_capability('resourcedump') )
        self.assertEqual( capl.capability_info('resourcedump').uri, 'http://example.com/dataset1/resourcedump.xml')
        self.assertTrue( capl.has_capability('changelist') )
        self.assertEqual( capl.capability_info('changelist').uri, 'http://example.com/dataset1/changelist.xml')
        # Check some that aren't
        self.assertFalse( capl.has_capability() )
        self.assertFalse( capl.has_capability('bogus') )
        self.assertFalse( capl.has_capability('capabilitylist') )

    def test_ex_2_8(self):
        """resourcesync_ex2_8 is a simple Resource List Index with 2 Resource Lists"""
        rl=ResourceList()
        rl.read(uri='resync/test/testdata/examples_from_spec/resourcesync_ex_2_8.xml',index_only=True)
        self.assertEqual( rl.capability, 'resourcelist' )
        self.assertEqual( rl.md_at, '2013-01-03T09:00:00Z' )
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/resourcelist-part1.xml',
                                'http://example.com/resourcelist-part2.xml'] )

##### BUILD EXAMPLES #####

    def test_build_ex_2_1(self):
        """Simple Resource List document """
        rl = ResourceList()
        rl.md_at = '2013-01-03T09:00:00Z'
        rl.add( Resource('http://example.com/res1') )
        rl.add( Resource('http://example.com/res2') )
        ex_xml = self._open_ex('resourcesync_ex_2_1').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_2_2(self):
        """Slightly more complex Resource List document """
        rl = ResourceList()
        rl.md_at = '2013-01-03T09:00:00Z'
        rl.add( Resource(uri='http://example.com/res1',
                         lastmod='2013-01-02T13:00:00Z',
                         md5='1584abdf8ebdc9802ac0c6a7402c03b6') )
        r2 =  Resource(uri='http://example.com/res2',
                       lastmod='2013-01-02T14:00:00Z',
                       md5='1e0d5cb8ef6ba40c99b14c0237be735e')
        r2.link_add(rel="duplicate",href="http://mirror.example.com/res2")
        rl.add( r2 )
        ex_xml = self._open_ex('resourcesync_ex_2_2').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_2_3(self):
        """Simple Change List document """
        cl = ChangeList()
        cl.md_from = '2013-01-02T00:00:00Z'
        cl.md_until= '2013-01-03T00:00:00Z'
        cl.add( Resource(uri='http://example.com/res2.pdf',
                         lastmod='2013-01-02T13:00:00Z',
                         change="updated") )
        cl.add( Resource(uri='http://example.com/res3.tiff',
                         lastmod='2013-01-02T18:00:00Z',
                         change='deleted') )
        ex_xml = self._open_ex('resourcesync_ex_2_3').read()
        self._assert_xml_equal( cl.as_xml(), ex_xml )

    def test_build_ex_2_4(self):
        """Simple Resource Dump document """
        rd = ResourceDump()
        rd.md_at = '2013-01-03T09:00:00Z'
        rd.add( Resource(uri='http://example.com/resourcedump.zip',
                         lastmod='2013-01-03T09:00:00Z') )
        ex_xml = self._open_ex('resourcesync_ex_2_4').read()
        self._assert_xml_equal( rd.as_xml(), ex_xml )

    def test_build_ex_2_5(self):
        """Simple Resource Dump Manifest document """
        rdm = ResourceDumpManifest()
        rdm.md_at = '2013-01-03T09:00:00Z'
        rdm.add( Resource(uri='http://example.com/res1',
                          lastmod='2013-01-03T03:00:00Z',
                          md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                          path='/resources/res1') )
        rdm.add( Resource(uri='http://example.com/res2',
                          lastmod='2013-01-03T04:00:00Z',
                          md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                          path='/resources/res2') )
        ex_xml = self._open_ex('resourcesync_ex_2_5').read()
        self._assert_xml_equal( rdm.as_xml(), ex_xml )

    def test_build_ex_2_6(self):
        """Simple Capability List document """
        cl = CapabilityList()
        cl.describedby = 'http://example.com/info_about_set1_of_resources.xml'
        cl.up = 'http://example.com/resourcesync_description.xml'
        cl.add_capability( uri='http://example.com/dataset1/resourcelist.xml', name='resourcelist' )
        cl.add_capability( uri='http://example.com/dataset1/resourcedump.xml', name='resourcedump' )
        cl.add_capability( uri='http://example.com/dataset1/changelist.xml', name='changelist' )
        ex_xml = self._open_ex('resourcesync_ex_2_6').read()
        self._assert_xml_equal( cl.as_xml(), ex_xml )

    def test_build_ex_2_7(self):
        """A Source Description document """
        sd = SourceDescription()
        sd.describedby = 'http://example.com/info-about-source.xml'
        r = Resource( uri='http://example.com/dataset1/capabilitylist.xml',
                      capability='capabilitylist' )
        r.link_add( rel='describedby',
                    href='http://example.com/info_about_set1_of_resources.xml' )
        sd.add( r )
        ex_xml = self._open_ex('resourcesync_ex_2_7').read()
        self._assert_xml_equal( sd.as_xml(), ex_xml )

    def test_build_ex_2_8(self):
        """Simple Resource List Index document
        
        This is not something that would usually be created directly 
        but instead would be created as part of the process of 
        writing a large Resource List in multiple files. However,
        it is possible to create manually.
        """
        rli = ResourceList()
        rli.sitemapindex=True
        rli.md_at = '2013-01-03T09:00:00Z'
        rli.add( Resource(uri='http://example.com/resourcelist-part1.xml') )
        rli.add( Resource(uri='http://example.com/resourcelist-part2.xml') )
        ex_xml = self._open_ex('resourcesync_ex_2_8').read()
        self._assert_xml_equal( rli.as_xml(), ex_xml )

    def test_build_ex_6_1(self):
        """Source Description document with describedby links"""
        sd = SourceDescription()
        sd.describedby = 'http://example.com/info_about_source.xml'
        cl1 = CapabilityList( uri='http://example.com/capabilitylist1.xml' )
        cl1.describedby = 'http://example.com/info_about_set1_of_resources.xml'
        sd.add_capability_list( cl1 )
        cl2 = CapabilityList( uri='http://example.com/capabilitylist2.xml' )
        cl2.describedby = 'http://example.com/info_about_set2_of_resources.xml'
        sd.add_capability_list( cl2 )
        cl3 = CapabilityList( uri='http://example.com/capabilitylist3.xml' )
        cl3.describedby = 'http://example.com/info_about_set3_of_resources.xml'
        sd.add_capability_list( cl3 )
        ex_xml = self._open_ex('resourcesync_ex_6_1').read()
        self._assert_xml_equal( sd.as_xml(), ex_xml )

    def test_build_ex_7_1(self):
        """Capability List document with 4 entries"""
        cl = CapabilityList()
        cl.describedby = 'http://example.com/info_about_set1_of_resources.xml'
        cl.up = 'http://example.com/resourcesync_description.xml'
        cl.add_capability( capability=ResourceList( uri='http://example.com/dataset1/resourcelist.xml' ) )
        cl.add_capability( capability=ResourceDump( uri='http://example.com/dataset1/resourcedump.xml' ) )
        cl.add_capability( capability=ChangeList( uri='http://example.com/dataset1/changelist.xml' ) )
        cl.add_capability( capability=ChangeDump( uri='http://example.com/dataset1/changedump.xml' ) )
        ex_xml = self._open_ex('resourcesync_ex_7_1').read()
        self._assert_xml_equal( cl.as_xml(), ex_xml )

    def test_build_ex_8_1(self):
        """Resource List with 2 entries and some metadata"""
        rl = ResourceList()
        rl.up='http://example.com/dataset1/capabilitylist.xml'
        rl.md_at="2013-01-03T09:00:00Z"
        rl.md_completed="2013-01-03T09:01:00Z"
        rl.add( Resource( uri='http://example.com/res1',
                          lastmod='2013-01-02T13:00:00Z',
                          md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                          length=8876,
                          mime_type="text/html" ))
        rl.add( Resource( uri='http://example.com/res2',
                          lastmod='2013-01-02T14:00:00Z',
                          md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                          sha256='854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784',
                          length=14599,
                          mime_type="application/pdf" ))
        ex_xml = self._open_ex('resourcesync_ex_8_1').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_8_2(self):
        """Resource List Index with metadata"""
        rl = ResourceList(resources_class=ResourceListOrdered) #order in example is non-canonical
        rl.sitemapindex=True
        rl.up='http://example.com/dataset1/capabilitylist.xml'
        rl.md_at="2013-01-03T09:00:00Z"
        rl.md_completed="2013-01-03T09:10:00Z"
        rl.add( Resource( uri='http://example.com/resourcelist1.xml',
                          md_at='2013-01-03T09:00:00Z' ))
        rl.add( Resource( uri='http://example.com/resourcelist2.xml',
                          md_at='2013-01-03T09:03:00Z' ))
        rl.add( Resource( uri='http://example.com/resourcelist3.xml',
                          md_at='2013-01-03T09:07:00Z' ))
        ex_xml = self._open_ex('resourcesync_ex_8_2').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_8_3(self):
        rl = ResourceList()
        rl.up = 'http://example.com/dataset1/capabilitylist.xml'
        rl.index = 'http://example.com/dataset1/resourcelist-index.xml'
        rl.md_at="2013-01-03T09:00:00Z"
        rl.add( Resource( uri='http://example.com/res3',
                          lastmod='2013-01-02T13:00:00Z',
                          md5='1584abdf8ebdc9802ac0c6a7402c8753',
                          length=4385,
                          mime_type="application/pdf" ))
        rl.add( Resource( uri='http://example.com/res4',
                          lastmod='2013-01-02T14:00:00Z',
                          md5='4556abdf8ebdc9802ac0c6a7402c9881',
                          length=883,
                          mime_type="image/png" ))
        ex_xml = self._open_ex('resourcesync_ex_8_3').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_9_1(self):
        """Resource Dump with 3 entries and some metadata"""
        rd = ResourceDump()
        rd.up='http://example.com/dataset1/capabilitylist.xml'
        rd.md_at="2013-01-03T09:00:00Z"
        rd.md_completed="2013-01-03T09:04:00Z"
        z1 = Resource( uri='http://example.com/resourcedump-part1.zip',
                       mime_type="application/zip",
                       length=4765,
                       md_at="2013-01-03T09:00:00Z",
                       md_completed="2013-01-03T09:02:00Z" )
        z1.link_add( rel="contents",
                     href="http://example.com/resourcedump_manifest-part1.xml",
                     mime_type="application/xml" )
        rd.add( z1 )
        z2 = Resource( uri='http://example.com/resourcedump-part2.zip',
                       mime_type="application/zip",
                       length=9875,
                       md_at="2013-01-03T09:01:00Z",
                       md_completed="2013-01-03T09:03:00Z" )
        z2.link_add( rel="contents",
                     href="http://example.com/resourcedump_manifest-part2.xml",
                     mime_type="application/xml" )
        rd.add( z2 )
        z3 = Resource( uri='http://example.com/resourcedump-part3.zip',
                       mime_type="application/zip",
                       length=2298,
                       md_at="2013-01-03T09:03:00Z",
                       md_completed="2013-01-03T09:04:00Z" )
        z3.link_add( rel="contents",
                     href="http://example.com/resourcedump_manifest-part3.xml",
                     mime_type="application/xml" )
        rd.add( z3 )
        ex_xml = self._open_ex('resourcesync_ex_9_1').read()
        self._assert_xml_equal( rd.as_xml(), ex_xml )

    def test_build_ex_9_2(self):
        """Resource Dump Manifest with 2 entries and some metadata"""
        rdm = ResourceDumpManifest()
        rdm.up='http://example.com/dataset1/capabilitylist.xml'
        rdm.md_at="2013-01-03T09:00:00Z"
        rdm.md_completed="2013-01-03T09:02:00Z"
        rdm.add( Resource( uri='http://example.com/res1',
                           lastmod='2013-01-02T13:00:00Z',
                           md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                           length=8876,
                           mime_type='text/html',
                           path='/resources/res1') )
        rdm.add( Resource( uri='http://example.com/res2',
                           lastmod='2013-01-02T14:00:00Z',
                           md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                           sha256='854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784',
                           length=14599,
                           mime_type='application/pdf',
                           path='/resources/res2') )
        ex_xml = self._open_ex('resourcesync_ex_9_2').read()
        self._assert_xml_equal( rdm.as_xml(), ex_xml )

    def test_build_ex_10_1(self):
        """Change List with 4 changes, 'open' as no until"""
        cl = ChangeList()
        cl.up = 'http://example.com/dataset1/capabilitylist.xml'
        cl.md_from="2013-01-03T00:00:00Z"
        cl.add( Resource( uri='http://example.com/res1.html',
                          lastmod='2013-01-03T11:00:00Z',
                          change='created' ) )
        cl.add( Resource( uri='http://example.com/res2.pdf',
                          lastmod='2013-01-03T13:00:00Z',
                          change='updated' ) )
        cl.add( Resource( uri='http://example.com/res3.tiff',
                          lastmod='2013-01-03T18:00:00Z',
                          change='deleted' ) )
        cl.add( Resource( uri='http://example.com/res2.pdf',
                          lastmod='2013-01-03T21:00:00Z',
                          change='updated' ) )
        ex_xml = self._open_ex('resourcesync_ex_10_1').read()
        self._assert_xml_equal( cl.as_xml(), ex_xml )

    def test_build_ex_10_2(self):
        """Change List Index listing 3 Change Lists, the last one 'open'"""
        cl = ChangeListArchive(resources_class=ResourceListOrdered) #order in example is non-canonical   
        cl.sitemapindex=True
        cl.capability_name='changelist'
        cl.up = 'http://example.com/dataset1/capabilitylist.xml'
        cl.md_from="2013-01-01T00:00:00Z"
        cl.add( Resource( uri='http://example.com/20130101-changelist.xml',
                          md_from='2013-01-01T00:00:00Z',
                          md_until='2013-01-02T00:00:00Z') )
        cl.add( Resource( uri='http://example.com/20130102-changelist.xml',
                          md_from='2013-01-02T00:00:00Z',
                          md_until='2013-01-03T00:00:00Z') )
        cl.add( Resource( uri='http://example.com/20130103-changelist.xml',
                          md_from='2013-01-03T00:00:00Z') )
        ex_xml = self._open_ex('resourcesync_ex_10_2').read()
        self._assert_xml_equal( cl.as_xml(), ex_xml )

    def test_build_archives_ex_3_1(self):
        """Resource List Archive listing 3 Resource Lists"""
        rla = ResourceListArchive()
        rla.up = 'http://example.com/dataset1/capabilitylist.xml'
        rla.add( Resource( uri='http://example.com/resourcelist1.xml',
                           md_at='2012-11-03T09:00:00Z') )
        rla.add( Resource( uri='http://example.com/resourcelist2.xml',
                           md_at='2012-12-03T09:00:00Z') )
        rla.add( Resource( uri='http://example.com/resourcelist3.xml',
                           md_at='2013-01-03T09:00:00Z') )
        ex_xml = self._open_ex('archives_ex_3_1').read()
        self._assert_xml_equal( rla.as_xml(), ex_xml )

    def test_build_archives_ex_3_2(self):
        """Resource List Archive Index listing 2 component Resource List Archives"""
        rlai = ResourceListArchive()
        rlai.sitemapindex = True
        rlai.up = 'http://example.com/dataset1/capabilitylist.xml'
        rlai.add( Resource( uri='http://example.com/resourcelistarchive00001.xml' ))
        rlai.add( Resource( uri='http://example.com/resourcelistarchive00002.xml' ))
        ex_xml = self._open_ex('archives_ex_3_2').read()
        self._assert_xml_equal( rlai.as_xml(), ex_xml )

    def test_build_archives_ex_4_1(self):
        """Resource Dump Archive listing 2 Resource Dumps"""
        rda = ResourceDumpArchive()
        rda.up = 'http://example.com/dataset1/capabilitylist.xml'
        rda.add( Resource( uri='http://example.com/resourcedump1.xml',
                           lastmod='2012-11-03T09:05:42Z',
                           md_at="2012-11-03T09:00:00Z",
                           md_completed="2012-11-03T09:05:01Z" ) )

        rda.add( Resource( uri='http://example.com/resourcedump2.xml',
                           lastmod='2012-12-03T09:06:12Z',
                           md_at="2012-12-03T09:00:00Z",
                           md_completed="2012-12-03T09:05:17Z" ) )
        ex_xml = self._open_ex('archives_ex_4_1').read()
        self._assert_xml_equal( rda.as_xml(), ex_xml )

    def test_build_archives_ex_5_1(self):
        """Change List Archive listing 3 Change Lists"""
        cla = ChangeListArchive()
        cla.up = 'http://example.com/dataset1/capabilitylist.xml'
        cla.add( Resource( uri='http://example.com/changelist1.xml',
                           md_from='2013-01-01T09:00:00Z',
                           md_until='2013-01-02T09:00:00Z') )
        cla.add( Resource( uri='http://example.com/changelist2.xml',
                           md_from='2013-01-02T09:00:00Z',
                           md_until='2013-01-03T09:00:00Z') )
        cla.add( Resource( uri='http://example.com/changelist3.xml',
                           md_from='2013-01-03T09:00:00Z',
                           md_until='2013-01-04T09:00:00Z') )
        ex_xml = self._open_ex('archives_ex_5_1').read()
        self._assert_xml_equal( cla.as_xml(), ex_xml )

    def test_build_archives_ex_6_1(self):
        """Change Dump Archive listing 2 Change Dumps"""
        cda = ChangeDumpArchive()
        cda.up = 'http://example.com/dataset1/capabilitylist.xml'
        cda.add( Resource( uri='http://example.com/changedump-w1.xml',
                           lastmod='2012-12-20T09:02:43Z',
                           md_from="2012-01-13T09:00:00Z",
                           md_until="2013-01-20T09:00:00Z" ) )
        cda.add( Resource( uri='http://example.com/changedump-w2.xml',
                           lastmod='2012-12-27T09:01:57Z',
                           md_from="2012-01-20T09:00:00Z",
                           md_until="2013-01-27T09:00:00Z" ) )
        ex_xml = self._open_ex('archives_ex_6_1').read()
        self._assert_xml_equal( cda.as_xml(), ex_xml )

##### UTILITIES FOR (APPROX) COMPARISON OF XML IN EXAMPLES AND OUTPUT

    def _assert_xml_equal(self,a,b):
        context = "Element mismatch in\n%s\nvs\n%s\n" % (a,b);
        aa = self._xml_massage_split(a)
        bb = self._xml_massage_split(b)
        ia=iter(aa)
        ib=iter(bb)
        try:
            while (1):
                self._assert_xml_elements_equal( self._xml_reorder_attributes(ia.next()), 
                                                 self._xml_reorder_attributes(ib.next()), 
                                                 context )
        except StopIteration:
            # all is good provided there were the same number of elements
            pass
        self.assertEqual( len(aa), len(bb), "Same length check\n%s" % (context) )

    def _assert_xml_elements_equal(self,a,b,context):
        context = "Elements %s != %s\n%s" % (a,b,context)
        self.assertEqual( a, b, context )

    def _xml_reorder_attributes(self,xml):
        """Manipulate string for single element with atts in alpha order
        
        This is a bit of a fudge because of pattern matching. Should give
        correct match for all matches, but might give matches in rare cases 
        that should not.
        """
        return(' '.join( sorted( xml.split(' ') ) ) )

    def _xml_massage_split(self,xml):
        """Massage XML for comparison and split by elements (on >)"""
        xml = re.sub( r'\s+$', '', xml)
        xml = re.sub( r'^\s+', '', xml)
        xml = re.sub( r'\s+', ' ', xml)
        xml = re.sub( r'\s*/>', ' />', xml) #always one space before end of self-closing element
        xml = re.sub( r'>\s+<', '><', xml) #remove space between elements
        # FUDGES, need to check these are OK
        xml = re.sub( r"version='1.0'", 'version="1.0"', xml )
        xml = re.sub( r"encoding='UTF-8'", 'encoding="UTF-8"', xml )
        # return self.assertEqual( x, 'xx' )
        return( xml.split('>') )

    def _open_ex(self,ex):
        return open('resync/test/testdata/examples_from_spec/%s.xml'%(ex),'r')

if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExamplesFromSpec)
    unittest.TextTestRunner(verbosity=2).run(suite)
