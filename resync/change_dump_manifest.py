"""ResourceSync ChangeDumpManifest object.

A ChangeDumpManifest lists the set of files/resources included 
within a content package that is included in a ChangeDump. 

The ChangeeDumpManifest object will include the change type,
a path for each item (except in the case of "deleted"), and may 
also contain metadata and links.

Described in specification at:
http://www.openarchives.org/rs/resourcesync#ChangeDumpManifest
"""

from .change_list import ChangeList

class ChangeDumpManifest(ChangeList):

    """Class representing a Change Dump Manifest.

    A ChangeDumpManifest comprises a set of files/resources
    in a content package. Properties much Like a ChangeList
    and implemented as a sub-class of ChangeeList.
    """

    def __init__(self, resources=None, md=None, ln=None, uri=None, allow_multifile=None, mapper=None):
        """Initialize ChangeDumpManifest.

        Simply sets capability_name to 'changedump-manifest' when
        subclassing ChangeList.
        """
        super(ChangeDumpManifest, self).__init__(resources=resources, md=md, ln=ln, uri=uri, mapper=mapper)
        self.capability_name = 'changedump-manifest'
