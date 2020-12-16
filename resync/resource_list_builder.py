"""ResourceListBuilder to create ResourceList objects."""

import os
import os.path
import re
import sys
import time
import logging
from defusedxml.ElementTree import parse

from .hashes import Hashes
from .resource import Resource
from .resource_list import ResourceList
from .sitemap import Sitemap
from .w3c_datetime import datetime_to_str


class ResourceListBuilder():
    """ResourceListBuilder to create ResourceList objects.

    Currently implements build from files on disk only.

    Attributes:
    - set_hashes to indicate which hashes should be calculated for each resource
    - set_path set true to add path attribute for each resource
    - set_length set true to include file length in resource_list (defaults true)
    - exclude_dirs is a list of directory names to exclude
      (defaults to ['CVS','.git'))
    """

    def __init__(self, mapper=None, set_hashes=None,
                 set_length=True, set_path=False):
        """Create ResourceListBuilder object, optionally set options.

        The mapper attribute must be set before a call to from_disk() in order to
        map between local filenames and URIs.

        The following attributes may be set to determine information added to
        each Resource object based on the disk scan:
        - set_hashes - Set of digests to computer for each resource. This may add
        significant time to the scan process as each file has to be read to
        compute the hash. Empty set or None means no hashes calculated
        - set_length - False to not add length for each resources
        - set_path - True to add local path information for each file/resource
        """
        self.mapper = mapper
        self.set_path = set_path
        self.set_hashes = set_hashes if (set_hashes and len(set_hashes) > 0) else None
        self.set_length = set_length
        self.exclude_files = [r'sitemap\d{0,5}.xml']
        self.exclude_dirs = ['CVS', '.git']
        self.include_symlinks = False
        # Used internally only:
        self.logger = logging.getLogger('resync.resource_list_builder')
        self.compiled_exclude_files = []

    def add_exclude_files(self, exclude_patterns):
        """Add more patterns of files to exclude while building resource_list."""
        for pattern in exclude_patterns:
            self.exclude_files.append(pattern)

    def compile_excludes(self):
        """Compile a set of regexps for files to be exlcuded from scans."""
        self.compiled_exclude_files = []
        for pattern in self.exclude_files:
            try:
                self.compiled_exclude_files.append(re.compile(pattern))
            except re.error as e:
                raise ValueError(
                    "Bad python regex in exclude '%s': %s" % (pattern, str(e)))

    def exclude_file(self, file):
        """True if file should be exclude based on name pattern."""
        for pattern in self.compiled_exclude_files:
            if (pattern.match(file)):
                return(True)
        return(False)

    def from_disk(self, resource_list=None, paths=None):
        """Create or extend resource_list with resources from disk scan.

        Assumes very simple disk path to URL mapping (in self.mapping): chop
        path and replace with url_path. Returns the new or extended ResourceList
        object.

        If a resource_list is specified then items are added to that rather
        than creating a new one.

        If paths is specified then these are used instead of the set
        of local paths in self.mapping.

        Example usage with mapping start paths:

        mapper=Mapper('http://example.org/path','/path/to/files')
        rlb = ResourceListBuilder(mapper=mapper)
        m = rlb.from_disk()

        Example usage with explicit paths:

        mapper=Mapper('http://example.org/path','/path/to/files')
        rlb = ResourceListBuilder(mapper=mapper)
        m = rlb.from_disk(paths=['/path/to/files/a','/path/to/files/b'])
        """
        num = 0
        # Either use resource_list passed in or make a new one
        if (resource_list is None):
            resource_list = ResourceList()
        # Compile exclude pattern matches
        self.compile_excludes()
        # Work out start paths from map if not explicitly specified
        if (paths is None):
            paths = []
            for map in self.mapper.mappings:
                paths.append(map.dst_path)
        # Set start time unless already set (perhaps because building in
        # chunks)
        if (resource_list.md_at is None):
            resource_list.md_at = datetime_to_str()
        # Run for each map in the mappings
        for path in paths:
            self.logger.info("Scanning disk from %s" % (path))
            self.from_disk_add_path(path=path, resource_list=resource_list)
        # Set end time
        resource_list.md_completed = datetime_to_str()
        return(resource_list)

    def from_disk_add_path(self, path=None, resource_list=None):
        """Add to resource_list with resources from disk scan starting at path."""
        # sanity
        if (path is None or resource_list is None or self.mapper is None):
            raise ValueError("Must specify path, resource_list and mapper")
        # is path a directory or a file? for each file: create Resource object,
        # add, increment counter
        if (sys.version_info < (3, 0)):
            path = path.decode('utf-8')
        if os.path.isdir(path):
            num_files = 0
            for dirpath, dirs, files in os.walk(path, topdown=True):
                for file_in_dirpath in files:
                    num_files += 1
                    if (num_files % 50000 == 0):
                        self.logger.info(
                            "ResourceListBuilder.from_disk_add_path: %d files..." % (num_files))
                    self.add_file(resource_list=resource_list,
                                  dir=dirpath, file=file_in_dirpath)
                    # prune list of dirs based on self.exclude_dirs
                    for exclude in self.exclude_dirs:
                        if exclude in dirs:
                            self.logger.debug("Excluding dir %s" % (exclude))
                            dirs.remove(exclude)
        else:
            # single file
            self.add_file(resource_list=resource_list, file=path)

    def add_file(self, resource_list=None, dir=None, file=None):
        """Add a single file to resource_list.

        Follows object settings of set_path, set_hashes and set_length.
        """
        try:
            if self.exclude_file(file):
                self.logger.debug("Excluding file %s" % (file))
                return
            # get abs filename and also URL
            if (dir is not None):
                file = os.path.join(dir, file)
            if (not os.path.isfile(file) or not (
                    self.include_symlinks or not os.path.islink(file))):
                return
            uri = self.mapper.dst_to_src(file)
            if (uri is None):
                raise Exception("Internal error, mapping failed")
            file_stat = os.stat(file)
        except OSError as e:
            sys.stderr.write("Ignoring file %s (error: %s)" % (file, str(e)))
            return
        timestamp = file_stat.st_mtime  # UTC
        r = Resource(uri=uri, timestamp=timestamp)
        if (self.set_path):
            # add full local path
            r.path = file
        if (self.set_hashes):
            hasher = Hashes(self.set_hashes, file)
            if ('md5' in self.set_hashes):
                r.md5 = hasher.md5
            if ('sha-1' in self.set_hashes):
                r.sha1 = hasher.sha1
            if ('sha-256' in self.set_hashes):
                r.sha256 = hasher.sha256
        if (self.set_length):
            # add length
            r.length = file_stat.st_size
        resource_list.add(r)
