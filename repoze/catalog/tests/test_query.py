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

    def test_iter_children(self):
        a = self._makeOne()
        self.assertEqual(a.iter_children(), ())

    def test_print_tree(self):
        from repoze.catalog.query import Query
        class Derived(Query):
            def __init__(self, name):
                self.name = name
                self.children = []
            def __str__(self):
                return self.name
            def iter_children(self):
                return self.children

        from StringIO import StringIO
        a = Derived('A')
        b = Derived('B')
        c = Derived('C')
        a.children.append(b)
        a.children.append(c)

        buf = StringIO()
        a.print_tree(buf)
        self.assertEqual(buf.getvalue(), 'A\n  B\n  C\n')

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

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "'val' in index")

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

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "index == 'val'")

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

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "index != 'val'")

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

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "index > 'val'")

class TestLt(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Lt
        return Lt

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.lt, 'val')

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "index < 'val'")

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

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "index >= 'val'")

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

    def test_to_str(self):
        inst = self._makeOne('index', 'val')
        self.assertEqual(str(inst), "index <= 'val'")

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

    def test_to_str(self):
        inst = self._makeOne('index', [1, 2, 3])
        self.assertEqual(str(inst), "index all [1, 2, 3]")

class TestAny(ComparatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Any
        return Any

    def test_apply(self):
        catalog = DummyCatalog()
        inst = self._makeOne('index', 'val')
        result = inst.apply(catalog)
        self.assertEqual(result, 'val')
        self.assertEqual(catalog.index.any, 'val')

    def test_to_str(self):
        inst = self._makeOne('index', [1, 2, 3])
        self.assertEqual(str(inst), "index any [1, 2, 3]")

class OperatorTestBase(unittest.TestCase):
    def _makeOne(self, left, right):
        return self._getTargetClass()(left, right)

class TestOperator(OperatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Operator as cls
        return cls

    def test_iter_children(self):
        o = self._makeOne('left', 'right')
        self.assertEqual(list(o.iter_children()), ['left', 'right'])

class TestUnion(OperatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Union as cls
        return cls

    def test_to_str(self):
        o = self._makeOne(None, None)
        self.assertEqual(str(o), 'Union')

    def test_apply(self):
        left = DummyQuery(set([1, 2]))
        right = DummyQuery(set([3, 4]))
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set([1, 2, 3, 4]))
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.union, (left.results, right.results))

    def test_apply_left_empty(self):
        left = DummyQuery(set())
        right = DummyQuery(set([3, 4]))
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set([3, 4]))
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.union, None)

    def test_apply_right_empty(self):
        left = DummyQuery(set([1, 2]))
        right = DummyQuery(set())
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set([1, 2]))
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.union, None)

class TestIntersection(OperatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Intersection as cls
        return cls

    def test_to_str(self):
        o = self._makeOne(None, None)
        self.assertEqual(str(o), 'Intersection')

    def test_apply(self):
        left = DummyQuery(set([1, 2, 3]))
        right = DummyQuery(set([3, 4, 5]))
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set([3]))
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.intersection, (left.results, right.results))

    def test_apply_left_empty(self):
        left = DummyQuery(set([]))
        right = DummyQuery(set([3, 4, 5]))
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set())
        self.failUnless(left.applied)
        self.failIf(right.applied)
        self.assertEqual(o.family.intersection, None)

    def test_apply_right_empty(self):
        left = DummyQuery(set([1, 2, 3]))
        right = DummyQuery(set())
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set())
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.intersection, None)

class TestDifference(OperatorTestBase):
    def _getTargetClass(self):
        from repoze.catalog.query import Difference as cls
        return cls

    def test_to_str(self):
        o = self._makeOne(None, None)
        self.assertEqual(str(o), 'Difference')

    def test_apply(self):
        left = DummyQuery(set([1, 2, 3]))
        right = DummyQuery(set([3, 4, 5]))
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set([1, 2]))
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.diff, (left.results, right.results))

    def test_apply_left_empty(self):
        left = DummyQuery(set([]))
        right = DummyQuery(set([3, 4, 5]))
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set())
        self.failUnless(left.applied)
        self.failIf(right.applied)
        self.assertEqual(o.family.diff, None)

    def test_right_empty(self):
        left = DummyQuery(set([1, 2, 3]))
        right = DummyQuery(set())
        o = self._makeOne(left, right)
        o.family = DummyFamily()
        self.assertEqual(o.apply(None), set([1, 2, 3]))
        self.failUnless(left.applied)
        self.failUnless(right.applied)
        self.assertEqual(o.family.diff, None)

class Test_parse_query(unittest.TestCase):
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

    def applyAny(self, value):
        self.any = value
        return value

    def applyAll(self, value):
        self.all = value
        return value

class DummyFamily(object):
    union = None
    intersection = None
    diff = None

    @property
    def IF(self):
        return self

    def weightedUnion(self, left, right):
        self.union = (left, right)
        return None, left | right

    def weightedIntersection(self, left, right):
        self.intersection = (left, right)
        return None, left & right

    def difference(self, left, right):
        self.diff = (left, right)
        return left - right

    def Set(self):
        return set()

class DummyQuery(object):
    applied = False

    def __init__(self, results):
        self.results = results

    def apply(self, catalog):
        self.applied = True
        return self.results

