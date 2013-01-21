import unittest
from resync.resource import Resource
from resync.resource_list import ResourceList, ResourceListDupeError

class TestResourceList(unittest.TestCase):

    def test1_same(self):
        src = ResourceList()
        src.add( Resource('a',timestamp=1) )
        src.add( Resource('b',timestamp=2) )
        dst = ResourceList()
        dst.add( Resource('a',timestamp=1) )
        dst.add( Resource('b',timestamp=2) )
        ( same, changed, deleted, added ) = dst.compare(src)
        self.assertEqual( len(same), 2, "2 things unchanged" )
        i = iter(same)
        self.assertEqual( i.next().uri, 'a', "first was a" )
        self.assertEqual( i.next().uri, 'b', "second was b" )
        self.assertEqual( len(changed), 0, "nothing changed" )
        self.assertEqual( len(deleted), 0, "nothing deleted" )
        self.assertEqual( len(added), 0, "nothing added" )

    def test2_changed(self):
        src = ResourceList()
        src.add( Resource('a',timestamp=1) )
        src.add( Resource('b',timestamp=2) )
        dst = ResourceList()
        dst.add( Resource('a',timestamp=3) )
        dst.add( Resource('b',timestamp=4) )
        ( same, changed, deleted, added ) = dst.compare(src)
        self.assertEqual( len(same), 0, "0 things unchanged" )
        self.assertEqual( len(changed), 2, "2 things changed" )
        i = iter(changed)
        self.assertEqual( i.next().uri, 'a', "first was a" )
        self.assertEqual( i.next().uri, 'b', "second was b" )
        self.assertEqual( len(deleted), 0, "nothing deleted" )
        self.assertEqual( len(added), 0, "nothing added" )

    def test3_deleted(self):
        src = ResourceList()
        src.add( Resource('a',timestamp=1) )
        src.add( Resource('b',timestamp=2) )
        dst = ResourceList()
        dst.add( Resource('a',timestamp=1) )
        dst.add( Resource('b',timestamp=2) )
        dst.add( Resource('c',timestamp=3) )
        dst.add( Resource('d',timestamp=4) )
        ( same, changed, deleted, added ) = dst.compare(src)
        self.assertEqual( len(same), 2, "2 things unchanged" )
        self.assertEqual( len(changed), 0, "nothing changed" )
        self.assertEqual( len(deleted), 2, "c and d deleted" )
        i = iter(deleted)
        self.assertEqual( i.next().uri, 'c', "first was c" )
        self.assertEqual( i.next().uri, 'd', "second was d" )
        self.assertEqual( len(added), 0, "nothing added" )

    def test4_added(self):
        src = ResourceList()
        src.add( Resource('a',timestamp=1) )
        src.add( Resource('b',timestamp=2) )
        src.add( Resource('c',timestamp=3) )
        src.add( Resource('d',timestamp=4) )
        dst = ResourceList()
        dst.add( Resource('a',timestamp=1) )
        dst.add( Resource('c',timestamp=3) )
        ( same, changed, deleted, added ) = dst.compare(src)
        self.assertEqual( len(same), 2, "2 things unchanged" )
        self.assertEqual( len(changed), 0, "nothing changed" )
        self.assertEqual( len(deleted), 0, "nothing deleted" )
        self.assertEqual( len(added), 2, "b and d added" )
        i = iter(added)
        self.assertEqual( i.next().uri, 'b', "first was b" )
        self.assertEqual( i.next().uri, 'd', "second was d" )

    def test5_add(self):
        r1 = Resource(uri='a',size=1)
        r2 = Resource(uri='b',size=2)
        i = ResourceList()
        i.add(r1)
        self.assertRaises( ResourceListDupeError, i.add, r1)
        i.add(r2)
        self.assertRaises( ResourceListDupeError, i.add, r2)
        # allow dupes
        r1d = Resource(uri='a',size=10)
        i.add(r1d,replace=True)
        self.assertEqual( len(i), 2 )
        self.assertEqual( i.resources['a'].size, 10 ) 

    def test5_add_iterable(self):
        r1 = Resource(uri='a',size=1)
        r2 = Resource(uri='b',size=2)
        i = ResourceList()
        i.add( [r1,r2] )
        self.assertRaises( ResourceListDupeError, i.add, r1)
        self.assertRaises( ResourceListDupeError, i.add, r2)
        # allow dupes
        r1d = Resource(uri='a',size=10)
        i.add( [r1d] ,replace=True)
        self.assertEqual( len(i), 2 )
        self.assertEqual( i.resources['a'].size, 10 ) 

    def test6_has_md5(self):
        r1 = Resource(uri='a')
        r2 = Resource(uri='b')
        i = ResourceList()
        self.assertFalse( i.has_md5() )
        i.add(r1)
        i.add(r2)
        self.assertFalse( i.has_md5() )
        r1.md5="aabbcc"
        self.assertTrue( i.has_md5() )

    def test7_iter(self):
        i = ResourceList()
        i.add( Resource('a',timestamp=1) )
        i.add( Resource('b',timestamp=2) )
        i.add( Resource('c',timestamp=3) )
        i.add( Resource('d',timestamp=4) )
        resources=[]
        for r in i:
            resources.append(r)
        self.assertEqual(len(resources), 4)
        self.assertEqual( resources[0].uri, 'a')
        self.assertEqual( resources[3].uri, 'd')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceList)
#    unittest.TextTestRunner(verbosity=1).run(suite)
    unittest.TextTestRunner().run(suite)
