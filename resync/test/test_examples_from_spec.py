"""Tests on the examples in the specification documents
"""
import re
import sys
import unittest
import StringIO
from resync.resource import Resource
from resync.resource_list import ResourceList,ResourceListOrdered
from resync.change_list import ChangeList
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.capability_list import CapabilityList
from resync.sitemap import Sitemap

class TestExamplesFromSpec(unittest.TestCase):

    def test_all_simple_read(self):
        """Just try to read each one"""
        for ex in ("archives_ex_2_1",
                   "archives_ex_3_1",
                   "archives_ex_4_1",
                   "archives_ex_5_1",
                   "archives_ex_6_1",
                   "resourcesync_ex_2_1", "resourcesync_ex_2_2",
                   "resourcesync_ex_2_3", "resourcesync_ex_2_4",
                   "resourcesync_ex_2_5", "resourcesync_ex_2_6",
                   "resourcesync_ex_2_7",
                   "resourcesync_ex_4_1", "resourcesync_ex_4_2",
                   "resourcesync_ex_4_3",
                   "resourcesync_ex_5_1", "resourcesync_ex_5_2",
                   "resourcesync_ex_6_1",
                   "resourcesync_ex_7_1", "resourcesync_ex_7_2",
                   "resourcesync_ex_8_1", "resourcesync_ex_8_2",
                   "resourcesync_ex_8_3", "resourcesync_ex_8_4",
                   "resourcesync_ex_8_5", "resourcesync_ex_8_6",
                   "resourcesync_ex_8_7", "resourcesync_ex_8_8",
                   "resourcesync_ex_8_9", "resourcesync_ex_8_10",
                   "resourcesync_ex_9_1" ):
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

    def test_ex_2_8(self):
        """resourcesync_ex2_8 is a simple Resource List Index with 2 Resource Lists"""
        rl=ResourceList()
        rl.read(uri='resync/test/testdata/examples_from_spec/resourcesync_ex_2_8.xml',index_only=True)
        self.assertEqual( rl.capability, 'resourcelist' )
        self.assertEqual( len(rl.resources), 2, '2 resources')
        sms = sorted(rl.uris())
        self.assertEqual( sms, ['http://example.com/resourcelist-part1.xml',
                                'http://example.com/resourcelist-part2.xml'] )
        self.assertEqual( rl.resources['http://example.com/resourcelist-part1.xml'].lastmod,
                          '2013-01-03T09:00:00Z' )
        self.assertEqual( rl.resources['http://example.com/resourcelist-part2.xml'].lastmod,
                          '2013-01-03T09:00:00Z' )

##### BUILD EXAMPLES #####

    def test_build_ex_4_1(self):
        rl = ResourceList()
        rl.ln.append({'rel':'resourcesync','href':'http://example.com/dataset1/capabilitylist.xml'})
        rl.md_from="2013-01-03T09:00:00Z"
        rl.add( Resource( uri='http://example.com/res1',
                             lastmod='2013-01-02T13:00:00Z',
                             md5='1584abdf8ebdc9802ac0c6a7402c03b6',
                             length=8876,
                             type="text/html" ))
        rl.add( Resource( uri='http://example.com/res2',
                             lastmod='2013-01-02T14:00:00Z',
                             md5='1e0d5cb8ef6ba40c99b14c0237be735e',
                             sha256='854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784',
                             length=14599,
                             type="application/pdf" ))
        ex_xml = self._open_ex('resourcesync_ex_4_1').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_4_2(self):
        rl = ResourceList(resources_class=ResourceListOrdered) #order in example is non-canonical
        rl.sitemapindex=True
        rl.ln.append({'rel':'resourcesync','href':'http://example.com/dataset1/capabilitylist.xml'})
        rl.md_from="2013-01-03T09:00:00Z"
        rl.add( Resource( uri='http://example.com/resourcelist3.xml',
                          lastmod='2013-01-03T09:00:00Z' ))
        rl.add( Resource( uri='http://example.com/resourcelist2.xml',
                          lastmod='2013-01-03T09:00:00Z' ))
        rl.add( Resource( uri='http://example.com/resourcelist1.xml',
                          lastmod='2013-01-03T09:00:00Z' ))
        ex_xml = self._open_ex('resourcesync_ex_4_2').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

    def test_build_ex_4_3(self):
        rl = ResourceList()
        rl.ln.append({'rel':'resourcesync','href':'http://example.com/dataset1/capabilitylist.xml'})
        rl.ln.append({'rel':'up','href':'http://example.com/dataset1/resourcelist-index.xml'})
        rl.md_from="2013-01-03T09:00:00Z"
        rl.add( Resource( uri='http://example.com/res3',
                             lastmod='2013-01-03T09:00:00Z',
                             md5='1584abdf8ebdc9802ac0c6a7402c8753',
                             length=4385,
                             type="application/pdf" ))
        rl.add( Resource( uri='http://example.com/res4',
                             lastmod='2013-01-03T09:00:00Z',
                             md5='4556abdf8ebdc9802ac0c6a7402c9881',
                             length=883,
                             type="image/png" ))
        ex_xml = self._open_ex('resourcesync_ex_4_3').read()
        self._assert_xml_equal( rl.as_xml(), ex_xml )

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
