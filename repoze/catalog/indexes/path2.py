from zope.interface import implements

import BTrees

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = ()

class CatalogPathIndex2(CatalogIndex):
    """Index for model paths (tokens separated by '/' characters or
    tuples representing a traversl path)

    A path index may be queried to obtain all subobjects (optionally
    limited by depth) of a certain path.

    This index differs from the original
    ``repoze.catalog.indexes.path.CatalogPath`` index inasmuch as it
    actually retains a graph representation of the objects in the path
    space instead of relying on 'level' information; query results
    relying on this level information may or may not be correct for
    any given tree.  Use of this index is suggested rather than the
    ``path`` index.
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

    def __len__(self):
        return len(self.docid_to_path)

    def __nonzero__(self):
        return True

    def _getPathTuple(self, path):
        if not path:
            raise ValueError('path must be nonempty (not %s)' % str(path))

        if isinstance(path, basestring):
            path = path.rstrip('/')
            path = tuple(path.split('/'))

        if path[0] != '':
            raise ValueError('Path must be absolute (not %s)' % str(path))

        return tuple(path)
        
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

    def search(self, path, depth=None, include_path=False):
        """ Provided a path string (e.g. ``/path/to/object``) or a
        path tuple (e.g. ``('', 'path', 'to', 'object')``, or a path
        list (e.g. ``['', 'path', 'to' object'])``), search the index
        for document ids representing subelements of the path
        specified by the path argument.

        If the ``path`` argment is specified as a tuple or list, its
        first element must be the empty string.  If the ``path``
        argument is specified as a string, it must begin with a ``/``
        character.  In other words, paths passed to the ``search``
        method must be absolute.

        If the ``depth`` argument is specified, return only documents
        at this depth and below.  Depth ``0`` will returns the empty
        set (or only the docid for the ``path`` specified if
        ``include_path`` is also True).  Depth ``1`` will return
        docids related to direct subobjects of the path (plus the
        docid for the ``path`` specified if ``include_path`` is also
        True).  Depth ``2`` will return docids related to direct
        subobjects and the docids of the children of those subobjects,
        and so on.

        If ``include_path`` is False, the docid of the object
        specified by the ``path`` argument is *not* returned as part
        of the search results.  If ``include_path`` is True, the
        object specified by the ``path`` argument *is* returned as
        part of the search results.
        """
        path = self._getPathTuple(path)
        sets = []

        if include_path:
            docid = self.path_to_docid.get(path)
            if docid is not None:
                sets.append(self.family.IF.Set([docid]))

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
        """ Search the path index using the query.  If ``query`` is a
        string, a tuple, or a list, it is treated as the ``path``
        argument to use to search.  If it is any other object, it is
        assumed to be a dictionary with at least a value for the
        ``query`` key, which is treated as a path.  The dictionary can
        also optionally specify the ``depth`` and whether to include
        the docid referenced by the path argument (the ``query`` key)
        in the set of docids returned (``include_path``).  See the
        documentation for the ``search`` method of this class to
        understand paths, depths, and the ``include_path`` argument.
        """
        if isinstance(query, (basestring, tuple, list)):
            path = query
            depth = None
            include_path = False
        else:
            path = query['query']
            depth = query.get('depth', None)
            include_path = query.get('include_path', False)

        return self.search(path, depth, include_path)
