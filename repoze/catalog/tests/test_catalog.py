import unittest

_marker = object()

class TestCatalog(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.catalog import Catalog
        return Catalog

    def _makeOne(self, family=_marker):
        klass = self._getTargetClass()
        if family is _marker:
            return klass()
        return klass(family)
    
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

    def test_ctor_defaults(self):
        from BTrees import family32
        catalog = self._makeOne()
        self.failUnless(catalog.family is family32)

    def test_ctor_explicit_family(self):
        from BTrees import family64
        catalog = self._makeOne(family64)
        self.failUnless(catalog.family is family64)

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

    def test_reindex_doc(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.reindex_doc(1, 'value')
        self.assertEqual(idx.reindexed_docid, 1)
        self.assertEqual(idx.reindexed_ob, 'value')

    def test_unindex_doc(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.unindex_doc(1)
        self.assertEqual(idx.unindexed, 1)

    def test_setitem_guard(self):
        catalog = self._makeOne()
        self.assertRaises(ValueError, catalog.__setitem__, 'a', None)

    def test_search(self):
        from BTrees.IFBTree import IFSet
        catalog = self._makeOne()
        c1 = IFSet([1, 2, 3])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.search(name1={}, name2={})
        self.assertEqual(numdocs, 1)
        self.assertEqual(list(result), [3])

    def test_search_index_returns_empty(self):
        from BTrees.IFBTree import IFSet
        catalog = self._makeOne()
        c1 = IFSet([])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.search(name1={}, name2={})
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_no_intersection(self):
        from BTrees.IFBTree import IFSet
        catalog = self._makeOne()
        c1 = IFSet([1, 2])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.search(name1={}, name2={})
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_index_query_order_returns_empty(self):
        from BTrees.IFBTree import IFSet
        catalog = self._makeOne()
        c1 = IFSet([1, 2])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.search(name1={}, name2={},
                                         index_query_order=['name2', 'name1'])
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_no_indexes_in_search(self):
        catalog = self._makeOne()
        numdocs, result = catalog.search()
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_noindex(self):
        catalog = self._makeOne()
        self.assertRaises(ValueError, catalog.search, name1={})

    def test_search_noindex_ordered(self):
        catalog = self._makeOne()
        self.assertRaises(ValueError, catalog.search, name1={},
                          index_query_order=['name1'])

    def test_apply(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.apply({'name1':{}, 'name2':{}})
        self.assertEqual(numdocs, 1)
        self.assertEqual(list(result), [3])

    def test_search_with_sortindex_ascending(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.search(
            name1={}, name2={}, sort_index='name1')
        self.assertEqual(numdocs, 3)
        self.assertEqual(list(result), ['sorted1', 'sorted2', 'sorted3'])

    def test_search_with_sortindex_reverse(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result = catalog.search(
            name1={}, name2={}, sort_index='name1',
            reverse=True)
        self.assertEqual(numdocs, 3)
        self.assertEqual(list(result), ['sorted3', 'sorted2', 'sorted1'])

    def test_search_with_sort_type(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        from repoze.catalog.indexes.field import FWSCAN
        numdocs, result = catalog.search(name1={}, sort_index='name1',
                                         limit=1, sort_type=FWSCAN)
        self.assertEqual(idx1.sort_type, FWSCAN)

    def test_limited(self):
        catalog = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        numdocs, result = catalog.search(name1={}, sort_index='name1', limit=1)
        self.assertEqual(numdocs, 1)
        self.assertEqual(idx1.limit, 1)

    def _test_functional_merge(self, **extra):
        catalog = self._makeOne()
        from repoze.catalog.indexes.field import CatalogFieldIndex
        from repoze.catalog.indexes.keyword import CatalogKeywordIndex
        from repoze.catalog.indexes.text import CatalogTextIndex
        from repoze.catalog.indexes.path2 import CatalogPathIndex2
        class Content(object):
            def __init__(self, field, keyword, text, path):
                self.field = field
                self.keyword = keyword
                self.text = text
                self.path = path
        field = CatalogFieldIndex('field')
        keyword = CatalogKeywordIndex('keyword')
        text = CatalogTextIndex('text')
        path = CatalogPathIndex2('path')
        catalog['field'] = field
        catalog['keyword'] = keyword
        catalog['text'] = text
        catalog['path'] = path
        map = {
            1:Content('field1', ['keyword1', 'same'], 'text one', '/path1'),
            2:Content('field2', ['keyword2', 'same'], 'text two',
                      '/path1/path2'),
            3:Content('field3', ['keyword3', 'same'], 'text three',
                      '/path1/path2/path3'),
            }
        for num, doc in map.items():
            catalog.index_doc(num, doc)
        num, result = catalog.search(field=('field1', 'field1'), **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [1])
        num, result = catalog.search(field=('field2', 'field2'), **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result = catalog.search(field=('field2', 'field2'),
                                     keyword='keyword2', **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result = catalog.search(field=('field2', 'field2'), text='two',
                                     **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result = catalog.search(text='text', keyword='same', **extra)
        self.assertEqual(num, 3)
        self.assertEqual(list(result), [1,2,3])

        num, result = catalog.search(text='text', path='/path1', **extra)
        self.assertEqual(num, 2)
        self.assertEqual(list(result), [2,3])

    def test_functional_index_merge_unordered(self):
        return self._test_functional_merge()

    def test_functional_index_merge_ordered(self):
        return self._test_functional_merge(
            index_query_order=['field', 'keyword', 'text', 'path'])

class TestFileStorageCatalogFactory(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.catalog import FileStorageCatalogFactory
        return FileStorageCatalogFactory

    def _makeOne(self, filename, appname, **kw):
        klass = self._getTargetClass()
        return klass(filename, appname, **kw)

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

    def test_with_cache_size(self):
        factory = self._makeOne(self.tempfile, 'catalog', cache_size=1000)
        from repoze.catalog.catalog import Catalog
        catalog = factory()
        self.failUnless(isinstance(catalog, Catalog))
        self.assertEqual(factory.db._cache_size, 1000)
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

class TestConnectionManager(unittest.TestCase):
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
    limit = None
    sort_type = None

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

    def reindex_doc(self, docid, object):
        self.reindexed_docid = docid
        self.reindexed_ob = object

    def apply(self, query):
        return self.arg[0]

    def apply_intersect(self, query, docids): # pragma: no cover
        if docids is None:
            return self.arg[0]
        L = []
        for docid in self.arg[0]:
            if docid in docids:
                L.append(docid)
        return L

    def sort(self, results, reverse=False, limit=None, sort_type=None):
        self.limit = limit
        self.sort_type = sort_type
        if reverse:
            return ['sorted3', 'sorted2', 'sorted1']
        return ['sorted1', 'sorted2', 'sorted3']
