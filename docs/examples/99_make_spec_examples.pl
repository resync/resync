from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.capability_list import CapabilityList
from resync.resource import Resource
from resync.sitemap import Sitemap

def head(txt):
    print "\n=== "+txt+" ===\n"

print "\nExample script to build objects to write the examples in the spec\n"

head("Example 2.1: A Resource List")
rl = ResourceList()
rl.modified='2013-01-03T09:00:00Z'
rl.add( Resource('http://example.com/res1') )
rl.add( Resource('http://example.com/res2') )
print rl.as_xml(pretty_xml=True)

head("Example 2.2: A Resource List with additional information")
rl = ResourceList()
rl.modified='2013-01-03T09:00:00Z'
rl.add( Resource('http://example.com/res1',
	         lastmod='2013-01-02T13:00:00Z', 
		 md5='1584abdf8ebdc9802ac0c6a7402c03b') )
rl.add( Resource('http://example.com/res2',
                 lastmod='2013-01-02T14:00:00Z',
		 md5='1e0d5cb8ef6ba40c99b14c0237be735e') )
print rl.as_xml(pretty_xml=True)

head("Example 2.3: A Change List")
cl = ChangeList()
cl.modified="2013-01-03T11:00:00Z"
cl.add( Resource('http://example.com/res2.pdf',
		 lastmod='2013-01-02T13:00:00Z',
		 change='updated') )
cl.add( Resource('http://example.com/res3.tiff',
	 	 lastmod='2013-01-02T18:00:00Z',
		 change='deleted') )
print cl.as_xml(pretty_xml=True)

head("Example 2.4: A Resource Dump")
rd = ResourceDump()
rd.modified="2013-01-03T09:00:00Z"
rd.add( Resource('http://example.com/resourcedump.zip',
		 lastmod='2013-01-03T09:00:00Z') )
print rd.as_xml(pretty_xml=True)

head("Example 2.5: A Resource Dump Manifest detailing the content of a ZIP file")
rdm = ResourceDumpManifest()
rdm.modified="2013-01-03T09:00:00Z"
rdm.add( Resource('http://example.com/res1',
	          lastmod='2013-01-02T13:00:00Z', 
		  md5='1584abdf8ebdc9802ac0c6a7402c03b6',
	          path='/resources/res1') )
rdm.add( Resource('http://example.com/res2',
                  lastmod='2013-01-02T14:00:00Z',
	   	  md5='1e0d5cb8ef6ba40c99b14c0237be735e',
	          path='/resources/res2') )
print rdm.as_xml(pretty_xml=True)

head("Example 2.6: A Capability List with the description of the ResourceSync capabilities of a Source")
caplist=CapabilityList()
caplist.modified="2013-01-02T14:00:00Z"
caplist.ln.append({'href':"http://example.com/info-about-source.xml",
                   'rel':"describedby",
		   'type':"application/xml"})
caplist.add( Resource('http://example.com/dataset1/resourcelist.xml',
                      capability="resourcelist") )
caplist.add( Resource('http://example.com/dataset1/resourcedump.xml',
                      capability="resourcedump") )
caplist.add( Resource('http://example.com/dataset1/changelist.xml',
                      capability="changelist") )
print caplist.as_xml(pretty_xml=True)

head("Example 2.7: A Resource List Index expressed using the <sitemapindex> document format")
rl = ResourceList()
rl.modified="2013-01-03T09:00:00Z"
rl.add( Resource("http://example.com/resourcelist-part2.xml",
		 lastmod="2013-01-03T09:00:00Z") )
rl.add( Resource("http://example.com/resourcelist-part1.xml",
                 lastmod="2013-01-03T09:00:00Z") )
print rl.index_as_xml(pretty_xml=True)

head("Example 4.1: A Resource List")
rl = ResourceList()
rl.modified="2013-01-03T09:00:00Z"
rl.ln.append({"rel":"resourcesync",
              "href":"http://example.com/dataset1/capabilitylist.xml"})
rl.add( Resource("http://example.com/res1",
                 lastmod="2013-01-02T13:00:00Z",
                 md5="1584abdf8ebdc9802ac0c6a7402c03b6",
                 length="8876",
                 type="text/html") )
rl.add( Resource("http://example.com/res2",
                 lastmod="2013-01-02T14:00:00Z",
                 md5="1e0d5cb8ef6ba40c99b14c0237be735e",
		 sha256="854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784",
                 length="14599",
                 type="application/pdf") )
