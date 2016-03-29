"""Dump handler for ResourceSync."""

import logging
import os.path
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from resync.resource_dump_manifest import ResourceDumpManifest

class Dump(object):
    
    """Dump of content for a Resource Dump or Change Dump.

    The resources itearable must be comprised of Resource objects
    which have the path attributes set to indicate the local
    location of the copies of the resources.

       rl = ResourceList()
       # ... add items by whatever means, may have >50k items and/or
       # >100MB total size of files ...
       d = Dump(resources=rl)
       d.write(basename="/tmp/rd_")
       # will create dump files /tmp/rd_00000.zip etc.
    """

    def __init__(self, resources=None, format=None, compress=True):
        """Initialize Dump object and set defaults."""
        self.resources = resources
        self.format = ('zip' if (format is None) else format)
        self.compress = compress
        self.manifest_class = ResourceDumpManifest #FIXME 
        self.max_size = 100*1024*1024 #100MB
        self.max_files = 50000
        self.path_prefix = None
        self.logger = logging.getLogger('resync.dump')
        
    def write(self, basename=None, write_separate_manifests=True):
        """Write one or more dump files to complete this dump.

        Returns the number of dump/archive files written.
        """
        self.check_files()
        n=0
        for manifest in self.partition_dumps():
            dumpbase="%s%05d" % (basename,n)
            dumpfile="%s.%s" % (dumpbase,self.format)
            if (write_separate_manifests):
                manifest.write(basename=dumpbase+'.xml')
            if (self.format == 'zip'):
                self.write_zip(manifest.resources,dumpfile)
            elif (self.format == 'warc'):
                self.write_warc(manifest.resources,dumpfile)
            else:
                raise DumpError("Unknown dump format requested (%s)" % (self.format))
            n+=1
        self.logger.info("Wrote %d dump files" % (n))
        return(n)

    def write_zip(self, resources=None, dumpfile=None):
        """Write a ZIP format dump file.

        Writes a ZIP file containing the resources in the iterable resources along with
        a manifest file manifest.xml (written first). No checks on the size of files
        or total size are performed, this is expected to have been done beforehand.
        """
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
        self.logger.info("Wrote ZIP file dump %s with size %d bytes" % (dumpfile,zipsize))
        
    def write_warc(self, resources=None, dumpfile=None):
        """Write a WARC dump file.

        WARC support is not part of ResourceSync v1.0 (Z39.99 2014) but is left
        in this library for experimentation.
        """
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
        self.logging.info("Wrote WARC file dump %s with size %d bytes" % (dumpfile,warcsize))
        
    def check_files(self,set_length=True,check_length=True):
        """Check all files in self.resources, find longest common prefix.

        Go though and check all files in self.resources, add up size, and find
        longest common path that can be used when writing the dump file. Saved in 
        self.path_prefix.

        Parameters set_length and check_length control control whether then set_length
        attribute should be set from the file size if not specified, and whether any 
        length specified should be checked. By default both are True. In any event, the
        total size calculated is the size of files on disk.
        """
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
            if (size > self.max_size):
                raise DumpError("Size of file (%s, %d) exceeds maximum (%d) dump size" % (resource.path,size,self.max_size))
            total_size += size
        self.path_prefix = path_prefix
        self.total_size = total_size
        self.logger.info("Total size of files to include in dump %d bytes" % (total_size))
        return True

    def partition_dumps(self):
        """Yeild a set of manifest object that parition the dumps.

        Simply adds resources/files to a manifest until their are either the
        the correct number of files or the size limit is exceeded, then yields
        that manifest. 
        """
        manifest=self.manifest_class()
        manifest_size=0
        manifest_files=0
        for resource in self.resources:
            manifest.add(resource)
            manifest_size+=resource.length
            manifest_files+=1
            if (manifest_size>=self.max_size or
                manifest_files>=self.max_files):
                yield(manifest)
                # Need to start a new manifest
                manifest=self.manifest_class()
                manifest_size=0
                manifest_files=0
        if (manifest_files>0):
            yield(manifest)


    def archive_path(self,real_path):
        """Return the archive path for file with real_path.

        Mapping is based on removal of self.path_prefix which is determined
        by self.check_files().
        """
        if (not self.path_prefix):
            return(real_path)
        else:
            return( os.path.relpath(real_path,self.path_prefix) )


class DumpError(Exception):
    
    """Error class used by Dump() objects."""
    
    pass
