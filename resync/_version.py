# This is the one place the version number for resync is stored
#
# Format: x.y.z where
# x.y is spec version, see http://www.openarchives.org/rs/x.y/
# z is incremented for revisions within that version, 1...
__version__ = '0.6.2'

# None is to allow the resource not be a change
CHANGE_TYPES = ['created', 'updated', 'deleted', None] 