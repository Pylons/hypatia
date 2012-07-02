import unittest

_marker = object()

class TestCatalog(unittest.TestCase):
    def _getTargetClass(self):
        from . import Catalog
        return Catalog

    def _makeOne(self, family=_marker):
        klass = self._getTargetClass()
        if family is _marker:
            return klass()
        return klass(family)
    
    def test_klass_provides_ICatalog(self):
        klass = self._getTargetClass()
        from zope.interface.verify import verifyClass
        from ..interfaces import ICatalog
        verifyClass(ICatalog, klass)
        
    def test_inst_provides_ICatalog(self):
        from zope.interface.verify import verifyObject
        from ..interfaces import ICatalog
        inst = self._makeOne()
        verifyObject(ICatalog, inst)

    def test_ctor_defaults(self):
        from BTrees import family64
        catalog = self._makeOne()
        self.failUnless(catalog.family is family64)

    def test_ctor_explicit_family(self):
        from BTrees import family32
        catalog = self._makeOne(family32)
        self.failUnless(catalog.family is family32)

    def test_reset(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.reset()
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

class TestCatalogQuery(unittest.TestCase):
    def _makeOne(self, catalog, family=None):
        from . import CatalogQuery
        return CatalogQuery(catalog, family=family)
    
    def _makeCatalog(self, family=None):
        from . import Catalog
        return Catalog(family=family)

    def test_with_alternate_family(self):
        from BTrees import family32
        search = self._makeOne(None, family=family32)
        self.assertEqual(search.family, family32)

    def test_search(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2, 3])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        q = self._makeOne(catalog)
        numdocs, result = q.search(name1={}, name2={})
        self.assertEqual(numdocs, 1)
        self.assertEqual(list(result), [3])

    def test_search_index_returns_empty(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        q = self._makeOne(catalog)
        numdocs, result = q.search(name1={}, name2={})
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_no_intersection(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        q = self._makeOne(catalog)
        numdocs, result = q.search(name1={}, name2={})
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_index_query_order_returns_empty(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        q = self._makeOne(catalog)
        numdocs, result = q.search(name1={}, name2={},
                                   index_query_order=['name2', 'name1'])
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_no_indexes_in_search(self):
        catalog = self._makeCatalog()
        q = self._makeOne(catalog)
        numdocs, result = q.search()
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_noindex(self):
        catalog = self._makeCatalog()
        q = self._makeOne(catalog)
        self.assertRaises(ValueError, q.search, name1={})

    def test_search_noindex_ordered(self):
        catalog = self._makeCatalog()
        q = self._makeOne(catalog)
        self.assertRaises(ValueError, q.search, name1={},
                          index_query_order=['name1'])

    def test_search_with_sortindex_ascending(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        q = self._makeOne(catalog)
        numdocs, result = q.search(
            name1={}, name2={}, sort_index='name1')
        self.assertEqual(numdocs, 3)
        self.assertEqual(list(result), ['sorted1', 'sorted2', 'sorted3'])

    def test_search_with_sortindex_reverse(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        q = self._makeOne(catalog)
        numdocs, result = q.search(
            name1={}, name2={}, sort_index='name1',
            reverse=True)
        self.assertEqual(numdocs, 3)
        self.assertEqual(list(result), ['sorted3', 'sorted2', 'sorted1'])

    def test_search_with_sort_type(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        from ..field import FWSCAN
        q = self._makeOne(catalog)
        numdocs, result = q.search(name1={}, sort_index='name1',
                                   limit=1, sort_type=FWSCAN)
        self.assertEqual(idx1.sort_type, FWSCAN)

    def test_limited(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        q = self._makeOne(catalog)
        numdocs, result = q.search(name1={}, sort_index='name1', limit=1)
        self.assertEqual(numdocs, 1)
        self.assertEqual(idx1.limit, 1)

    def test_sort(self):
        import BTrees
        IFSet = BTrees.family64.IF.Set
        catalog = self._makeCatalog()
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        q = self._makeOne(catalog)
        numdocs, result = q.sort(c1, sort_index='name1', limit=1)
        self.assertEqual(numdocs, 1)
        self.assertEqual(idx1.limit, 1)
        

    def _test_functional_merge(self, **extra):
        catalog = self._makeCatalog()
        from ..field import FieldIndex
        from ..keyword import KeywordIndex
        from ..text import TextIndex
        class Content(object):
            def __init__(self, field, keyword, text):
                self.field = field
                self.keyword = keyword
                self.text = text
        field = FieldIndex('field')
        keyword = KeywordIndex('keyword')
        text = TextIndex('text')
        catalog['field'] = field
        catalog['keyword'] = keyword
        catalog['text'] = text
        map = {
            1:Content('field1', ['keyword1', 'same'], 'text one'),
            2:Content('field2', ['keyword2', 'same'], 'text two'),
            3:Content('field3', ['keyword3', 'same'], 'text three'),
            }
        for num, doc in map.items():
            catalog.index_doc(num, doc)

        q = self._makeOne(catalog)
        
        num, result = q.search(field=('field1', 'field1'), **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [1])
        num, result = q.search(field=('field2', 'field2'), **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result = q.search(field=('field2', 'field2'),
                               keyword='keyword2', **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result = q.search(field=('field2', 'field2'), text='two',
                               **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result = q.search(text='text', keyword='same', **extra)
        self.assertEqual(num, 3)
        self.assertEqual(list(result), [1,2,3])

    def test_functional_index_merge_unordered(self):
        return self._test_functional_merge()

    def test_functional_index_merge_ordered(self):
        return self._test_functional_merge(
            index_query_order=['field', 'keyword', 'text'])

from ..interfaces import IIndex
from zope.interface import implementer

@implementer(IIndex)
class DummyIndex(object):

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

    def reset(self):
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
