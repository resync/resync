"""A set of Resource objects used for Capability List
Indexes and ResourceSync Description documents.

Ordinging is currently alphanumeric (using sorted(..)) on the
uri which is the key. 
"""

class ResourceSet(dict):
    """Implementation of class to store resources in Capability List
    Indexes and ResourceSync Description documents.

    Key properties of this class are:
    - has add(resource) method
    - is iterable and results given in alphanumeric order by resource.uri
    """

    def __iter__(self):
        """Iterator over all the resources in this resource_list"""
        self._iter_next_list = sorted(self.keys())
        self._iter_next_list.reverse()
        return(iter(self._iter_next, None))

    def _iter_next(self):
        if (len(self._iter_next_list)>0):
            return(self[self._iter_next_list.pop()])
        else:
            return(None)

    def add(self, resource, replace=False):
        """Add just a single resource"""
        uri = resource.uri
        if (uri in self and not replace):
            raise ResourceSetDupeError("Attempt to add resource already in this set") 
        self[uri]=resource

class ResourceSetDupeError(Exception):
    pass
