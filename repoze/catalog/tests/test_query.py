import unittest

class QueryTestBase(unittest.TestCase):
    def _makeOne(self, index_name, value):
        return self._getTargetClass()(index_name, value)

class TestQuery(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Query
        return Query

    def test_ctor(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(inst.index_name, 'index')
        self.assertEqual(inst.value, 'val')

class TestContains(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Contains
        return Contains

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.contains, 'val')

class TestEq(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Eq
        return Eq

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.eq, 'val')

class TestNotEq(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import NotEq
        return NotEq

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.not_eq, 'val')

class TestGt(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Gt
        return Gt

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.gt, 'val')

class TestGt(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Lt
        return Lt

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.lt, 'val')

class TestGe(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Ge
        return Ge

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.ge, 'val')

class TestLe(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Le
        return Le

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.le, 'val')

class TestAll(QueryTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import All
        return All

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.all, 'val')

class DummyCatalog(object):
    def __init__(self, index=None):
        if index is None:
            index = DummyIndex()
        self.index = index

    def __getitem__(self, name):
        return self.index

class DummyIndex(object):

    def applyContains(self, value):
        self.contains = value
        return value

    def applyEq(self, value):
        self.eq = value
        return value

    def applyNotEq(self, value):
        self.not_eq = value
        return value

    def applyGt(self, value):
        self.gt = value
        return value

    def applyLt(self, value):
        self.lt = value
        return value

    def applyGe(self, value):
        self.ge = value
        return value

    def applyLe(self, value):
        self.le = value
        return value

    def applyIn(self, value):
        self.In = value
        return value

    def applyAny(self, value):
        self.any = value
        return value

    def applyAll(self, value):
        self.all = value
        return value

