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
        individual indexes."""
        sort_index = None
        reverse = False
        limit = None
        if 'sort_index' in query:
            sort_index = query.pop('sort_index')
        if 'reverse' in query:
            reverse = query.pop('reverse')
        if 'limit' in query:
            limit = query.pop('limit')

        results = []
        for index_name, index_query in query.items():
            index = self.get(index_name)
            if index is None:
                raise ValueError('No such index %s' % index_name)
            r = index.apply(index_query)
            if r is None:
                continue
            if not r:
                # empty results
                return 0, r
            results.append((len(r), r))

        if not results:
            # no applicable indexes, so catalog was not applicable
            return 0, ()

        results.sort() # order from smallest to largest

        _, result = results.pop(0)
        for _, r in results:
            _, result = self.family.IF.weightedIntersection(result, r)

        numdocs = len(result)

        if sort_index:
            index = self[sort_index]
            result = index.sort(result, reverse=reverse, limit=limit)
            if limit:
                numdocs = min(numdocs, limit)
            return numdocs, result
        else:
            return numdocs, result

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
    def __init__(self, filename, appname):
        from ZODB.FileStorage.FileStorage import FileStorage
        from ZODB.DB import DB
        f = FileStorage(filename)
        self.db = DB(f)
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

