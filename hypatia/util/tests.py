import unittest

from . import RichComparisonMixin

_marker = object()

class TestBaseIndexMixin(unittest.TestCase):
    def _getTargetClass(self):
        from . import BaseIndexMixin
        return BaseIndexMixin

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

    def test_indexed_count(self):
        inst = self._makeIndex('abc')
        def indexed(): return [1,2,3]
        inst.indexed = indexed
        self.assertEqual(inst.indexed_count(), 3)

    def test_not_indexed_count(self):
        inst = self._makeIndex('abc')
        def not_indexed(): return [1,2,3]
        inst.not_indexed = not_indexed
        self.assertEqual(inst.not_indexed_count(), 3)

    def test_docids_count(self):
        inst = self._makeIndex('abc')
        def docids(): return [1,2,3]
        inst.docids = docids
        self.assertEqual(inst.docids_count(), 3)

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

    def test_qname_with___name__(self):
        index = self._makeIndex('abc')
        index.__name__ = 'fred'
        self.assertEqual(index.qname(), 'fred')

    def test_qname_without___name__(self):
        index = self._makeIndex('abc')
        self.assertEqual(index.qname(), str(index))

class DummyIndex(object):

    value = None

    def index_doc(self, docid, value):
        value = self.discriminate(value, _marker)
        if value is _marker:
            # unindex the previous value
            self.unindex_doc(docid)
            # Store docid in set of unindexed docids
            self._not_indexed.add(docid)
            return None
        if docid in self._not_indexed:
            # Remove from set of unindexed docs if it was in there.
            self._not_indexed.remove(docid)
        self._docids.add(docid)
        self.value = value
        return value

    def unindex_doc(self, docid):
        _not_indexed = self._not_indexed
        if docid in _not_indexed:
            _not_indexed.remove(docid)
        if docid in self._docids:
            self._docids.remove(docid)
            self.unindexed = docid

    def indexed(self):
        return self._docids

    def not_indexed(self):
        return self._not_indexed

class RichComparisonMixinTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.comp = RichComparer(6)

    def testDefaultComparison(self):
        self.assertRaises(NotImplementedError,
                          lambda: RichComparisonMixin() == 3)
        self.assertRaises(NotImplementedError,
                          lambda: RichComparisonMixin() != 3)
        self.assertRaises(NotImplementedError,
                          lambda: RichComparisonMixin() < 3)
        self.assertRaises(NotImplementedError,
                          lambda: RichComparisonMixin() > 3)
        self.assertRaises(NotImplementedError,
                          lambda: RichComparisonMixin() <= 3)
        self.assertRaises(NotImplementedError,
                          lambda: RichComparisonMixin() >= 3)


    def testEquality(self):
        self.assertTrue(self.comp == 6)
        self.assertTrue(self.comp == RichComparer(6))

        self.assertFalse(self.comp == 7)
        self.assertFalse(self.comp == RichComparer(7))

    def testInEquality(self):
        self.assertFalse(self.comp != 6)
        self.assertFalse(self.comp != RichComparer(6))

        self.assertTrue(self.comp != 7)
        self.assertTrue(self.comp != RichComparer(7))

    def testLessThan(self):
        self.assertTrue(self.comp < 7)
        self.assertTrue(self.comp < RichComparer(7))

        self.assertFalse(self.comp < 5)
        self.assertFalse(self.comp < RichComparer(5))

        self.assertFalse(self.comp < 6)
        self.assertFalse(self.comp < RichComparer(6))

    def testGreaterThan(self):
        self.assertTrue(self.comp > 5)
        self.assertTrue(self.comp > RichComparer(5))

        self.assertFalse(self.comp > 7)
        self.assertFalse(self.comp > RichComparer(7))

        self.assertFalse(self.comp > 6)
        self.assertFalse(self.comp > RichComparer(6))

    def testLessThanEqual(self):
        self.assertTrue(self.comp <= 7)
        self.assertTrue(self.comp <= RichComparer(7))
        self.assertTrue(self.comp <= 6)
        self.assertTrue(self.comp <= RichComparer(6))

        self.assertFalse(self.comp <= 5)
        self.assertFalse(self.comp <= RichComparer(5))

    def testGreaterThanEqual(self):
        self.assertTrue(self.comp >= 5)
        self.assertTrue(self.comp >= RichComparer(5))
        self.assertTrue(self.comp >= 6)
        self.assertTrue(self.comp >= RichComparer(6))

        self.assertFalse(self.comp >= 7)
        self.assertFalse(self.comp >= RichComparer(7))
        

class RichComparer(RichComparisonMixin):

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if not hasattr(other, 'value'):
            return self.value == other
        return self.value == other.value

    def __lt__(self, other):
        if not hasattr(other, 'value'):
            return self.value < other
        return self.value < other.value


