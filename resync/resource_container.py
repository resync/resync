"""ResourceSync Resource Container object

All documents in ResourceSync have the same types of information:
they have some top-level metadata and links, and then a list of
resources, each of which may also have metadata and links. This 
class implements this model.

This is a base class for the ListBase class which is in turn the
base class for ResourceList, ChangeList, etc. This class provides
only the data storage and manipulation, ListBase adds IO.
"""
import collections
from w3c_datetime import datetime_to_str

class ResourceContainer(object):
    """Class containing resource-like objects

    Core functionality::
    - resources property that is the set/list of resources
    -- add() to add a resource-like object to self.resources
    -- iter() to get iterator over self.resource in appropriate order
    - md property that is a dict of metadata
    - ln property that is a list of links
    - uri is optional identifier of this container object

    Derived classes may add extra functionality such as len() etc..
    However, any code designed to work with any ResourceContainer
    should use only the core functionality.
    """

    def __init__(self, resources=None, md=None, ln=None, uri=None):
        self.resources=(resources if (resources is not None) else [])
        self.md=(md if (md is not None) else {})
        self.ln=(ln if (ln is not None) else [])
        self.uri=uri
        self.capability_name=None
        self.capability_md=None

    def __iter__(self):
        """Iterator over all the resources in this resource list

        Baseline implementation use iterator given by resources property
        """
        return(iter(self.resources))

    @property
    def capability(self):
        if ('capability' in self.md):
            return(self.md['capability'])
        else:
            return(None)

    @capability.setter
    def capability(self,capability):
        """Get/set the capability attribute of this resource container"""
        self.md['capability']=capability

    @property
    def md_from(self):
        """ Convenient access to <rs:md from="" .../> """
        if ('from' in self.md):
            return(self.md['from'])
        else:
            return(None)

    @md_from.setter
    def md_from(self,md_from):
        """Get/set the from attribute of this resource container"""
        self.md['from']=md_from

    @property
    def md_until(self):
        """ Convenient access to <rs:md until="" .../> """
        if ('until' in self.md):
            return(self.md['until'])
        else:
            return(None)

    @md_until.setter
    def md_until(self,md_until):
        """Get/set the until attribute of this resource container"""
        self.md['until']=md_until

    @property
    def md_at(self):
        """ Convenient access to <rs:md at="" .../> """
        if ('at' in self.md):
            return(self.md['at'])
        else:
            return(None)

    @md_at.setter
    def md_at(self,md_at):
        """Get/set the at attribute of this resource container"""
        self.md['at']=md_at

    @property
    def md_completed(self):
        """ Convenient access to <rs:md completed="" .../> """
        if ('completed' in self.md):
            return(self.md['completed'])
        else:
            return(None)

    @md_completed.setter
    def md_completed(self,md_completed):
        """Get/set the completed attribute of this resource container"""
        self.md['completed']=md_completed

    def link(self,rel):
        """Look for link with specified rel, return else None"""
        for link in self.ln:
            if ('rel' in link and
                link['rel']==rel):
                return(link)
        return(None)

    def link_href(self,rel):
        """Look for link with specified rel, return href from it or None"""
        link = self.link(rel)
        if (link is not None):
            link = link['href']
        return(link)

    def link_set(self,rel,href,**atts):
        """Set/create link with specified rel, set href and any other attributes

        Any link element must have both rel and href values, the specification
        also defines the type attributes and others are permitted also
        """
        link = self.link(rel)
        if (link is not None):
            # overwrite current value
            link['href'] = href
        else:
            # create new link
            link = {'rel':rel,'href':href}
            self.ln.append(link)
        for k in atts:
            link[k] = atts[k]

    @property
    def describedby(self):
        """Convenient access to <rs:ln rel="describedby" href="uri">"""
        return(self.link_href('describedby'))

    @describedby.setter
    def describedby(self,uri):
        """Set ResourceSync Description link to given URI"""
        self.link_set('describedby',uri)

    @property
    def up(self):
        """Convenient access to <rs:ln rel="resourcesync" href="uri">"""
        return(self.link_href('up'))

    @up.setter
    def up(self,uri):
        """Set ResourceSync Up link to given URI"""
        self.link_set('up',uri)

    @property
    def index(self):
        """Convenient access to <rs:ln rel="index" href="uri">"""
        return(self.link_href('index'))

    @index.setter
    def index(self,uri):
        """Set index link to given URI"""
        self.link_set('index',uri)

    def default_capability(self):
        """Set capability name in md

        Every ResourceSync document should have the top-level
        capability attributes.
        """
        if ('capability' not in self.md and self.capability_md is not None):
            self.md['capability']=self.capability_md

    def add(self, resource):
        """Add a resource or an iterable collection of resources to this container

        Must be implemented in derived class
        """
        if isinstance(resource, collections.Iterable):
            for r in resource:
                self.resources.append(r)
        else:
            self.resources.append(resource)

    def uris(self):
        """Return list of all URIs, possibly including dupes"""
        uris = []
        for r in self.resources:
            uris.append(r.uri)
        return(uris)

    def prune_before(self, timestamp):
        """Remove all resources with timestamp earlier than that given
        
        Returns the number of entries removed. Will raise an excpetion
        if there are any entries without a timestamp.
        """
        n = 0
        pruned = []
        for r in self.resources:
            if (r.timestamp is None):
                raise Exception("Entry %s has no timestamp" % (r.uri))
            elif (r.timestamp >= timestamp):
                pruned.append(r)
            else:
                n += 1
        self.resources = pruned
        return(n)

    def prune_dupes(self):
        """Remove all but the last entry for a given resource URI
        
        Returns the number of entries removed. Also removes all entries for a 
        given URI where the first entry is a create and the last entry is a
        delete.
        """
        n = 0
        pruned1 = []
        seen = set()
        deletes = {}
        for r in reversed(self.resources):
            if (r.uri in seen):
                n += 1
                if (r.uri in deletes):
                    deletes[r.uri]=r.change
            else:
                pruned1.append(r)
                seen.add(r.uri)
                if (r.change == 'deleted'):
                    deletes[r.uri]=r.change
        # go through all deletes and prune if first was create
        pruned2 = []
        for r in reversed(pruned1):
            if (r.uri in deletes and deletes[r.uri] == 'created'):
                n += 1
            else:
                pruned2.append(r)
        self.resources=pruned2
        return(n)

    def __str__(self):
        """Return string of all resources in order given by interator"""
        s = ''
        for resource in self:
            s += str(resource) + "\n"
        return(s)
