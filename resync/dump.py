"""Dump handler for ResourceSync"""

import os.path
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from sitemap import Sitemap

class DumpError(Exception):
    pass

class Dump(object):
    """Dump of resource content associated with an resourcelist or change set

    The resourcelist must be comprised of Resource objects
    which have the path attributes set to indicate the local
    location of the copies of the resources.
    """

    def __init__(self, format=None, compress=True):
        self.format = ('zip' if (format is None) else format)
        self.compress = compress
        self.max_size = 100*1024*1024 #100MB
        self.max_files = 50000
        
    def write(self, resourcelist=None, dumpfile=None):
        """Write a dump file"""
        self.check_files(resourcelist)
        if (self.format == 'zip'):
            self.write_zip(resourcelist,dumpfile)
        elif (self.format == 'warc'):
            self.write_warc(resourcelist,dumpfile)
        else:
            raise DumpError("Unknown dump format '%s'" % (self.format))

    def write_zip(self, resourcelist=None, dumpfile=None):
        """Write a ZIP dump file"""
        compression = ( ZIP_DEFLATED if self.compress else ZIP_STORED )
        zf = ZipFile(dumpfile, mode="w", compression=compression, allowZip64=True)
        # Write resourcelist first
        s = Sitemap(pretty_xml=True, allow_multifile=False)
        zf.writestr('manifest.xml',s.resources_as_xml(resourcelist))
        # Add all files in the resourcelist
        for resource in resourcelist:
            zf.write(resource.uri)
        zf.close()
        zipsize = os.path.getsize(dumpfile)
        print "Wrote ZIP file dump %s with size %d bytes" % (dumpfile,zipsize)
        
    def write_warc(self, resourcelist=None, dumpfile=None):
        """Write a WARC dump file"""
        # Load library late as we want to be able to run rest of code 
        # without this installed
        try:
            from warc import WARCFile,WARCHeader,WARCRecord
        except:
            raise DumpError("Failed to load WARC library")
        wf = WARCFile(dumpfile, mode="w", compress=self.compress)
        # Add all files in the resourcelist
        for resource in resourcelist:
            wh = WARCHeader({})
            wh.url = resource.uri
            wh.ip_address = None
            wh.date = resource.lastmod
            wh.content_type = 'text/plain'
            wh.result_code = 200
            wh.checksum = 'aabbcc'
            wh.location = 'loc'
            wf.write_record( WARCRecord( header=wh, payload=resource.path ) )
        wf.close()
        warcsize = os.path.getsize(dumpfile)
        print "Wrote WARC file dump %s with size %d bytes" % (dumpfile,warcsize)
        
    def check_files(self,resourcelist):
        """Go though and check all files in resourcelist, add up size"""
        if (len(resourcelist) > self.max_files):
            raise DumpError("Number of files to dump (%d) exceeds maximum (%d)" % (len(resourcelist),self.max_files))
        total_size = 0 #total size of all files in bytes
        for resource in resourcelist:
            if (resource.path is None):
                #explicit test because exception raised by getsize otherwise confusing
                raise DumpError("No file path defined for resource %s" % resource.uri)
            total_size += os.path.getsize(resource.path)
        self.total_size = total_size
        print "Total size of files to include in dump %d bytes" % (total_size)
        if (total_size > self.max_size):
            raise DumpError("Size of files to dump (%d) exceeds maximum (%d)" % (total_size,self.max_size))
