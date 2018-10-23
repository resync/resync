"""ResourceSync client state class.

The client requires memory of state to support incremental
synchronization. At minimum it must store the source timestamp
of the last change seen.
"""

import sys
import os.path
import datetime
import distutils.dir_util
import re
import time
import logging
try:  # python3
    from configparser import ConfigParser, NoSectionError, NoOptionError
except ImportError:  # pragma: no cover python2
    from ConfigParser import SafeConfigParser as ConfigParser, NoSectionError, NoOptionError  # pragma: no cover


class ClientState(object):
    """Read and store client state on disk."""

    def __init__(self):
        """Initialize ClientState object with default status file name."""
        self.status_file = '.resync-client-status.cfg'

    def set_state(self, site, timestamp=None):
        """Write status dict to client status file.

        FIXME - should have some file lock to avoid race
        """
        parser = ConfigParser()
        parser.read(self.status_file)
        status_section = 'incremental'
        if (not parser.has_section(status_section)):
            parser.add_section(status_section)
        if (timestamp is None):
            parser.remove_option(
                status_section,
                self.config_site_to_name(site))
        else:
            parser.set(
                status_section,
                self.config_site_to_name(site),
                str(timestamp))
        with open(self.status_file, 'w') as configfile:
            parser.write(configfile)
            configfile.close()

    def get_state(self, site):
        """Read client status file and return dict."""
        parser = ConfigParser()
        status_section = 'incremental'
        parser.read(self.status_file)
        timestamp = None
        try:
            timestamp = float(
                parser.get(
                    status_section,
                    self.config_site_to_name(site)))
        except NoSectionError as e:
            pass
        except NoOptionError as e:
            pass
        return(timestamp)

    def config_site_to_name(self, name):
        """Convert site name to safe string for config.

        Simply replaces any non-word chars with underscore. This could
        lead to multiple site names mapping to one config name but
        probably not too likely.
        """
        return(re.sub(r"[^\w]", '_', name))
