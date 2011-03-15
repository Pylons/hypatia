import BTrees
from persistent.mapping import PersistentMapping
import transaction

from zope.interface import implements

from repoze.catalog.interfaces import ICatalog
from repoze.catalog.interfaces import ICatalogIndex

class Catalog(PersistentMapping):

    implements(ICatalog)

    family = BTrees.family32

    def __init__(self, family=None):
        PersistentMapping.__init__(self)
        if family is not None:
            self.family = family

    def clear(self):
        """ Clear all indexes in this catalog. """
        for index in self.values():
            index.clear()

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

    def __setitem__(self, name, index):
        """ Add an object which implements
        ``repoze.catalog.interfaces.ICatalogIndex`` to the catalog.
        No other type of object may be added to a catalog."""
        if not ICatalogIndex.providedBy(index):
            raise ValueError('%s does not provide ICatalogIndex')
        return PersistentMapping.__setitem__(self, name, index)

    def search(self, **query):
        """ Use the query terms to perform a query.  Return a tuple of
        (num, resultseq) based on the merging of results from
        individual indexes.

        .. note:: this method is deprecated as of
                  :mod:`repoze.catalog` version 0.8.  Use
                  :meth:`repoze.catalog.Catalog.query` instead.


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
                index = self.get(index_name)
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
                index = self.get(index_name)
                if index is None:
                    raise ValueError('No such index %s' % index_name)
                result = index.apply_intersect(index_query, result)
                if not result:
                    # empty results
                    return 0, result

        return self.sort_result(result, sort_index, limit, sort_type, reverse)

    def sort_result(self, result, sort_index=None, limit=None, sort_type=None,
                    reverse=False):

        numdocs = len(result)

        if sort_index:
            index = self[sort_index]
            result = index.sort(result, reverse=reverse, limit=limit,
                                sort_type=sort_type)
            if limit:
                numdocs = min(numdocs, limit)
            return numdocs, result
        else:
            return numdocs, result

    def query(self, queryobject, sort_index=None, limit=None, sort_type=None,
              reverse=False, names=None):
        """ Use the arguments to perform a query.  Return a tuple of
        (num, resultseq)."""
        try:
            from repoze.catalog.query import parse_query
            if isinstance(queryobject, basestring):
                queryobject = parse_query(queryobject)
        except ImportError: #pragma NO COVERAGE
            pass
        results = queryobject._apply(self, names)
        return self.sort_result(results, sort_index, limit, sort_type, reverse)

    def apply(self, query):
        return self.search(**query)

def assertint(docid):
    if not isinstance(docid, int):
        raise ValueError('%r is not an integer value; document ids must be '
                         'integers' % docid)

class CatalogFactory(object):
    def __call__(self, connection_handler=None):
        conn = self.db.open()
        if connection_handler:
            connection_handler(conn)
        root = conn.root()
        if root.get(self.appname) is None:
            root[self.appname] = Catalog()
        return root[self.appname]

class FileStorageCatalogFactory(CatalogFactory):
    def __init__(self, filename, appname, **kw):
        """ ``filename`` is a filename to the FileStorage storage,
        ``appname`` is a key name in the root of the FileStorage in
        which to store the catalog, and ``**kw`` is passed as extra
        keyword arguments to :class:`ZODB.DB.DB` when creating a
        database.  Note that when we create a :class:`ZODB.DB.DB`
        instance, if a ``cache_size`` is not passed in ``*kw``, we
        override the default ``cache_size`` value with ``50000`` in
        order to provide a more realistic cache size for modern apps"""
        cache_size = kw.get('cache_size')
        if cache_size is None:
            kw['cache_size'] = 50000

        from ZODB.FileStorage.FileStorage import FileStorage
        from ZODB.DB import DB
        f = FileStorage(filename)
        self.db = DB(f, **kw)
        self.appname = appname

    def __del__(self):
        self.db.close()

class ConnectionManager(object):
    def __call__(self, conn):
        self.conn = conn

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()

    def commit(self, transaction=transaction):
        transaction.commit()