print rl.as_xml(pretty_xml=True)

head("Example 4.2: A Resource List Index")
rl = ResourceList()
rl.modified="2013-01-03T09:00:00Z"
rl.ln.append({"rel":"resourcesync",
              "href":"http://example.com/dataset1/capabilitylist.xml"})
rl.add( Resource("http://example.com/resourcelist3.xml",
                 lastmod="2013-01-03T09:00:00Z") )
rl.add( Resource("http://example.com/resourcelist2.xml",
                 lastmod="2013-01-03T09:00:00Z") )
rl.add( Resource("http://example.com/resourcelist1.xml",
                 lastmod="2013-01-03T09:00:00Z") )
print rl.index_as_xml(pretty_xml=True)

head("Example 4.3: A Resource List with a navigational link to its parent Resource List Index")
rl = ResourceList()
rl.modified="2013-01-03T09:00:00Z"
rl.ln.append({"rel":"resourcesync",
              "href":"http://example.com/dataset1/capabilitylist.xml"})
rl.ln.append({"rel":"up",
              "href":"http://example.com/dataset1/resourcelist-index.xml"})
rl.add( Resource("http://example.com/res3",
                 lastmod="2013-01-03T09:00:00Z",
                 md5="1584abdf8ebdc9802ac0c6a7402c8753",
                 length="4385",
                 type="application/pdf") )
rl.add( Resource("http://example.com/res2",
                 lastmod="2013-01-03T09:00:00Z",
                 md5="4556abdf8ebdc9802ac0c6a7402c9881",
                 length="883",
                 type="image/png") )
print rl.as_xml(pretty_xml=True)

head("Example 5.1: A Resource Dump document")
rd = ResourceDump()
rd.modified = "2013-01-03T09:00:00Z"
rd.ln.append({"rel":"resourcesync",
              "href":"http://example.com/dataset1/capabilitylist.xml"})
rd.add( Resource("http://example.com/resourcedump-part3.zip",
		 lastmod="2013-01-03T09:00:00Z",
		 type="application/zip",
		 length="4765") )
rd.add( Resource("http://example.com/resourcedump-part2.zip",
		 lastmod="2013-01-03T09:00:00Z",
                 type="application/zip",
		 length="9875") )
rd.add( Resource("http://example.com/resourcedump-part1.zip",
                 lastmod="2013-01-03T09:00:00Z",
                 type="application/zip",
                 length="2298") )
print rd.as_xml(pretty_xml=True)

head("Example 5.2: A Resource Dump Manifest")
rdm = ResourceDumpManifest()
rdm.modified="2013-01-03T09:00:00Z"
rdm.ln.append({"rel":"resourcesync",
               "href":"http://example.com/dataset1/capabilitylist.xml"})
rdm.add( Resource("http://example.com/res1",
		  lastmod="2013-01-02T13:00:00Z",
		  md5="1584abdf8ebdc9802ac0c6a7402c03b6",
		  length="8876",
		  type="text/html",
		  path="/resources/res1") )
rdm.add( Resource("http://example.com/res2",
		  lastmod="2013-01-02T14:00:00Z",
                  md5="1e0d5cb8ef6ba40c99b14c0237be735e",
                  sha256="854f61290e2e197a11bc91063afce22e43f8ccc655237050ace766adc68dc784",
		  length="14599",
		  type="application/pdf",
		  path="/resources/res2") )
print rdm.as_xml(pretty_xml=True)

head("Example 5.3: A Resource Dump Manifest Index")
rdm = ResourceDumpManifest()
rdm.modified="2013-01-03T09:00:00Z"
rdm.ln.append({"rel":"resourcesync",
               "href":"http://example.com/dataset1/capabilitylist.xml"})
rdm.add( Resource("/manifests/part3.xml",
		  lastmod="2013-01-03T09:00:00Z",
                  path="/manifests/part3.xml") )
rdm.add( Resource("/manifests/part2.xml",
		  lastmod="2013-01-03T09:00:00Z",
		  path="/manifests/part2.xml") )
rdm.add( Resource("/manifests/part1.xml",
		  lastmod="2013-01-03T09:00:00Z",
		  path="/manifests/part1.xml") )
print rdm.index_as_xml(pretty_xml=True)

