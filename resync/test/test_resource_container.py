import unittest
from resync.resource import Resource
from resync.resource_container import ResourceContainer

class TestResourceContainer(unittest.TestCase):

    def test01_create_and_add(self):
        rc = ResourceContainer( resources=[] )
        self.assertEqual( len(rc.resources), 0, "empty" )
        rc.resources.append( Resource('a',timestamp=1) )
        rc.resources.append( Resource('b',timestamp=2) )
        self.assertEqual( len(rc.resources), 2, "two resources" )

    def test02_iter(self):
        rc = ResourceContainer( resources=[] )
        rc.resources.append( Resource('a',timestamp=1) )
        rc.resources.append( Resource('b',timestamp=2) )
        rc.resources.append( Resource('c',timestamp=3) )
        rc.resources.append( Resource('d',timestamp=4) )
        resources=[]
        for r in rc:
            resources.append(r)
        self.assertEqual(len(resources), 4)
        self.assertEqual( resources[0].uri, 'a')
        self.assertEqual( resources[3].uri, 'd')

    def test03_prune_before(self):
        rc = ResourceContainer()
        rc.resources.append( Resource('a',timestamp=1) )
        rc.resources.append( Resource('b',timestamp=2) )
        rc.resources.append( Resource('c',timestamp=3) )
        rc.resources.append( Resource('d',timestamp=4) )
        rc.prune_before(3)
        self.assertEqual( len(rc.resources), 2 )
        i = iter(rc)
        self.assertEqual( i.next().uri, 'c' )
        self.assertEqual( i.next().uri, 'd' )
        # put some more back out of order
        rc.resources.append( Resource('a',timestamp=1) )
        rc.resources.append( Resource('b',timestamp=2) )
        rc.resources.append( Resource('e',timestamp=1000) )
        rc.prune_before(3.5)
        self.assertEqual( len(rc.resources), 2 )
        i = iter(rc)
        self.assertEqual( i.next().uri, 'd' )
        self.assertEqual( i.next().uri, 'e' )

    def test04_prune_dupes(self):
        rc = ResourceContainer()
        rc.resources.append( Resource('a',timestamp=1, change='created') )
        rc.resources.append( Resource('b',timestamp=2, change='created') )
        rc.resources.append( Resource('c',timestamp=3, change='updated') )
        rc.resources.append( Resource('d',timestamp=4, change='deleted') )
        rc.resources.append( Resource('a',timestamp=4, change='updated') )
        rc.resources.append( Resource('b',timestamp=4, change='deleted') )
        rc.resources.append( Resource('b',timestamp=5, change='created') )
        rc.resources.append( Resource('b',timestamp=6, change='deleted') )
        rc.resources.append( Resource('c',timestamp=7, change='deleted') )
        rc.resources.append( Resource('d',timestamp=8, change='created') )
        rc.prune_dupes()
        self.assertEqual( len(rc.resources), 3 )
        i = iter(rc)
        i1 = i.next()
        self.assertEqual( i1.uri, 'a' )
        self.assertEqual( i1.change, 'updated' )
        i2 = i.next()
        self.assertEqual( i2.uri, 'c' )
        self.assertEqual( i2.change, 'deleted' )
        i3 = i.next()
        self.assertEqual( i3.uri, 'd' )
        self.assertEqual( i3.change, 'created' )

    def test05_from_until(self):
        rc = ResourceContainer()
        # via convenience methods
        self.assertEqual( rc.md_from, None )
        self.assertEqual( rc.md_until, None )
        rc.md_from = "ftime"
        rc.md_until = "utime"
        self.assertEqual( rc.md_from, "ftime" )
        self.assertEqual( rc.md_until, "utime" )
        # via underlying dict
        rc.md['from'] = "ftime2"
        rc.md['until'] = "utime2too"
        self.assertEqual( rc.md_from, "ftime2" )
        self.assertEqual( rc.md_until, "utime2too" )

    def test06_source_description(self):
        # up links used to point to the source description
        rc = ResourceContainer()
        # via convenience methods                                  
        self.assertEqual( rc.up, None )
        rc.up = "well-known"
        self.assertEqual( rc.up, "well-known" )
        rc.up = "well-known2"
        self.assertEqual( rc.up, "well-known2" )
        # via link
        link = rc.link("up")
        self.assertEqual( link['href'], "well-known2" )
        link['href'] = "wk3"
        self.assertEqual( rc.up, "wk3" )

    def test07_describedby(self):
        rc = ResourceContainer()
        # via convenience methods                                  
        self.assertEqual( rc.describedby, None )
        rc.describedby = "db_uri"
        self.assertEqual( rc.describedby, "db_uri" )

    def test08_up(self):
        rc = ResourceContainer()
        # via convenience methods                                  
        self.assertEqual( rc.up, None )
        rc.up = "up_uri"
        self.assertEqual( rc.up, "up_uri" )

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceContainer)
    unittest.TextTestRunner().run(suite)
