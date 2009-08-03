import unittest

_marker = object()

class TestCatalogKeywordIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.keyword import CatalogKeywordIndex
        return CatalogKeywordIndex

    def _makeOne(self, discriminator=_marker):
        def _discriminator(obj, default):
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
            return obj
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
        

class FrozenDict(dict):
    def _forbidden(self, *args, **kw):
        assert 0
    __setitem__ = __delitem__ = clear = update = _forbidden
