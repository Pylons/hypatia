import unittest

class ComparatorTestBase(unittest.TestCase):
    def _makeOne(self, index_name, value):
        return self._getTargetClass()(index_name, value)

class TestQuery(unittest.TestCase):
    def _makeOne(self):
        from repoze.catalog.query import Query as cls
        return cls()

    def test_intersection(self):
        from repoze.catalog.query import Intersection
        a = self._makeOne()
        b = self._makeOne()
        result = a & b
        self.failUnless(isinstance(result, Intersection))
        self.assertEqual(result.left, a)
        self.assertEqual(result.right, b)

    def test_intersection_type_error(self):
        a = self._makeOne()
        self.assertRaises(TypeError, a.__and__, 2)

    def test_or(self):
        from repoze.catalog.query import Union
        a = self._makeOne()
        b = self._makeOne()
        result = a | b
        self.failUnless(isinstance(result, Union))
        self.assertEqual(result.left, a)
        self.assertEqual(result.right, b)

    def test_union_type_error(self):
        a = self._makeOne()
        self.assertRaises(TypeError, a.__or__, 2)

    def test_difference(self):
        from repoze.catalog.query import Difference
        a = self._makeOne()
        b = self._makeOne()
        result = a - b
        self.failUnless(isinstance(result, Difference))
        self.assertEqual(result.left, a)
        self.assertEqual(result.right, b)

    def test_difference_type_error(self):
        a = self._makeOne()
        self.assertRaises(TypeError, a.__sub__, 2)

class TestComparator(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Comparator
        return Comparator

    def test_ctor(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(inst.index_name, 'index')
        self.assertEqual(inst.value, 'val')

class TestContains(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Contains
        return Contains

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.contains, 'val')

class TestEq(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Eq
        return Eq

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.eq, 'val')

class TestNotEq(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import NotEq
        return NotEq

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.not_eq, 'val')

class TestGt(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Gt
        return Gt

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.gt, 'val')

class TestGt(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Lt
        return Lt

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.lt, 'val')

class TestGe(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Ge
        return Ge

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.ge, 'val')

class TestLe(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Le
        return Le

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.le, 'val')

class TestAll(ComparatorTestBase):
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

class Test_generate_query(unittest.TestCase):
    def _call_fut(self, expr, names=None):
        from repoze.catalog.query import parse_query as fut
        return fut(expr, names)

    def test_not_an_expression(self):
        self.assertRaises(ValueError, self._call_fut, 'a = 1')

    def test_multiple_expressions(self):
        self.assertRaises(ValueError, self._call_fut, 'a == 1\nb == 2\n')

    def test_unhandled_operator(self):
        self.assertRaises(ValueError, self._call_fut, 'a ^ b')

    def test_non_string_index_name(self):
        # == is not commutative in this context, sorry.
        self.assertRaises(ValueError, self._call_fut, '1 == a')

    def test_bad_value_name(self):
        self.assertRaises(NameError, self._call_fut, 'a == b')

    def test_bad_operand_for_set_operation(self):
        self.assertRaises(ValueError, self._call_fut, '(a == 1) | 2')
        self.assertRaises(ValueError, self._call_fut, '1 | (b == 2)')

    def test_bad_operand_for_bool_operation(self):
        self.assertRaises(ValueError, self._call_fut, '1 or 2')

    def test_num(self):
        self.assertEqual(self._call_fut('1'), 1)
        self.assertEqual(self._call_fut('1.1'), 1.1)

    def test_str(self):
        self.assertEqual(self._call_fut('"foo"'), 'foo')

    def test_unicode(self):
        self.assertEqual(self._call_fut('u"foo"'), u'foo')

    def test_list(self):
        self.assertEqual(self._call_fut('[1, 2, 3]'), [1, 2, 3])

    def test_tuple(self):
        a, b, c = 1, 2, 3
        self.assertEqual(self._call_fut('(a, b, c)', locals()), (1, 2, 3))

    def test_eq(self):
        from repoze.catalog.query import Eq
        eq = self._call_fut('a == 1')
        self.failUnless(isinstance(eq, Eq))
        self.assertEqual(eq.index_name, 'a')
        self.assertEqual(eq.value, 1)

    def test_not_eq(self):
        from repoze.catalog.query import NotEq
        not_eq = self._call_fut("a != 'one'")
        self.failUnless(isinstance(not_eq, NotEq))
        self.assertEqual(not_eq.index_name, 'a')
        self.assertEqual(not_eq.value, "one")

    def test_lt(self):
        from repoze.catalog.query import Lt
        lt = self._call_fut("a < foo", dict(foo=6))
        self.failUnless(isinstance(lt, Lt))
        self.assertEqual(lt.index_name, 'a')
        self.assertEqual(lt.value, 6)

    def test_le(self):
        from repoze.catalog.query import Le
        le = self._call_fut("a <= 4")
        self.failUnless(isinstance(le, Le))
        self.assertEqual(le.index_name, 'a')
        self.assertEqual(le.value, 4)

    def test_gt(self):
        from repoze.catalog.query import Gt
        gt = self._call_fut('b > 2')
        self.failUnless(isinstance(gt, Gt))
        self.assertEqual(gt.index_name, 'b')
        self.assertEqual(gt.value, 2)

    def test_ge(self):
        from repoze.catalog.query import Ge
        ge = self._call_fut("a >= 5")
        self.failUnless(isinstance(ge, Ge))
        self.assertEqual(ge.index_name, 'a')
        self.assertEqual(ge.value, 5)

    def test_contains(self):
        from repoze.catalog.query import Contains
        contains = self._call_fut("6 in a")
        self.failUnless(isinstance(contains, Contains))
        self.assertEqual(contains.index_name, 'a')
        self.assertEqual(contains.value, 6)

    def test_union(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import Union
        op = self._call_fut("(a == 1) | (b == 2)")
        self.failUnless(isinstance(op, Union))
        query = op.left
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.right
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)

    def test_union_with_bool_syntax(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import Union
        op = self._call_fut("a == 1 or b == 2")
        self.failUnless(isinstance(op, Union))
        query = op.left
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.right
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)

    def test_any(self):
        from repoze.catalog.query import Any
        op = self._call_fut("a == 1 or a == 2 or a == 3")
        self.failUnless(isinstance(op, Any), op)
        self.assertEqual(op.index_name, 'a')
        self.assertEqual(op.value, [1, 2, 3])

    def test_intersection(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import Intersection
        op = self._call_fut("(a == 1) & (b == 2)")
        self.failUnless(isinstance(op, Intersection))
        query = op.left
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.right
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)

    def test_intersection_with_bool_syntax(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import Intersection
        op = self._call_fut("a == 1 and b == 2")
        self.failUnless(isinstance(op, Intersection))
        query = op.left
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.right
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)

    def test_all(self):
        from repoze.catalog.query import All
        op = self._call_fut("a == 1 and a == 2 and a == 3")
        self.failUnless(isinstance(op, All), op)
        self.assertEqual(op.index_name, 'a')
        self.assertEqual(op.value, [1, 2, 3])

    def test_difference(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import Difference
        op = self._call_fut("(a == 1) - (b == 2)")
        self.failUnless(isinstance(op, Difference))
        query = op.left
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.right
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)
