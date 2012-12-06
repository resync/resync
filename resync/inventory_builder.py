"""InventoryBuilder to create Inventory objects from various sources

Attributes:
- do_md5 set true to calculate MD5 sums for all files
- do_size set true to include file size in inventory
- exclude_dirs is a list of directory names to exclude
  (defaults to ['CVS','.git'))
"""

import os
import os.path
import re
import time
import logging
from urllib import URLopener
from xml.etree.ElementTree import parse

from resource import Resource
from inventory import Inventory
from sitemap import Sitemap
from utils import compute_md5_for_file

class InventoryBuilder():

    def __init__(self, do_md5=False, do_size=True, mapper=None):
        """Create InventoryBuilder object, optionally set options

        Optionaly sets the following attributes:
        - do_md5 - True to add md5 digests for each resource
        - do_size - False to not add size for each resources
        """
        self.do_md5 = do_md5
        self.do_size = do_size
        self.mapper = mapper
        self.exclude_files = ['sitemap\d{0,5}.xml']
        self.exclude_dirs = ['CVS','.git']
        self.include_symlinks = False
        # Used internally only:
        self.logger = logging.getLogger('inventory_builder')
        self.compiled_exclude_files = []

    def add_exclude_files(self, exclude_patterns):
        """Add more patterns of files to exclude while building inventory"""
        for pattern in exclude_patterns:
            self.exclude_files.append(pattern)

    def compile_excludes(self):
        self.compiled_exclude_files = []
        for pattern in self.exclude_files:
            self.compiled_exclude_files.append(re.compile(pattern))

    def exclude_file(self, file):
        """True if file should be exclude based on name pattern"""
        for pattern in self.compiled_exclude_files:
            if (pattern.match(file)):
                return(True)
        return(False)

    def from_disk(self,inventory=None):
        """Create or extend inventory with resources from disk scan

        Assumes very simple disk path to URL mapping: chop path and
        replace with url_path. Returns the new or extended Inventory
        object.

        If a inventory is specified then items are added to that rather
        than creating a new one.

        mapper=Mapper('http://example.org/path','/path/to/files')
        mb = InventoryBuilder(mapper=mapper)
        m = inventory_from_disk()
        """
        num=0
        # Either use inventory passed in or make a new one
        if (inventory is None):
            inventory = Inventory()
        # Compile exclude pattern matches
        self.compile_excludes()
        # Run for each map in the mappings
        for map in self.mapper.mappings:
            self.logger.info("Scanning disk for %s" % (str(map)))
            self.from_disk_add_map(inventory=inventory, map=map)
        return(inventory)

    def from_disk_add_map(self, inventory=None, map=None):
        # sanity
        if (inventory is None or map is None):
            raise ValueError("Must specify inventory and map")
        path=map.dst_path
        #print "walking: %s" % (path)
        # for each file: create Resource object, add, increment counter
	num_files=0
        for dirpath, dirs, files in os.walk(path,topdown=True):
            for file_in_dirpath in files:
		num_files+=1
		if (num_files%50000 == 0):
		    self.logger.info("InventoryBuilder.from_disk_add_map: %d files..." % (num_files))
                try:
                    if self.exclude_file(file_in_dirpath):
                        self.logger.debug("Excluding file %s" % (file_in_dirpath))
                        continue
                    # get abs filename and also URL
                    file = os.path.join(dirpath,file_in_dirpath)
                    if (not os.path.isfile(file) or not (self.include_symlinks or not os.path.islink(file))):
                        continue
                    uri = map.dst_to_src(file)
                    if (uri is None):
                        raise Exception("Internal error, mapping failed")
                    file_stat=os.stat(file)
                except OSError as e:
                    sys.stderr.write("Ignoring file %s (error: %s)" % (file,str(e)))
                    continue
                timestamp = file_stat.st_mtime #UTC
                r = Resource(uri=uri,timestamp=timestamp,path=file)
                if (self.do_md5):
                    # add md5
                    r.md5=compute_md5_for_file(file)
                if (self.do_size):
                    # add size
                    r.size=file_stat.st_size
                inventory.add(r)
            # prune list of dirs based on self.exclude_dirs
            for exclude in self.exclude_dirs:
                if exclude in dirs:
                    self.logger.debug("Excluding dir %s" % (exclude))
                    dirs.remove(exclude)
        return(inventory)
