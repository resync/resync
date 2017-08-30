import unittest
import re
from resync.resource import Resource
from resync.resource_set import ResourceSet, ResourceSetDupeError


class TestResourceSet(unittest.TestCase):

    def test01_add(self):
        rs = ResourceSet()
        self.assertEqual(len(rs), 0)
        rs.add(Resource('a'))
        self.assertEqual(len(rs), 1)
        rs.add(Resource('b'))
        self.assertEqual(len(rs), 2)
        rs.add(Resource('c'))
        self.assertEqual(len(rs), 3)

    def test02_order(self):
        rs = ResourceSet()
        rs.add(Resource('a2'))
        rs.add(Resource('a3'))
        rs.add(Resource('a1'))
        i = iter(rs)
        self.assertEqual(next(i).uri, 'a1')
        self.assertEqual(next(i).uri, 'a2')
        self.assertEqual(next(i).uri, 'a3')
        self.assertRaises(StopIteration, next, i)

    def test03_dupe(self):
        rs = ResourceSet()
        self.assertEqual(len(rs), 0)
        rs.add(Resource('a'))
        self.assertEqual(len(rs), 1)
        self.assertRaises(ResourceSetDupeError, rs.add, Resource('a'))
