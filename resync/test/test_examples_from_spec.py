import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.capability_list import CapabilityList
from resync.sitemap import Sitemap

class TestSitemap(unittest.TestCase):

    def test_all_simple(self):
        """Just try to read each one"""
        for ex in ("archives_ex_2_1.xml",
                   "archives_ex_3_1.xml",
                   "archives_ex_4_1.xml",
                   "archives_ex_5_1.xml",
                   "archives_ex_6_1.xml",
                   "resourcesync_ex_2_1.xml", "resourcesync_ex_2_2.xml",
                   "resourcesync_ex_2_3.xml", "resourcesync_ex_2_4.xml",
                   "resourcesync_ex_2_5.xml", "resourcesync_ex_2_6.xml",
                   "resourcesync_ex_2_7.xml",
                   "resourcesync_ex_4_1.xml", "resourcesync_ex_4_2.xml",
                   "resourcesync_ex_4_3.xml",
                   "resourcesync_ex_5_1.xml", "resourcesync_ex_5_2.xml",
                   "resourcesync_ex_6_1.xml",
                   "resourcesync_ex_7_1.xml", "resourcesync_ex_7_2.xml",
                   "resourcesync_ex_8_1.xml", "resourcesync_ex_8_2.xml",
                   "resourcesync_ex_8_3.xml", "resourcesync_ex_8_4.xml",
                   "resourcesync_ex_8_5.xml", "resourcesync_ex_8_6.xml",
                   "resourcesync_ex_8_7.xml", "resourcesync_ex_8_8.xml",
                   "resourcesync_ex_8_9.xml", "resourcesync_ex_8_10.xml",
                   "resourcesync_ex_9_1.xml" ):
            s=Sitemap()
            fh = open( 'resync/test/testdata/examples_from_spec/%s' % (ex), 'r')
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
        """resourcesync_ex_2_6 is a simple capability list with capabilities"""
        capl=CapabilityList()
        capl.parse('resync/test/testdata/examples_from_spec/resourcesync_ex_2_6.xml')
        self.assertEqual( len(capl.resources), 3, '3 capabilities')
        # What capabilities are present?
        self.assertTrue( capl.has_capability('resourcelist') )
        self.assertEqual( capl.capability('resourcelist').uri, 'http://example.com/dataset1/resourcelist.xml')
        self.assertTrue( capl.has_capability('resourcedump') )
        self.assertEqual( capl.capability('resourcedump').uri, 'http://example.com/dataset1/resourcedump.xml')
        self.assertTrue( capl.has_capability('changelist') )
        self.assertEqual( capl.capability('changelist').uri, 'http://example.com/dataset1/changelist.xml')
        # Check some that aren't
        self.assertFalse( capl.has_capability() )
        self.assertFalse( capl.has_capability('bogus') )
        self.assertFalse( capl.has_capability('capabilitylist') )

    def test_ex_2_7(self):
        """resourcesync_ex2_7 is a simple Resource List Index with 2 Resource Lists"""
        rl=ResourceList()
        rl.read(uri='resync/test/testdata/examples_from_spec/resourcesync_ex_2_7.xml',index_only=True)
        self.assertEqual( rl.capability, 'resourcelist' )
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/resourcelist-part1.xml',
                                'http://example.com/resourcelist-part2.xml'] )
        self.assertEqual( rl.resources['http://example.com/resourcelist-part1.xml'].lastmod,
                          '2013-01-03T09:00:00Z' )
        self.assertEqual( rl.resources['http://example.com/resourcelist-part2.xml'].lastmod,
                          '2013-01-03T09:00:00Z' )


if  __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSitemap)
    unittest.TextTestRunner(verbosity=2).run(suite)
