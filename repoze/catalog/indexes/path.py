from zope.interface import implements
from persistent import Persistent

import BTrees

from BTrees.Length import Length

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = ()

class CatalogPathIndex(CatalogIndex):

    """Index for model paths (tokens separated by '/' characters)

    A path index stores all path components of the physical path of an object.

    Internal datastructure:

    - a physical path of an object is split into its components

    - every component is kept as a  key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all docids with this path component on this level'


    Query types supported:

    - Eq

    - NotEq

    """
    implements(ICatalogIndex)
    useOperator = 'or'

    family = BTrees.family32

    def __init__(self, discriminator):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        self._not_indexed = self.family.IF.Set()
        self.clear()

    def clear(self):
        self._depth = 0
        self._index = self.family.OO.BTree()
        self._unindex = self.family.IO.BTree()
        self._length = Length(0)

    def insertEntry(self, comp, id, level):
        """Insert an entry.

           comp is a path component
           id is the docid
           level is the level of the component inside the path
        """

        if not self._index.has_key(comp):
            self._index[comp] = self.family.IO.BTree()

        if not self._index[comp].has_key(level):
            self._index[comp][level] = self.family.IF.TreeSet()

        self._index[comp][level].insert(id)
        if level > self._depth:
            self._depth = level

    def index_doc(self, docid, object):
        if callable(self.discriminator):
            value = self.discriminator(object, _marker)
        else:
            value = getattr(object, self.discriminator, _marker)

        if value is _marker:
            # unindex the previous value
            self.unindex_doc(docid)

            # Store docid in set of unindexed docids
            self._not_indexed.add(docid)

            return None

        if isinstance(value, Persistent):
            raise ValueError('Catalog cannot index persistent object %s' %
                             value)

        if docid in self._not_indexed:
            # Remove from set of unindexed docs if it was in there.
            self._not_indexed.remove(docid)

        path = value

        if isinstance(path, (list, tuple)):
            path = '/'+ '/'.join(path[1:])

        comps = filter(None, path.split('/'))

        if not self._unindex.has_key(docid):
            self._length.change(1)

        for i in range(len(comps)):
            self.insertEntry(comps[i], docid, i)

        self._unindex[docid] = path
        return 1

    def unindex_doc(self, docid):
        _not_indexed = self._not_indexed
        if docid in _not_indexed:
            _not_indexed.remove(docid)

        if not self._unindex.has_key(docid):
            return

        comps =  self._unindex[docid].split('/')

        for level in range(len(comps[1:])):
            comp = comps[level+1]

            try:
                self._index[comp][level].remove(docid)

                if not self._index[comp][level]:
                    del self._index[comp][level]

                if not self._index[comp]:
                    del self._index[comp]
            except KeyError:
                pass

        self._length.change(-1)
        del self._unindex[docid]

    def _indexed(self):
        return self._unindex.keys()

    def search(self, path, default_level=0):
        """
        path is either a string representing a
        relative URL or a part of a relative URL or
        a tuple (path,level).

        level >= 0  starts searching at the given level
        level <  0  not implemented yet
        """
        if isinstance(path, basestring):
            level = default_level
        else:
            level = int(path[1])
            path  = path[0]

        comps = filter(None, path.split('/'))

        if len(comps) == 0:
            return self.family.IF.Set(self._unindex.keys())

        results = None
        if level >= 0:
            for i, comp in enumerate(comps):
                if not self._index.has_key(comp):
                    return self.family.IF.Set()
                if not self._index[comp].has_key(level+i):
                    return self.family.IF.Set()
                results = self.family.IF.intersection(
                    results, self._index[comp][level+i])

        else:
            for level in range(self._depth + 1):
                ids = None
                for i, comp in enumerate(comps):
                    try:
                        ids = self.family.IF.intersection(
                            ids, self._index[comp][level+i])
                    except KeyError:
                        break
                else:
                    results = self.family.IF.union(results, ids)
        return results

    def numObjects(self):
        """ return the number distinct values """
        return len(self._unindex)

    def getEntryForObject(self, docid):
        """ Takes a document ID and returns all the information
            we have on that specific object.
        """
        return self._unindex.get(docid)

    def apply(self, query):
        """
        """
        level = 0
        operator = self.useOperator

        if isinstance(query, basestring):
            paths = [query]
        elif isinstance(query, (tuple, list)):
            paths = query
        else:
            paths = query.get('query', [])
            if isinstance(paths, basestring):
                paths = [ paths ]
            level = query.get('level', 0)
            operator = query.get('operator', self.useOperator).lower()

        sets = []
        for path in paths:
            sets.append(self.search(path, level))

        if operator == 'or':
            rs = self.family.IF.multiunion(sets)

        else:
            rs = None
            sets.sort(lambda x, y: cmp(len(x), len(y)))
            for set in sets:
                rs = self.family.IF.intersection(rs, set)
                if not rs:
                    break

        if rs:
            return rs
        else:
            return self.family.IF.Set()

    applyEq = apply
