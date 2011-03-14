import unittest

FACETS = [
    'price',
    'price:0-100',
    'price:100-500',
    'price:100-*',
    'color',
    'color:blue',
    'color:red',
    'size',
    'size:small',
    'size:medium',
    'size:large',
    'style',
    'style:gucci',
    'style:gucci:handbag',
    'style:gucci:dress',
    ]

_marker = object()

class TestCatalogFacetIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.facet import CatalogFacetIndex
        return CatalogFacetIndex

    def _makeOne(self, discriminator=None, facets=FACETS, family=_marker):
        def _discriminator(obj, default):
            return obj
        if discriminator is None:
            discriminator = _discriminator
        if family is _marker:
            return self._getTargetClass()(discriminator, facets)
        return self._getTargetClass()(discriminator, facets, family)

    def _populateIndex(self, idx):
        idx.index_doc(1, ['price:0-100', 'color:blue', 'style:gucci:handbag'])
        idx.index_doc(2, ['price:0-100', 'color:blue', 'style:gucci:dress'])
        idx.index_doc(3, ['price:0-100', 'color:red', 'color:blue',
                          'style:gucci'])
        idx.index_doc(4, ['size:large'])

    def test_class_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyClass
        from repoze.catalog.interfaces import ICatalogIndex
        verifyClass(ICatalogIndex, self._getTargetClass())

    def test_instance_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyObject
        from repoze.catalog.interfaces import ICatalogIndex
        verifyObject(ICatalogIndex, self._makeOne())

    def test_ctor_defaults(self):
        from BTrees import family32
        index = self._makeOne()
        self.failUnless(index.discriminator(self, index) is self)
        self.assertEqual(list(index.facets), sorted(FACETS))
        self.failUnless(index.family is family32)

    def test_ctor_explicit(self):
        from BTrees import family64
        OTHER_FACETS = ['foo', 'foo:bar']
        def _discriminator(obj, default):
            return default
        index = self._makeOne(_discriminator, OTHER_FACETS, family64)
        self.failUnless(index.discriminator(self, index) is index)
        self.assertEqual(list(index.facets), OTHER_FACETS)
        self.failUnless(index.family is family64)

    def test_ctor_string_discriminator(self):
        from BTrees import family64
        OTHER_FACETS = ['foo', 'foo:bar']
        index = self._makeOne('facets')
        self.assertEqual(index.discriminator, 'facets')

    def test_ctor_bad_discriminator(self):
        self.assertRaises(ValueError, self._makeOne, object())

    def test_index_doc_callback_discriminator(self):
        OTHER_FACETS = ['foo', 'foo:bar', 'foo:baz']
        def _discrimintator(obj, default):
            return ['foo:bar']
        index = self._makeOne(_discrimintator, OTHER_FACETS)
        index.index_doc(1, object())
        self.assertEqual(list(index._fwd_index['foo']), [1])
        self.assertEqual(list(index._fwd_index['foo:bar']), [1])
        self.assertEqual(list(index._rev_index[1]), ['foo', 'foo:bar'])

    def test_index_doc_string_discriminator(self):
        OTHER_FACETS = ['foo', 'foo:bar', 'foo:baz']
        class Dummy:
            facets = ['foo:bar']
        index = self._makeOne('facets', OTHER_FACETS)
        index.index_doc(1, Dummy())
        self.assertEqual(list(index._fwd_index['foo']), [1])
        self.assertEqual(list(index._fwd_index['foo:bar']), [1])
        self.assertEqual(list(index._rev_index[1]), ['foo', 'foo:bar'])

    def test_index_doc_missing_value_unindexes(self):
        OTHER_FACETS = ['foo', 'foo:bar', 'foo:baz']
        class Dummy:
            pass
        dummy = Dummy()
        dummy.facets = ['foo:bar']
        index = self._makeOne('facets', OTHER_FACETS)
        index.index_doc(1, dummy)
        del dummy.facets
        index.index_doc(1, dummy)
        self.failIf('foo' in index._fwd_index)
        self.failIf('foo:bar' in index._fwd_index)
        self.failIf(1 in index._rev_index)

    def test_index_doc_persistent_value_raises(self):
        from persistent import Persistent
        OTHER_FACETS = ['foo', 'foo:bar', 'foo:baz']
        class Dummy:
            pass
        index = self._makeOne('facets', OTHER_FACETS)
        dummy = Dummy()
        dummy.facets = Persistent()
        self.assertRaises(ValueError, index.index_doc, 1, dummy)

    def test_index_doc_unindexes_old_values(self):
        OTHER_FACETS = ['foo', 'foo:bar', 'foo:baz']
        class Dummy:
            pass
        dummy = Dummy()
        dummy.facets = ['foo:bar']
        index = self._makeOne('facets', OTHER_FACETS)
        index.index_doc(1, dummy)
        dummy.facets = ['foo:baz']
        index.index_doc(1, dummy)
        self.assertEqual(list(index._fwd_index['foo']), [1])
        self.assertEqual(list(index._fwd_index['foo:baz']), [1])
        self.assertEqual(list(index._rev_index[1]), ['foo', 'foo:baz'])
        self.failIf('foo:bar' in index._fwd_index)

    def test_search(self):
        index = self._makeOne()
        self._populateIndex(index)

        result = index.search(['color:blue', 'color:red'])
        self.assertEqual(sorted(list(result)), [3])
        result = index.search(['price'])
        self.assertEqual(sorted(list(result)), [1,2,3])
        result = index.search(['price:0-100'])
        self.assertEqual(sorted(list(result)), [1,2,3])
        result = index.search(['style:gucci'])
        self.assertEqual(sorted(list(result)), [1,2,3])
        result = index.search(['style:gucci:handbag'])
        self.assertEqual(sorted(list(result)), [1])
        result = index.search(['size'])
        self.assertEqual(sorted(list(result)), [4])
        result = index.search(['size:large'])
        self.assertEqual(sorted(list(result)), [4])
        result = index.search(['size:nonexistent'])
        self.assertEqual(sorted(list(result)), [])
        result = index.search(['nonexistent'])
        self.assertEqual(sorted(list(result)), [])

        index.unindex_doc(1)
        result = index.search(['price'])
        self.assertEqual(sorted(list(result)), [2,3])
        result = index.search(['price:0-100'])
        self.assertEqual(sorted(list(result)), [2,3])
        result = index.search(['style:gucci'])
        self.assertEqual(sorted(list(result)), [2,3])
        result = index.search(['style:gucci:handbag'])
        self.assertEqual(sorted(list(result)), [])

        index.unindex_doc(2)
        result = index.search(['price'])
        self.assertEqual(sorted(list(result)), [3])
        result = index.search(['price:0-100'])
        self.assertEqual(sorted(list(result)), [3])
        result = index.search(['style:gucci'])
        self.assertEqual(sorted(list(result)), [3])

        index.unindex_doc(4)
        result = index.search(['size'])
        self.assertEqual(sorted(list(result)), [])
        result = index.search(['size:large'])
        self.assertEqual(sorted(list(result)), [])
        result = index.search(['size:nonexistent'])
        self.assertEqual(sorted(list(result)), [])
        result = index.search(['nonexistent'])
        self.assertEqual(sorted(list(result)), [])

    def test_counts(self):
        index = self._makeOne()
        self._populateIndex(index)

        search = ['price:0-100']
        result = index.search(search)
        self.assertEqual(sorted(list(result)), [1,2,3])
        counts = index.counts(result, search)
        self.assertEqual(counts['style'], 3)
        self.assertEqual(counts['style:gucci'], 3)
        self.assertEqual(counts['style:gucci:handbag'], 1)
        self.assertEqual(counts['style:gucci:dress'], 1)
        self.assertEqual(counts['color'], 3)
        self.assertEqual(counts['color:blue'], 3)
        self.assertEqual(counts['color:red'], 1)
        self.assertEqual(len(counts), 7)

        search = ['price:0-100', 'color:red']
        result = index.search(search)
        self.assertEqual(sorted(list(result)), [3])
        counts = index.counts(result, search)
        self.assertEqual(counts['style'], 1)
        self.assertEqual(counts['style:gucci'], 1)
        self.assertEqual(counts['color:blue'], 1)
        self.assertEqual(len(counts), 3)

        search = ['size:large']
        result = index.search(search)
        self.assertEqual(sorted(list(result)), [4])
        counts = index.counts(result, search)
        self.assertEqual(counts, {})

        search = ['size']
        result = index.search(search)
        self.assertEqual(sorted(list(result)), [4])
        counts = index.counts(result, search)
        self.assertEqual(counts, {'size:large':1})

    def test__indexed(self):
        index = self._makeOne()
        self._populateIndex(index)
        self.assertEqual(set(index._indexed()), set((1, 2, 3, 4)))

    def test_index_doc_missing_value_adds_to__not_indexed(self):
        def discriminator(obj, default):
            return default
        index = self._makeOne(discriminator)
        self.assertEqual(index.index_doc(20, 3), None)
        self.failUnless(20 in index._not_indexed)

    def test_index_doc_with_value_removes_from__not_indexed(self):
        index = self._makeOne()
        index._not_indexed.add(20)
        self.assertEqual(index.index_doc(20, 'foo'), 'foo')
        self.failIf(20 in index._not_indexed)

