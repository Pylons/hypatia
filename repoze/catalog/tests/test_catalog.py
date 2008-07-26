import unittest

class TestCatalogIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.catalog import CatalogIndex
        return CatalogIndex

    def test_ctor(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        def callback(object, default):
            return default
        index = Test(callback, 'a', a=1)
        self.assertEqual(index.discriminator, callback)
        self.assertEqual(index.arg, ('a',))
        self.assertEqual(index.kw, {'a':1})

    def test_index_doc_callback_returns_nondefault(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        def callback(ob, default):
            return ob
        index = Test(callback)
        self.assertEqual(index.index_doc(1, 'abc'), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(index.docid, 1)

class TestCatalog(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.catalog import Catalog
        return Catalog

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()
    
    def test_klass_provides_ICatalog(self):
        klass = self._getTargetClass()
        from zope.interface.verify import verifyClass
        from repoze.catalog.catalog import ICatalog
        verifyClass(ICatalog, klass)
        
    def test_inst_provides_ICatalog(self):
        klass = self._getTargetClass()
        from zope.interface.verify import verifyObject
        from repoze.catalog.catalog import ICatalog
        inst = self._makeOne()
        verifyObject(ICatalog, inst)

    def test_clear(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.clear()
        self.assertEqual(idx.cleared, True)

    def test_index_doc(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.index_doc(1, 'value')
        self.assertEqual(idx.docid, 1)
        self.assertEqual(idx.value, 'value')

    def test_index_doc_nonint_docid(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        self.assertRaises(ValueError, catalog.index_doc, 'abc', 'value')

    def test_unindex_doc(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.unindex_doc(1)
        self.assertEqual(idx.unindexed, 1)

    def test_setitem_guard(self):
        catalog = self._makeOne()
        self.assertRaises(ValueError, catalog.__setitem__, 'a', None)

    def test_updateIndex(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.updateIndex('name', [(1, 1)])
        self.assertEqual(idx.docid, 1)
        self.assertEqual(idx.value, 1)

    def test_updateIndexes(self):
        catalog = self._makeOne()
        idx1 = DummyIndex()
        catalog['name1'] = idx1
        idx2 = DummyIndex()
        catalog['name2'] = idx2
        catalog.updateIndexes([(1, 1)])
        self.assertEqual(idx1.docid, 1)
        self.assertEqual(idx1.value, 1)
        self.assertEqual(idx2.docid, 1)
        self.assertEqual(idx2.value, 1)

    def test_searchResults(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        result = catalog.searchResults(name1={}, name2={})
        self.assertEqual(list(result), [3])

    def test_apply(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        result = catalog.apply({'name1':{}, 'name2':{}})
        self.assertEqual(list(result), [3])

class TestFileStorageCatalogFactory(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.catalog import FileStorageCatalogFactory
        return FileStorageCatalogFactory

    def _makeOne(self, filename, appname):
        klass = self._getTargetClass()
        return klass(filename, appname)

    def setUp(self):
        import tempfile
        self.tempfile = tempfile.mktemp()

    def tearDown(self):
        import os
        os.remove(self.tempfile)

    def test_no_conn_handler(self):
        factory = self._makeOne(self.tempfile, 'catalog')
        from repoze.catalog.catalog import Catalog
        catalog = factory()
        self.failUnless(isinstance(catalog, Catalog))
        factory.db.close()

    def test_with_conn_handler(self):
        factory = self._makeOne(self.tempfile, 'catalog')
        from repoze.catalog.catalog import Catalog
        e = {}
        def handle(conn):
            e['conn'] = conn
        catalog = factory(handle)
        self.failUnless(isinstance(catalog, Catalog))
        self.assertEqual(e['conn']._db, factory.db)
        factory.db.close()

class TestConnectioManager(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.catalog import ConnectionManager
        return ConnectionManager

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_call(self):
        conn = DummyConnection()
        manager = self._makeOne()
        manager(conn)
        self.assertEqual(manager.conn, conn)
        
    def test_close(self):
        conn = DummyConnection()
        manager = self._makeOne()
        manager(conn)
        manager.close()
        self.assertEqual(conn.closed, True)

    def test_del(self):
        conn = DummyConnection()
        manager = self._makeOne()
        manager(conn)
        del manager
        self.assertEqual(conn.closed, True)

    def test_commit(self):
        conn = DummyConnection()
        txn = DummyTransaction()
        manager = self._makeOne()
        manager(conn)
        manager.commit(txn)
        self.assertEqual(txn.committed, True)

class DummyConnection:
    def close(self):
        self.closed = True

class DummyTransaction:
    def commit(self):
        self.committed = True

from repoze.catalog.catalog import ICatalogIndex
from zope.interface import implements

class DummyIndex(object):
    implements(ICatalogIndex)

    value = None
    docid = None

    def __init__(self, *arg, **kw):
        self.arg = arg
        self.kw = kw

    def index_doc(self, docid, value):
        self.docid = docid
        self.value = value
        return value

    def unindex_doc(self, docid):
        self.unindexed = docid

    def clear(self):
        self.cleared = True

    def apply(self, query):
        return self.arg[0]
        

