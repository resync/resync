"""Dump handler for ResourceSync"""

import os.path
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from resync.resource_dump_manifest import ResourceDumpManifest

class DumpError(Exception):
    pass

class Dump(object):
    """Dump of content for a Resource Dump or Change Dump

    The resources itearable must be comprised of Resource objects
    which have the path attributes set to indicate the local
    location of the copies of the resources.

       rl = ResourceList()
       # ... add items by whatever means, may have >50k items and/or
       # >100MB total size of files ...
       d = Dump(rl)
       d.write()
    """

    def __init__(self, resources=None, format=None, compress=True):
        self.resources = resources
        self.format = ('zip' if (format is None) else format)
        self.compress = compress
        self.max_size = 100*1024*1024 #100MB
        self.max_files = 50000
        self.path_prefix = None
        
    def write(self, dumpfile=None):
        """Write one or more dump files to complete this dump"""
        self.check_files()
        n=0
        for manifest in self.partition_dumps():
            if (self.format == 'zip'):
                self.write_zip(self.resources,dumpfile)
            elif (self.format == 'warc'):
                self.write_warc(self.resources,dumpfile)
            else:
                raise DumpError("Unknown dump format requested (%s)" % (self.format))
            n+=1
        print "Wrote %d dump files" % (n)

    def write_zip(self, resources=None, dumpfile=None):
        """Write a ZIP format dump file"""
        compression = ( ZIP_DEFLATED if self.compress else ZIP_STORED )
        zf = ZipFile(dumpfile, mode="w", compression=compression, allowZip64=True)
        # Write resources first
        rdm = ResourceDumpManifest(resources=resources)
        real_path = {}
        for resource in resources:
            archive_path = self.archive_path(resource.path)
            real_path[archive_path] = resource.path
            resource.path = archive_path
        zf.writestr('manifest.xml',rdm.as_xml())
        # Add all files in the resources
        for resource in resources:
            zf.write(real_path[resource.path], arcname=resource.path)
        zf.close()
        zipsize = os.path.getsize(dumpfile)
        print "Wrote ZIP file dump %s with size %d bytes" % (dumpfile,zipsize)
        
    def write_warc(self, resources=None, dumpfile=None):
        """Write a WARC dump file"""
        # Load library late as we want to be able to run rest of code 
        # without this installed
        try:
            from warc import WARCFile,WARCHeader,WARCRecord
        except:
            raise DumpError("Failed to load WARC library")
        wf = WARCFile(dumpfile, mode="w", compress=self.compress)
        # Add all files in the resources
        for resource in resources:
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
        
    def check_files(self,set_length=True,check_length=True):
        """Go though and check all files in self.resources, add up size, and find
        longest common path that can be used when writing the dump file. Saved in 
        self.path_prefix.

        Parameters set_length and check_lenght control control whether then set_length
        attribute should be set from the file size if not specified, and whether any 
        length specified should be checked. By default both are True. In any event, the
        total size calculated is the size of files on disk.
        """
        if (len(self.resources) > self.max_files):
            raise DumpError("Number of files to dump (%d) exceeds maximum (%d)" % (len(resources),self.max_files))
        total_size = 0 #total size of all files in bytes
        path_prefix = None
        for resource in self.resources:
            if (resource.path is None):
                #explicit test because exception raised by getsize otherwise confusing
                raise DumpError("No file path defined for resource %s" % resource.uri)
            if (path_prefix is None):
                path_prefix = os.path.dirname(resource.path)
            else:
                path_prefix = os.path.commonprefix( [ path_prefix, os.path.dirname(resource.path) ])
            size = os.path.getsize(resource.path)
            if (resource.length is not None):
                if (check_length and resource.length!=size):
                    raise DumpError("Size of resource %s is %d on disk, not %d as specified" %
                                    (resource.uri, size, resource.length) )
            elif (set_length):
                resource.length = size
            total_size += size
        self.path_prefix = path_prefix
        self.total_size = total_size
        print "Total size of files to include in dump %d bytes" % (total_size)
        if (total_size > self.max_size):
            raise DumpError("Size of files to dump (%d) exceeds maximum (%d)" % (total_size,self.max_size))
        return True

    def partition_dumps(self):
        """Return a set of manifest object that parition the dumps
        """
        manifests=[]
        if (self.total_size<=self.max_size and
            self.total_files<=self.max_files):
            # No need to partition into multiple files
            pass #FIXME - fill in
        else:
            pass #FIXME - fill in 
        return manifests

    def archive_path(self,real_path):
        """Return the archive path for file with real_path

        Mapping is based on removal of self.path_prefix which is determined
        by self.check_files().
        """
        if (not self.path_prefix):
            return(real_path)
        else:
            return( os.path.relpath(real_path,self.path_prefix) )
