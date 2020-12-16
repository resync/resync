# resync

[![Build Status](https://travis-ci.org/resync/resync.svg?branch=master)](https://travis-ci.org/resync/resync)
[![Test Coverage](https://coveralls.io/repos/github/resync/resync/badge.svg?branch=master)](https://coveralls.io/github/resync/resync)

**resync** is a ResourceSync library with supporting client scipts,
written in python.
[ResourceSync](http://www.openarchives.org/rs/) is a synchronization
framework for the web consisting of various capabilities that allow
third party systems to remain synchronized with a server's evolving
resources. The capabilities can be combined in a modular manner to
meet local or community requirements.

## Client usage

Typical client usage to synchronize from a source at
`http://source.example.com/` to a set of local files would be

```
resync-sync http://source.example.com/
```

which will create or update a local directory `./source.example.com`.
Alternatively, the destination directory may be specified explicitly::

```
resync-sync http://source.example.com/ /tmp/my_copy
```

Option details and a number of different modes are described with::

```
resync-sync -h
```

## Python library usage

Typical library use in a source (create and output a Resource List)::

```
from resync import Resource, ResourceList

rl = ResourceList()
rl.add( Resource('http://example.com/res1', lastmod='2013-01-01') )
rl.add( Resource('http://example.com/res2', lastmod='2013-01-02') )
print rl.as_xml()
```

Typical library use in a destination (get and examine a Capability List)::

```
from resync import CapabilityList

# Read Capability List and show supported capabilities
cl = CapabilityList()
cl.read("https://raw.github.com/resync/resync/1.0/resync/test/testdata/examples_from_spec/resourcesync_ex_2_6.xml")
for resource in cl:
    print "supports %s (at %s)" % (resource.capability,resource.uri)
```

## Installation

The client and library are designed to work with Python 3.5 and up. (The
last version supporting Python 2.7 was
[1.0.9, also on PyPI](https://pypi.org/project/resync/1.0.9/))

### Automatic installation

```
pip install resync
```

rsync is listed in [PyPI](http://pypi.python.org/pypi/resync) and can be
installed with `pip` or `easy_install`.

### Manual installation from github

```
cd /tmp
git clone git://github.com/resync/resync.git
cd resync/
python setup.py build
python setup.py install
```

This will install the library code in the appropriate place within
a user-space python setup, including the clients `resync-sync`,
`resync-build` and `resync-explorer`. Use of `sudo` to install in
system spaces is generally discouraged.

The source code is maintained on [Github](https://github.com/resync/resync)
and there may be branches/versions available there that are not
yet packaged for PyPI.

## See also

  * [ResourceSync simulator](http://github.com/resync/simulator)

## Contributors

Thanks to: [Bernhard Haslhofer](https://github.com/behas),
[Robert Sanderson](<https://github.com/azaroth42)
and [other contributors](https://github.com/resync/resync/graphs/contributors).

See [CONTRIBUTING.md](https://github.com/resync/resync/blob/master/CONTRIBUTING.md)
for guidelines for contributing.

## Copyright and License

Copyright 2012--2020 Simeon Warner and contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

See `LICENSE.txt`
