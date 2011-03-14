from zope.interface import implements

import BTrees

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = object()


class CatalogPathIndex2(CatalogIndex):  #pragma NO COVERAGE
    """
    DEPRECATED

    Index for model paths (tokens separated by '/' characters or
    tuples representing a model path).

    A path index may be queried to obtain all subobjects (optionally
    limited by depth) of a certain path.

    This index differs from the original
    ``repoze.catalog.indexes.path.CatalogPath`` index inasmuch as it
    actually retains a graph representation of the objects in the path
    space instead of relying on 'level' information; query results
    relying on this level information may or may not be correct for
    any given tree.  Use of this index is suggested rather than the
    ``path`` index.

    Query types supported:

    Eq

    """
    implements(ICatalogIndex)
    attr_discriminator = None # b/w compat

    family = BTrees.family32

    def __init__(self, discriminator, attr_discriminator=None):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        if attr_discriminator is not None and not callable(attr_discriminator):
            if not isinstance(attr_discriminator, basestring):
                raise ValueError('attr_discriminator value must be callable '
                                 'or a string')
        self.attr_discriminator = attr_discriminator
        self.clear()

    def clear(self):
        self.docid_to_path = self.family.IO.BTree()
        self.path_to_docid = self.family.OI.BTree()
        self.adjacency = self.family.IO.BTree()
        self.disjoint = self.family.OO.BTree()
        self.docid_to_attr = self.family.IO.BTree()

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

    def _getObjectPath(self, object):
        if callable(self.discriminator):
            path = self.discriminator(object, _marker)
        else:
            path = getattr(object, self.discriminator, _marker)

        return path

    def _getObjectAttr(self, object):
        if callable(self.attr_discriminator):
            attr = self.attr_discriminator(object, _marker)
        else:
            attr = getattr(object, self.attr_discriminator, _marker)
        return attr

    def index_doc(self, docid, object):

        path = self._getObjectPath(object)

        if path is _marker:
            self.unindex_doc(docid)
            return None

        path = self._getPathTuple(path)

        if self.attr_discriminator is not None:
            attr = self._getObjectAttr(object)
            if attr is not _marker:
                self.docid_to_attr[docid] = attr

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
            if docid in self.docid_to_attr:
                del self.docid_to_attr[docid]
            next_docids = self.adjacency.get(docid)
            if next_docids is None:
                next_docids = self.disjoint.get(path)
                if next_docids is not None:
                    del self.disjoint[path]
                    stack.extend(next_docids)
            else:
                del self.adjacency[docid]
                stack.extend(next_docids)

    def reindex_doc(self, docid, object):
        path = self._getPathTuple(self._getObjectPath(object))

        if self.docid_to_path.get(docid) != path:
            self.unindex_doc(docid)
            self.index_doc(docid, object)
            return True

        else:
            if self.attr_discriminator is not None:
                attr = self._getObjectAttr(object)
                if docid in self.docid_to_attr:
                    if attr is _marker:
                        del self.docid_to_attr[docid]
                        return True
                    elif attr != self.docid_to_attr[docid]:
                        self.docid_to_attr[docid] = attr
                        return True
                else:
                    if attr is not _marker:
                        self.docid_to_attr[docid] = attr
                        return True
            return False

    def _indexed(self):
        return self.docid_to_path.keys()

    def search(self, path, depth=None, include_path=False, attr_checker=None):
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

        If ``attr_checker`` is not None, it must be a callback that
        accepts two arguments: the first argument will be the
        attribute value found, the second argument is a sequence of
        all previous attributes encountered during this search (in
        path order).  If ``attr_checker`` returns True, traversal will
        continue; otherwise, traversal will cease.
        """
        if attr_checker is None:
            return self._simple_search(path, depth, include_path)
        else:
            return self._attr_search(path, depth, include_path, attr_checker)

    def _simple_search(self, path, depth, include_path):
        """ Codepath taken when no attr checker is used """
        path = self._getPathTuple(path)
        sets = []

        if include_path:
            try:
                docid = self.path_to_docid[path]
            except KeyError:
                pass # XXX should we just return an empty set?
            else:
                sets.append(self.family.IF.Set([docid]))

        stack = [path]
        plen = len(path)

        while stack:
            nextpath = stack.pop()
            if depth is not None and len(nextpath) - plen >= depth:
                continue
            try:
                docid = self.path_to_docid[nextpath]
            except KeyError:
                continue    # XXX we can't search from an unindexed root path?
            try:
                theset = self.adjacency[docid]
            except KeyError:
                pass
            else:
                sets.append(theset)
                for docid in theset:
                    try:
                        newpath = self.docid_to_path[docid]
                    except KeyError:
                        continue
                    stack.append(newpath)

        return self.family.IF.multiunion(sets)

    def _attr_search(self, path, depth, include_path, attr_checker):
        """ Codepath taken when an attr checker is used """
        path = self._getPathTuple(path)

        leading_attrs = []
        result = {}
        plen = len(path)

        # make sure we get "leading" attrs
        for p in range(plen-1):
            subpath = path[:p+1]
            try:
                docid = self.path_to_docid[subpath]
            except KeyError:
                continue  # XXX should we just return an empty set?
            attr = self.docid_to_attr.get(docid, _marker)
            if attr is not _marker:
                remove_from_closest(result, subpath, docid)
                leading_attrs.append(attr)
                result[subpath] = ((docid, leading_attrs[:]),
                                   self.family.IF.Set())

        stack = [(path, leading_attrs)]
        attrset = self.family.IF.Set()

        while stack:
            nextpath, attrs = stack.pop()
            try:
                docid = self.path_to_docid[nextpath]
            except KeyError:
                continue # XXX we can't search from an unindexed root path?
            attr = self.docid_to_attr.get(docid, _marker)
            if attr is _marker:
                if include_path and nextpath == path:
                    add_to_closest(
                        result, nextpath, self.family.IF.Set([docid]))
                if depth is not None and len(nextpath) - plen >= depth:
                    continue
            else:
                remove_from_closest(result, nextpath, docid)
                attrs.append(attr)
                if nextpath == path:
                    if include_path:
                        attrset = self.family.IF.Set([docid])
                    else:
                        attrset = self.family.IF.Set()
                else:
                    attrset = self.family.IF.Set([docid])
                result[nextpath] = ((docid, attrs), attrset)
                if depth is not None and len(nextpath) - plen >= depth:
                    continue
            try:
                theset = self.adjacency[docid]
            except KeyError:
                pass
            else:
                add_to_closest(result, nextpath, theset)
                for docid in theset:
                    try:
                        newpath = self.docid_to_path[docid]
                    except KeyError:
                        continue
                    stack.append((newpath, attrs[:]))

        return attr_checker(result.values())

    def apply_intersect(self, query, docids):
        """ Default apply_intersect implementation """
        result = self.apply(query)
        if docids is None:
            return result
        return self.family.IF.weightedIntersection(result, docids)[1]

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
            attr_checker = None
        else:
            path = query['query']
            depth = query.get('depth', None)
            include_path = query.get('include_path', False)
            attr_checker = query.get('attr_checker', None)

        return self.search(path, depth, include_path, attr_checker)

    def applyEq(self, query):
        return self.apply(query)

def add_to_closest(sofar, thispath, theset):
    paths = sofar.keys()
    paths.reverse()
    for path in paths:
        pathlen = len(path)
        if thispath[:pathlen] == path:
            sofar[path][1].update(theset)
            break

def remove_from_closest(sofar, thispath, docid):
    paths = sofar.keys()
    paths.reverse()
    for path in paths:
        pathlen = len(path)
        if thispath[:pathlen] == path:
            theset = sofar[path][1]
            if docid in theset:
                theset.remove(docid)
            break

