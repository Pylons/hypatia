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
            return default
        index = Test(callback, 'a', a=1)
        self.assertEqual(index.discriminator, callback)
        self.assertEqual(index.arg, ('a',))
        self.assertEqual(index.kw, {'a':1})

    def test_ctor_string(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc', 'a', a=1)
        self.assertEqual(index.discriminator, 'abc')
        self.assertEqual(index.arg, ('a',))
        self.assertEqual(index.kw, {'a':1})

    def test_ctor_bad_discrim(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        self.assertRaises(ValueError, Test, None, 'a', a=1)

    def test_index_doc_callback_returns_nondefault(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        def callback(ob, default):
            return ob
        index = Test(callback)
        self.assertEqual(index.index_doc(1, 'abc'), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(index.docid, 1)

    def test_index_doc_string_discrim(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        class Dummy:
            abc = 'abc'
        dummy = Dummy()
        self.assertEqual(index.index_doc(1, dummy), 'abc')
        self.assertEqual(index.value, 'abc')
        self.assertEqual(index.docid, 1)

    def test_reindex_doc(self):
        klass = self._getTargetClass()
        class Test(klass, DummyIndex):
            pass
        index = Test('abc')
        class Dummy:
            abc = 'abc'
        dummy = Dummy()
        index.reindex_doc(1, dummy)
        self.assertEqual(index.unindexed, 1)
        self.assertEqual(index.value, 'abc')
        self.assertEqual(index.docid, 1)

from repoze.catalog.interfaces import ICatalogIndex
from zope.interface import implements

class DummyIndex(object):
    implements(ICatalogIndex)

    value = None
    docid = None

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

    def apply(self, query):
        return self.arg[0]

    def sort(self, results, reverse=False, limit=None):
        self.limited = True
        if reverse:
            return ['sorted3', 'sorted2', 'sorted1']
        return ['sorted1', 'sorted2', 'sorted3']
