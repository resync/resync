import unittest
from resync.mapper import Mapper, MapperError

class TestMapper(unittest.TestCase):

    def test00_mapper_creation(self):
        m1=Mapper( ['http://e.org/p/','/tmp/q/'] )
        self.assertEqual( len(m1), 1 )
        m2=Mapper( mappings=['http://e.org/p','/tmp/q'] )
        self.assertEqual( len(m2), 1 )
        self.assertEqual( str(m1), str(m2) )
        m3=Mapper( ['http://e.org/p/=/tmp/q/'] )
        self.assertEqual( len(m3), 1 )
        self.assertEqual( str(m1), str(m3) )
        m4=Mapper( ['http://e.org/p/=/tmp/q/','http://e.org/r/=/tmp/s/'] )
        m5=Mapper( ['http://e.org/r/=/tmp/s/','http://e.org/p/=/tmp/q/'] )
        self.assertEqual( len(m4), 2 )
        self.assertEqual( len(m5), 2 )
        self.assertNotEqual( str(m4), str(m5) )
        

    def test01_mapper_src_to_dst(self):
        m=Mapper( ['http://e.org/p/','/tmp/q/'] )
        self.assertEqual( m.src_to_dst('http://e.org/p/'), '/tmp/q/')
        self.assertEqual( m.src_to_dst('http://e.org/p/aa'), '/tmp/q/aa')
        self.assertEqual( m.src_to_dst('http://e.org/p/aa/bb'), '/tmp/q/aa/bb')
        self.assertEqual( m.src_to_dst('http://e.org/p/aa/bb/'), '/tmp/q/aa/bb/')
        self.assertRaises( MapperError, m.src_to_dst, 'http://e.org/p' )
        self.assertRaises( MapperError, m.src_to_dst, 'http://e.org/pa' )
        self.assertRaises( MapperError, m.src_to_dst, 'nomatch' )

    def test02_mapper_dst_to_src(self):
        m=Mapper( ['http://e.org/p/','/tmp/q/'] )
        self.assertEqual( m.dst_to_src('/tmp/q/'), 'http://e.org/p/')
        self.assertEqual( m.dst_to_src('/tmp/q/bb'), 'http://e.org/p/bb')
        self.assertEqual( m.dst_to_src('/tmp/q/bb/cc'), 'http://e.org/p/bb/cc')
        self.assertRaises( MapperError, m.dst_to_src, '/tmp/q' )
        self.assertRaises( MapperError, m.dst_to_src, '/tmp/qa')
        self.assertRaises( MapperError, m.dst_to_src, 'nomatch' )

    def test03_mapper2_src_to_dst(self):
        m=Mapper( ['http://e.org/p=/tmp/q','http://e.org/r=/tmp/s'] )
        self.assertEqual( m.src_to_dst('http://e.org/p/'), '/tmp/q/')
        self.assertEqual( m.src_to_dst('http://e.org/p/aa'), '/tmp/q/aa')
        self.assertEqual( m.src_to_dst('http://e.org/r/'), '/tmp/s/')
        self.assertEqual( m.src_to_dst('http://e.org/r/aa'), '/tmp/s/aa')

    def test04_mapper2_dst_to_src(self):
        m=Mapper( ['http://e.org/p=/tmp/q','http://e.org/r=/tmp/s'] )
        self.assertEqual( m.dst_to_src('/tmp/q/'), 'http://e.org/p/')
        self.assertEqual( m.dst_to_src('/tmp/q/bb'), 'http://e.org/p/bb')
        self.assertEqual( m.dst_to_src('/tmp/s/'), 'http://e.org/r/')
        self.assertEqual( m.dst_to_src('/tmp/s/bb'), 'http://e.org/r/bb')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMapper)
    unittest.TextTestRunner(verbosity=2).run(suite)
