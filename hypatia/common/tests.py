import unittest

class TestCatalogIndex(unittest.TestCase):
    def _getTargetClass(self):
        from . import CatalogIndex
        return CatalogIndex

    def _makeIndex(self, discriminator):
        import BTrees
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test()
        index.discriminator = discriminator
        index._docids = BTrees.family64.IF.Set()
        index._not_indexed = BTrees.family64.IF.TreeSet()
        index.family = BTrees.family64
        return index

    def test_not_implemented_applies_methods(self):
        index = self._getTargetClass()()
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
        def callback(ob, default):
            return ob
        index = self._makeIndex(callback)
        self.assertEqual(index.index_doc(1, 'abc'), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(set(index.docids()), set([1]))

    def test_index_doc_string_discrim(self):
        index = self._makeIndex('abc')
        class Dummy:
            abc = 'abc'
        dummy = Dummy()
        self.assertEqual(index.index_doc(1, dummy), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(set(index.docids()), set([1]))

    def test_index_doc_missing_value_unindexes(self):
        index = self._makeIndex('abc')
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
        index = self._makeIndex('abc')
        class Dummy:
            pass
        dummy = Dummy()
        self.assertEqual(index.index_doc(20, dummy), None)
        self.failUnless(20 in index.docids())
        dummy.abc = 'foo'
        self.assertEqual(index.index_doc(20, dummy), 'foo')
        self.failUnless(20 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        index = self._makeIndex('abc')
        class Dummy:
            pass
        dummy = Dummy()
        self.assertEqual(index.index_doc(20, dummy), None)
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_docids_with_indexed_and_not_indexed(self):
        index = self._makeIndex('abc')
        class Dummy:
            pass
        dummy = Dummy()
        self.assertEqual(index.index_doc(20, dummy), None)
        dummy.abc = 'foo'
        self.assertEqual(index.index_doc(21, dummy), 'foo')
        docids = index.docids()
        self.assertEqual(set(docids), set([20, 21]))

    def test_index_doc_persistent_value_raises(self):
        from persistent import Persistent
        index = self._makeIndex('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = Persistent()
        self.assertRaises(ValueError, index.index_doc, 1, dummy)

    def test_index_doc_broken_object_raises(self):
        from ZODB.broken import Broken
        index = self._makeIndex('abc')
        index._docids = set()
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = Broken()
        self.assertRaises(ValueError, index.index_doc, 1, dummy)

    def test_reindex_doc(self):
        index = self._makeIndex('abc')
        index._docids = set()
        class Dummy:
            abc = 'abc'
        dummy = Dummy()
        index.index_doc(1, dummy)
        index.reindex_doc(1, dummy)
        self.assertEqual(index.unindexed, 1)
        self.assertEqual(index.value, 'abc')
        self.assertEqual(set(index.docids()), set([1]))

from ..interfaces import ICatalogIndex
from zope.interface import implementer

@implementer(ICatalogIndex)
class DummyIndex(object):

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

