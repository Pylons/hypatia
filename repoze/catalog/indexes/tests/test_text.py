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

    def test_applyDoesNotContain(self):
        index = self._makeOne()
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        result = sorted(index.applyDoesNotContain('time'))
        self.assertEqual(result, [2])

    def test_applyDoesNotContain_with_unindexed_doc(self):
        def discriminator(obj, default):
            if isinstance(obj, basestring):
                return obj
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        index.index_doc(3, 3)
        result = sorted(index.applyDoesNotContain('time'))
        self.assertEqual(result, [2, 3])

    def test_applyDoesNotContain_nothing_indexed(self):
        def discriminator(obj, default):
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        index.index_doc(3, 3)
        result = sorted(index.applyDoesNotContain('time'))
        self.assertEqual(result, [1, 2, 3])

    def test_get_indexed_docids(self):
        index = self._makeOne()
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        index.index_doc(3, u"you have nice hair.")
        self.assertEqual(set(index.get_indexed_docids()), set((1, 2, 3)))
