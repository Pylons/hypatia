import BTrees
from persistent.mapping import PersistentMapping
from persistent import Persistent
import transaction

from zope.interface import implements
from zope.interface import Interface
from zope.interface import Attribute

from zope.index.interfaces import IInjection
from zope.index.interfaces import IIndexSearch

from zope.index.text import TextIndex
from zope.index.field import FieldIndex
from zope.index.keyword import KeywordIndex

class ICatalog(IIndexSearch, IInjection):
    def searchResults(**query):
        """Search on the given indexes."""

    def updateIndexes(items):
        """Reindex all objects in the items sequence [(docid, obj),..] in all
        indexes."""

    def updateIndex(name, items):
        """Reindex all objects in the items sequence [(docid, obj),..] in
        the named index."""

class ICatalogIndex(IIndexSearch, IInjection):
    """ An index that adapts objects to an attribute or callable value
    on an object """
    interface = Attribute('The interface that object to be indexed will '
                          'be adapted against to provide its catalog value')

class ICatalogAdapter(Interface):
    def __call__(default):
        """ Return the value or the default if the object no longer
        has any value for the adaptation"""

_marker = ()

class CatalogIndex(object):
    """ Abstract class for interface-based lookup """

    def __init__(self, discriminator, *args, **kwargs):
        super(CatalogIndex, self).__init__(*args, **kwargs)
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator

    def index_doc(self, docid, object):
        if callable(self.discriminator):
            value = self.discriminator(object, _marker)
        else:
            value = getattr(object, self.discriminator, _marker)

        if value is _marker:
            # unindex the previous value
            super(CatalogIndex, self).unindex_doc(docid)
            return None

        if isinstance(value, Persistent):
            raise ValueError('Catalog cannot index persistent object %s' %
                             value)

        return super(CatalogIndex, self).index_doc(docid, value)

class CatalogTextIndex(CatalogIndex, TextIndex):
    implements(ICatalogIndex)

class CatalogFieldIndex(CatalogIndex, FieldIndex):
    implements(ICatalogIndex)

class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    implements(ICatalogIndex)

class Catalog(PersistentMapping):

    implements(ICatalog)

    family = BTrees.family32

    def __init__(self, family=None):
        PersistentMapping.__init__(self)
        if family is not None:
            self.family = family

    def clear(self):
        for index in self.values():
            index.clear()

    def index_doc(self, docid, obj):
        """Register the data in indexes of this catalog."""
        for index in self.values():
            assertint(docid)
            index.index_doc(docid, obj)

    def unindex_doc(self, docid):
        """Unregister the data from indexes of this catalog."""
        for index in self.values():
            assertint(docid)
            index.unindex_doc(docid)

    def __setitem__(self, name, index):
        if not ICatalogIndex.providedBy(index):
            raise ValueError('%s does not provide ICatalogIndex')
        index.__parent__ = self
        index.__name__ = name
        return PersistentMapping.__setitem__(self, name, index)
            
    def updateIndex(self, name, items):
        index = self[name]
        for docid, obj in items:
            assertint(docid)
            index.index_doc(docid, obj)

    def updateIndexes(self, items):
        for docid, obj in items:
            assertint(docid)
            for index in self.values():
                index.index_doc(docid, obj)

    def searchResults(self, **query):
        results = []
        for index_name, index_query in query.items():
            index = self.get(index_name)
            if index is None:
                raise ValueError('No such index %s' % index)
            r = index.apply(index_query)
            if r is None:
                continue
            if not r:
                # empty results
                return r
            results.append((len(r), r))

        if not results:
            # no applicable indexes, so catalog was not applicable
            return None

        results.sort() # order from smallest to largest

        _, result = results.pop(0)
        for _, r in results:
            _, result = self.family.IF.weightedIntersection(result, r)

        return result

    def apply(self, query):
        return self.searchResults(**query)

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

