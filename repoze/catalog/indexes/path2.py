from zope.interface import implements

import BTrees

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = ()

class CatalogPathIndex2(CatalogIndex):
    """Index for model paths (tokens separated by '/' characters)

    A path index stores all path components of the physical path of an object.
    """
    implements(ICatalogIndex)

    family = BTrees.family32

    def __init__(self, *arg, **kw):
        super(CatalogPathIndex2, self).__init__(*arg, **kw)
        self.clear()

    def clear(self):
        self.docid_to_path = self.family.IO.BTree()
        self.path_to_docid = self.family.OI.BTree()
        self.adjacency = self.family.IO.BTree()
        self.disjoint = self.family.OO.BTree()

    def numObjects(self):
        return len(self.docid_to_path)

    def _getPathTuple(self, path):
        if not path:
            raise ValueError('path must be nonempty (not %s)' % str(path))

        if isinstance(path, basestring):
            path = path.rstrip('/')
            path = tuple(path.split('/'))

        if path[0] != '':
            raise ValueError('Path must be absolute (not %s)' % str(path))

        return path
        
    def index_doc(self, docid, object):
        if callable(self.discriminator):
            path = self.discriminator(object, _marker)
        else:
            path = getattr(object, self.discriminator, _marker)


        if path is _marker:
            self.unindex_doc(docid)
            return None

        path = self._getPathTuple(path)

        self.docid_to_path[docid] = path
        self.path_to_docid[path] = docid

        if path in self.disjoint:
            self.adjacency[docid] = self.disjoint[path]
            del self.disjoint[path]

        if len(path) > 1:
            parent_path = tuple(path[:-1])
            parent_docid = self.path_to_docid.get(parent_path)
            if parent_docid is None:
                theset = self.disjoint.get(parent_path)
                if theset is None:
                    theset = self.family.IF.Set()
                    self.disjoint[parent_path] = theset
            else:
                theset = self.adjacency.get(parent_docid)
                if theset is None:
                    theset = self.family.IF.Set()
                    self.adjacency[parent_docid] = theset
            theset.insert(docid)

    def unindex_doc(self, docid):
        path = self.docid_to_path.get(docid)
        if path is None:
            return

        if len(path) > 1:
            parent_path = tuple(path[:-1])
            parent_docid = self.path_to_docid.get(parent_path)
            if parent_docid is not None:  # might be disjoint
                self.adjacency[parent_docid].remove(docid)
                if not self.adjacency[parent_docid]:
                    del self.adjacency[parent_docid]
            else:
                self.disjoint[parent_path].remove(docid)
                if not self.disjoint[parent_path]:
                    del self.disjoint[parent_path]

        stack = [docid]

        while stack:
            docid = stack.pop()
            path = self.docid_to_path[docid]
            del self.path_to_docid[path]
            del self.docid_to_path[docid]
            next_docids = self.adjacency.get(docid)
            if next_docids is None:
                next_docids = self.disjoint.get(path)
                if next_docids is not None:
                    del self.disjoint[path]
                    stack.extend(next_docids)
            else:
                del self.adjacency[docid]
                stack.extend(next_docids)

    def search(self, path, depth=None):
        path = self._getPathTuple(path)
        sets = []
        stack = [tuple(path)]
        plen = len(path)

        while stack:
            nextpath = stack.pop()
            if depth is not None and len(nextpath) - plen >= depth:
                continue
            docid = self.path_to_docid.get(nextpath)
            if docid is None:
                continue
            theset = self.adjacency.get(docid)
            if not theset:
                continue
            sets.append(theset)
            for docid in theset:
                newpath = self.docid_to_path.get(docid)
                if newpath is not None:
                    stack.append(newpath)

        return self.family.IF.multiunion(sets)

    def apply(self, query):
        if isinstance(query, basestring):
            path = query
            level = None
        else:
            path = query['query']
            level = query.get('level', None)

        return self.search(path, level)
        

