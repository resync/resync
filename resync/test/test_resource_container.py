import unittest
from resync.resource import Resource
from resync.resource_container import ResourceContainer

class TestResourceContainer(unittest.TestCase):

    def test1_create_and_add(self):
        rc = ResourceContainer( resources=[] )
        self.assertEqual( len(rc.resources), 0, "empty" )
        rc.resources.append( Resource('a',timestamp=1) )
        rc.resources.append( Resource('b',timestamp=2) )
        self.assertEqual( len(rc.resources), 2, "two resources" )

    def test2_iter(self):
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

    def test3_prune_before(self):
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

    def test4_prune_dupes(self):
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

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceContainer)
    unittest.TextTestRunner().run(suite)
