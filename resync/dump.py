"""Dump handler for ResourceSync"""

import os.path
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from sitemap import Sitemap

class DumpError(Exception):
    pass

class Dump(object):
    """Dump of content for a Resource Dump or Change Dump

    The resource_list must be comprised of Resource objects
    which have the path attributes set to indicate the local
    location of the copies of the resources.
    """

    def __init__(self, format=None, compress=True):
        self.format = ('zip' if (format is None) else format)
        self.compress = compress
        self.max_size = 100*1024*1024 #100MB
        self.max_files = 50000
        self.path_prefix = None
        
    def write(self, resource_list=None, dumpfile=None):
        """Wrapper to Write a dump file"""
        self.check_files(resource_list)
        if (self.format == 'zip'):
            self.write_zip(resource_list,dumpfile)
        elif (self.format == 'warc'):
            self.write_warc(resource_list,dumpfile)
        else:
            raise DumpError("Unknown dump format '%s'" % (self.format))

    def write_zip(self, resource_list=None, dumpfile=None):
        """Write a ZIP format dump file"""
        compression = ( ZIP_DEFLATED if self.compress else ZIP_STORED )
        zf = ZipFile(dumpfile, mode="w", compression=compression, allowZip64=True)
        # Write resource_list first
        s = Sitemap()
        real_path = {}
        for resource in resource_list:
            archive_path = self.archive_path(resource.path)
            real_path[archive_path] = resource.path
            resource.path = archive_path
        zf.writestr('manifest.xml',s.resources_as_xml(resource_list))
        # Add all files in the resource_list
        for resource in resource_list:
            zf.write(real_path[resource.path], arcname=resource.path)
        zf.close()
        zipsize = os.path.getsize(dumpfile)
        print "Wrote ZIP file dump %s with size %d bytes" % (dumpfile,zipsize)
        
    def write_warc(self, resource_list=None, dumpfile=None):
        """Write a WARC dump file"""
        # Load library late as we want to be able to run rest of code 
        # without this installed
        try:
            from warc import WARCFile,WARCHeader,WARCRecord
        except:
            raise DumpError("Failed to load WARC library")
        wf = WARCFile(dumpfile, mode="w", compress=self.compress)
        # Add all files in the resource_list
        for resource in resource_list:
            wh = WARCHeader({})
            wh.url = resource.uri
            wh.ip_address = None
            wh.date = resource.lastmod
            wh.content_type = 'text/plain'
            wh.result_code = 200
            wh.checksum = 'aabbcc'
            wh.location = self.archive_path(resource.path)
            wf.write_record( WARCRecord( header=wh, payload=resource.path ) )
        wf.close()
        warcsize = os.path.getsize(dumpfile)
        print "Wrote WARC file dump %s with size %d bytes" % (dumpfile,warcsize)
        
    def check_files(self,resource_list):
        """Go though and check all files in resource_list, add up size, find common path

        Will find the longest common path prefix that can be used when writing the
        dump file. Saved in self.path_prefix.
        """
        if (len(resource_list) > self.max_files):
            raise DumpError("Number of files to dump (%d) exceeds maximum (%d)" % (len(resource_list),self.max_files))
        total_size = 0 #total size of all files in bytes
        path_prefix = None
        for resource in resource_list:
            if (resource.path is None):
                #explicit test because exception raised by getsize otherwise confusing
                raise DumpError("No file path defined for resource %s" % resource.uri)
            if (path_prefix is None):
                path_prefix = os.path.dirname(resource.path)
            else:
                path_prefix = os.path.commonprefix( [ path_prefix, os.path.dirname(resource.path) ])
            total_size += os.path.getsize(resource.path)
        self.path_prefix = path_prefix
        self.total_size = total_size
        print "Total size of files to include in dump %d bytes" % (total_size)
        if (total_size > self.max_size):
            raise DumpError("Size of files to dump (%d) exceeds maximum (%d)" % (total_size,self.max_size))

    def archive_path(self,real_path):
        """Return the archive path for file with real_path

        Mapping is based on removal of self.path_prefix which is determined
        by self.check_files().
        """
        if (not self.path_prefix):
            return(real_path)
        else:
            return( os.path.relpath(real_path,self.path_prefix) )
