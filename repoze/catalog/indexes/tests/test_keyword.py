import unittest

_marker = object()

class TestCatalogKeywordIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.keyword import CatalogKeywordIndex
        return CatalogKeywordIndex

    def _makeOne(self, discriminator=_marker):
        def _discriminator(obj, default):
            if obj is _marker:
                return default
            return obj
        if discriminator is _marker:
            discriminator = _discriminator
        return self._getTargetClass()(discriminator)

    def test_class_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyClass
        from repoze.catalog.interfaces import ICatalogIndex
        verifyClass(ICatalogIndex, self._getTargetClass())

    def test_instance_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyObject
        from repoze.catalog.interfaces import ICatalogIndex
        verifyObject(ICatalogIndex, self._makeOne())

    def test_ctor_callback_discriminator(self):
        def _discriminator(obj, default):
            """ """
        index = self._makeOne(_discriminator)
        self.failUnless(index.discriminator is _discriminator)

    def test_ctor_string_discriminator(self):
        index = self._makeOne('abc')
        self.assertEqual(index.discriminator, 'abc')

    def test_ctor_bad_discriminator(self):
        self.assertRaises(ValueError, self._makeOne, object())

    def test_reindex_doc_doesnt_unindex(self):
        index = self._makeOne()
        index.index_doc(5, [1])
        index.unindex_doc = lambda *args, **kw: 1/0
        index.reindex_doc(5, [1])

    def test_reindex_doc_same_values(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        self.assertEqual(index.documentCount(), 1)
        index.reindex_doc(1, [1,2,3])
        self.assertEqual(index.documentCount(), 1)
        self.failUnless(1 in index._rev_index)
        self.failUnless(1 in index._fwd_index[1])
        self.failUnless(1 in index._fwd_index[2])
        self.failUnless(1 in index._fwd_index[3])
        self.failIf(4 in index._fwd_index)

    def test_reindex_doc_different_values(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        self.assertEqual(index.documentCount(), 1)
        index.reindex_doc(1, [2,3,4])
        self.assertEqual(index.documentCount(), 1)
        self.failUnless(1 in index._rev_index)
        self.failIf(1 in index._fwd_index.get(1, []))
        self.failUnless(1 in index._fwd_index[2])
        self.failUnless(1 in index._fwd_index[3])
        self.failUnless(1 in index._fwd_index[4])

    def test_apply_doesnt_mutate_query(self):
        # Some previous version of zope.index munged the query dict
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        query = {'operator':'or', 'query':[5]}
        result = index.apply(FrozenDict(query))
        self.assertEqual(list(result), [2,3])
        self.assertEqual(query, {'operator':'or', 'query':[5]})

    def test_applyAny(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        result = index.applyAny([5, 9])
        self.assertEqual(list(result), [2,3, 4, 5])

    def test_applyNotAny(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        result = index.applyNotAny([5, 9])
        self.assertEqual(list(result), [1])

    def test_applyAll(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        result = index.applyAll([5, 9])
        self.assertEqual(list(result), [])

    def test_applyNotAll(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        result = index.applyNotAll([5, 9])
        self.assertEqual(list(result), [1, 2, 3, 4, 5])

    def test_applyEq(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        result = index.applyEq([5, 9])
        self.assertEqual(list(result), [])

    def test_applyNotEq(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        result = index.applyNotEq([5])
        self.assertEqual(list(result), [1,4,5])

    def test_applyNotEq_with_unindexed_docs(self):
        def discriminator(obj, default):
            if isinstance(obj, list):
                return obj
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        index.index_doc(6, (5, 6))
        result = index.applyNotEq([5])
        self.assertEqual(list(result), [1,4,5,6])

    def test_applyNotEq_nothing_indexed(self):
        def discriminator(obj, default):
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        index.index_doc(6, (5,6))
        result = index.applyNotEq([5])
        self.assertEqual(list(result), [1,2,3,4,5,6])

    def test_docids(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9])
        index.index_doc(5, [9,10])
        index.index_doc(6, (5,6))
        self.assertEqual(set(index.docids()),
                         set((1, 2, 3, 4, 5, 6)))

    def test_unindex_doc_removes_from_docids(self):
        index = self._makeOne()
        index.index_doc(20, [1, 2, 3])
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_index_doc_then_missing_value(self):
        index = self._makeOne()
        index.index_doc(20, [1, 2, 3])
        self.assertEqual(set([20]), set(index.applyEq([2])))
        self.failUnless(20 in index.docids())
        index.index_doc(20, _marker)
        self.assertEqual(set(), set(index.applyEq([2])))
        self.failUnless(20 in index.docids())

    def test_index_doc_missing_value_then_with_value(self):
        index = self._makeOne()
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq([4])))
        self.failUnless(3 in index.docids())
        index.index_doc(3, [3, 4, 5])
        self.assertEqual(set([3]), set(index.applyEq([4])))
        self.failUnless(3 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        index = self._makeOne()
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq([4])))
        self.failUnless(3 in index.docids())
        index.unindex_doc(3)
        self.assertEqual(set(), set(index.applyEq([4])))
        self.failIf(3 in index.docids())

    def test_docids_with_indexed_and_not_indexed(self):
        index = self._makeOne()
        index.index_doc(1, [1])
        index.index_doc(2, _marker)
        self.assertEqual(set([1, 2]), set(index.docids()))


class FrozenDict(dict):
    def _forbidden(self, *args, **kw):
        assert 0 # pragma: no cover
    __setitem__ = __delitem__ = clear = update = _forbidden
