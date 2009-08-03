import unittest

_marker = object()

class TestCatalogTextIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.text import CatalogTextIndex
        return CatalogTextIndex

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

    def test_class_conforms_to_IIndexSort(self):
        from zope.interface.verify import verifyClass
        from zope.index.interfaces import IIndexSort
        verifyClass(IIndexSort, self._getTargetClass())

    def test_instance_conforms_to_IIndexSort(self):
        from zope.interface.verify import verifyObject
        from zope.index.interfaces import IIndexSort
        verifyObject(IIndexSort, self._makeOne())

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
        index.index_doc(5, 'now is the time')
        index.unindex_doc = lambda *args, **kw: 1/0
        index.reindex_doc(5, 'now is the time')

    def test_sort_no_results(self):
        index = self._makeOne()
        self.assertEqual([], index.sort([]))

    def test_sort_without_weights(self):
        index = self._makeOne()
        self.assertRaises(TypeError, index.sort, [1])

    def test_sort_unlimited_forward(self):
        index = self._makeOne()
        results = {-2: 5.0, 3: 3.0, 0: 4.5}
        expect = [-2, 0, 3]
        self.assertEqual(index.sort(results), expect)

    def test_sort_unlimited_reverse(self):
        index = self._makeOne()
        results = {-2: 5.0, 3: 3.0, 0: 4.5}
        expect = [3, 0, -2]
        self.assertEqual(index.sort(results, reverse=True), expect)

    def test_sort_limited(self):
        index = self._makeOne()
        results = {-2: 5.0, 3: 3.0, 0: 4.5}
        expect = [-2, 0]
        self.assertEqual(index.sort(results, limit=2), expect)
