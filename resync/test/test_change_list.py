import unittest
from resync.resource import Resource
from resync.change_list import ChangeList
from resync.resource_list import ResourceList

class TestChangeList(unittest.TestCase):

    def test1_set_with_repeats(self):
        src = ChangeList()
        src.add( Resource('a',timestamp=1) )
        src.add( Resource('b',timestamp=1) )
        src.add( Resource('c',timestamp=1) )
        src.add( Resource('a',timestamp=2) )
        src.add( Resource('b',timestamp=2) )
        self.assertEqual(len(src), 5, "5 changes in change_list")

    def test2_with_repeats_again(self):
        r1 = Resource(uri='a',size=1)
        r2 = Resource(uri='b',size=2)
        i = ChangeList()
        i.add(r1)
        i.add(r2)
        self.assertEqual( len(i), 2 )
        # Can add another Resource with same URI
        r1d = Resource(uri='a',size=10)
        i.add(r1d)
        self.assertEqual( len(i), 3 )

    def test3_change_list(self):
        src = ChangeList()
        src.add( Resource('a',timestamp=1) )
        src.add( Resource('b',timestamp=2) )
        src.add( Resource('c',timestamp=3) )
        src.add( Resource('d',timestamp=4)) 
        src.add( Resource('e',timestamp=5) )
        self.assertEqual(len(src), 5, "5 things in src")

    def test4_iter(self):
        i = ChangeList()
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

    def test5_add_changed_resources(self):
        added = ResourceList()
        added.add( Resource('a',timestamp=1) )
        added.add( Resource('d',timestamp=4))
        self.assertEqual(len(added), 2, "2 things in added resource_list")
        changes = ChangeList()
        changes.add_changed_resources( added, change='created' )
        self.assertEqual(len(changes), 2, "2 things added")
        i = iter(changes)
        first = i.next()
        self.assertEqual(first.uri, 'a', "changes[0].uri=a")
        self.assertEqual(first.timestamp, 1, "changes[0].timestamp=1")
        self.assertEqual(first.change, 'created') #, "changes[0].change=created")
        second = i.next()
        self.assertEqual(second.timestamp, 4, "changes[1].timestamp=4")
        self.assertEqual(second.change, 'created', "changes[1].change=created")
        # Now add some with updated (one same, one diff)
        updated = ResourceList()
        updated.add( Resource('a',timestamp=5) )
        updated.add( Resource('b',timestamp=6))
        self.assertEqual(len(updated), 2, "2 things in updated resource_list")
        changes.add_changed_resources( updated, change='updated' )
        self.assertEqual(len(changes), 4, "4 = 2 old + 2 things updated")
        # Make new resource_list from the changes which should not have dupes
        dst = ResourceList()
        dst.add( changes, replace=True )
        self.assertEqual(len(dst), 3, "3 unique resources")
        self.assertEqual(dst.resources['a'].timestamp, 5 ) # 5 was later in last the 1
        self.assertEqual(dst.resources['a'].change, 'updated')
        self.assertEqual(dst.resources['b'].timestamp, 6)
        self.assertEqual(dst.resources['b'].change, 'updated')
        self.assertEqual(dst.resources['d'].timestamp, 4)
        self.assertEqual(dst.resources['d'].change, 'created')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestChangeList)
    unittest.TextTestRunner().run(suite)
