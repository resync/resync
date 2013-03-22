======
resync
======

resync is ResourceSync client and library in python.

Typical client usage:

> resync http://source.example.com/ /tmp/my_source_example_com

Typical library usage in a source:

```python
from resync.resource_list import ResourceList
from resync.resource import Resource

rl = ResourceList()
rl.add( Resource('http://example.com/res1', lastmod='2013-01-01') )
rl.add( Resource('http://example.com/res2', lastmod='2013-01-02') )
print rl.as_xml(rl)
```

See also
--------

http://github.com/resync/simulator



