import BTrees
from persistent.mapping import PersistentMapping

from zope.interface import implementer

from ..interfaces import ICatalog
from ..interfaces import ICatalogQuery

from ..query import parse_query

@implementer(ICatalog)
class Catalog(PersistentMapping):

    family = BTrees.family64

    def __init__(self, family=None):
        PersistentMapping.__init__(self)
        if family is not None:
            self.family = family

    def __setitem__(self, name, index):
        index.__name__ = name
        return PersistentMapping.__setitem__(self, name, index)

    def reset(self):
        """ Clear all indexes in this catalog. """
        for index in self.values():
            index.reset()

    def index_doc(self, docid, obj):
        """Register the document represented by ``obj`` in indexes of
        this catalog using docid ``docid``."""
        assertint(docid)
        for index in self.values():
            index.index_doc(docid, obj)

    def unindex_doc(self, docid):
        """Unregister the document id from indexes of this catalog."""
        assertint(docid)
        for index in self.values():
            index.unindex_doc(docid)

    def reindex_doc(self, docid, obj):
        """ Reindex the document referenced by docid using the object
        passed in as ``obj`` (typically just does the equivalent of
        ``unindex_doc``, then ``index_doc``, but specialized indexes
        can override the method that this API calls to do less work. """
        assertint(docid)
        for index in self.values():
            index.reindex_doc(docid, obj)

def assertint(docid):
    if not isinstance(docid, int):
        raise ValueError('%r is not an integer value; document ids must be '
                         'integers' % docid)


@implementer(ICatalogQuery)
class CatalogQuery(object):
    """ Legacy query API for non-index-based queries; might be useful if/when
    an index-based query doesn't work properly, or a particular contstraint
    can't be spelled with one."""

    family = BTrees.family64
    
    def __init__(self, catalog, family=None):
        self.catalog = catalog
        if family is not None:
            self.family = family

    def sort(self, docidset, sort_index, limit=None, sort_type=None,
             reverse=False):
        """ Return ``(num, sorted-resultseq)`` for the concrete docidset. """

        result = docidset
        numdocs = len(docidset)

        if sort_index:
            index = self.catalog[sort_index]
            result = index.sort(
                result, reverse=reverse, limit=limit, sort_type=sort_type
                )
            if limit:
                numdocs = min(numdocs, limit)
            return numdocs, result
        else:
            return numdocs, result

    def search(self, **query):
        """ Use the query terms to perform a query.  Return a tuple of
        (num, resultseq) based on the merging of results from
        individual indexes.

        .. note::

           This method is deprecated. Use
           :func:`hypatia.catalog.CatalogQuery.__call__` instead.


        """
        sort_index = None
        reverse = False
        limit = None
        sort_type = None
        index_query_order = None

        if 'sort_index' in query:
            sort_index = query.pop('sort_index')
        if 'reverse' in query:
            reverse = query.pop('reverse')
        if 'limit' in query:
            limit = query.pop('limit')
        if 'sort_type' in query:
            sort_type = query.pop('sort_type')
        if 'index_query_order' in query:
            index_query_order = query.pop('index_query_order')

        if index_query_order is None:
            # unordered query (use apply)
            results = []
            for index_name, index_query in query.items():
                index = self.catalog.get(index_name)
                if index is None:
                    raise ValueError('No such index %s' % index_name)
                r = index.apply(index_query)
                if not r:
                    # empty results, bail early; intersect will be null
                    return 0, r

                results.append((len(r), r))

            if not results:
                return 0, ()

            results.sort() # order from smallest to largest
            _, result = results.pop(0)
            for _, r in results:
                _, result = self.family.IF.weightedIntersection(result, r)

            if not result:
                return 0, ()

        else:
            # ordered query (use apply_intersect)
            result = None
            _marker = object()
            for index_name in index_query_order:
                index_query = query.get(index_name, _marker)
                if index_query is _marker:
                    continue
                index = self.catalog.get(index_name)
                if index is None:
                    raise ValueError('No such index %s' % index_name)
                result = index.apply_intersect(index_query, result)
                if not result:
                    # empty results
                    return 0, result

        return self.sort(result, sort_index, limit, sort_type, reverse)

    def query(self, queryobject, sort_index=None, limit=None, sort_type=None,
              reverse=False, names=None):
        """ Use the arguments to perform a query.  Return a tuple of
        (num, resultseq)."""
        if isinstance(queryobject, basestring):
            queryobject = parse_query(queryobject, self.catalog)
        results = queryobject._apply(names)
        return self.sort(results, sort_index, limit, sort_type, reverse)

    __call__ = query

