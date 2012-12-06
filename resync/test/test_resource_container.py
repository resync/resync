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

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestResourceContainer)
    unittest.TextTestRunner().run(suite)
