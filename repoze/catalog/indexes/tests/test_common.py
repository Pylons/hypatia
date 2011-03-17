import unittest

class TestCatalogIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.common import CatalogIndex
        return CatalogIndex

    def test_ctor(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        def callback(object, default):
            """ """
        index = Test(callback)
        index._docids = set()
        self.assertEqual(index.discriminator, callback)

    def test_ctor_callback(self):
        klass = self._getTargetClass()
        def _discriminator(obj, default):
            """ """
        class Test(klass, DummyIndex):
            pass
        index = Test(_discriminator)
        index._docids = set()
        self.failUnless(index.discriminator is _discriminator)

    def test_ctor_string(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        self.assertEqual(index.discriminator, 'abc')

    def test_ctor_bad_discrim(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        self.assertRaises(ValueError, Test, None)

    def test_not_implemented_applies_methods(self):
        index = self._getTargetClass()('foo')
        for name in [
            'applyContains',
            'applyDoesNotContain',
            'applyEq',
            'applyNotEq',
            'applyGt',
            'applyLt',
            'applyGe',
            'applyLe',
            'applyAny',
            'applyNotAny',
            'applyAll',
            'applyNotAll',
            'applyInRange',
            'applyNotInRange']:
            self.assertRaises(NotImplementedError, getattr(index, name))

    def test_index_doc_callback_returns_nondefault(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        def callback(ob, default):
            return ob
        index = Test(callback)
        index._docids = set()
        self.assertEqual(index.index_doc(1, 'abc'), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(set(index.docids()), set([1]))

    def test_index_doc_string_discrim(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            abc = 'abc'
        dummy = Dummy()
        self.assertEqual(index.index_doc(1, dummy), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(set(index.docids()), set([1]))

    def test_index_doc_missing_value_unindexes(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = 'abc'
        self.assertEqual(index.index_doc(1, dummy), 'abc')
        del dummy.abc
        del index.value
        self.assertEqual(index.index_doc(1, dummy), None)
        self.assertEqual(set(index.docids()), set([1]))
        self.assertEqual(index.value, None)
        self.assertEqual(index.unindexed, 1)

    def test_index_doc_missing_value_then_with_value(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        self.assertEqual(index.index_doc(20, dummy), None)
        self.failUnless(20 in index.docids())
        dummy.abc = 'foo'
        self.assertEqual(index.index_doc(20, dummy), 'foo')
        self.failUnless(20 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        self.assertEqual(index.index_doc(20, dummy), None)
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_docids_with_indexed_and_not_indexed(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        self.assertEqual(index.index_doc(20, dummy), None)
        dummy.abc = 'foo'
        self.assertEqual(index.index_doc(21, dummy), 'foo')
        self.assertEqual(set(index.docids()), set([20, 21]))

    def test_index_doc_persistent_value_raises(self):
        from persistent import Persistent
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = Persistent()
        self.assertRaises(ValueError, index.index_doc, 1, dummy)

    def test_index_doc_broken_object_raises(self):
        from ZODB.broken import Broken
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = Broken()
        self.assertRaises(ValueError, index.index_doc, 1, dummy)

    def test_reindex_doc(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = set()
        class Dummy:
            abc = 'abc'
        dummy = Dummy()
        index.index_doc(1, dummy)
        index.reindex_doc(1, dummy)
        self.assertEqual(index.unindexed, 1)
        self.assertEqual(index.value, 'abc')
        self.assertEqual(set(index.docids()), set([1]))

    def test_migrate_to_0_8_0(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        index._docids = index.family.IF.Set([1, 2])
        self.assertEqual(set(index.docids()), set([1, 2]))
        all_docids = set([1, 2, 3, 4])
        index._migrate_to_0_8_0(all_docids)
        self.assertEqual(set(index.docids()), set([1, 2, 3, 4]))


from repoze.catalog.interfaces import ICatalogIndex
from zope.interface import implements


class DummyIndex(object):
    implements(ICatalogIndex)

    value = None

    def index_doc(self, docid, value):
        self._docids.add(docid)
        self.value = value
        return value

    def unindex_doc(self, docid):
        if docid in self._docids:
            self._docids.remove(docid)
            self.unindexed = docid

    def _indexed(self):
        return self._docids

