import unittest

class Test_generate_query(unittest.TestCase):
    def _call_fut(self, expr, names=None):
        from repoze.catalog.astquery import parse_query as fut
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

    def test_any(self):
        from repoze.catalog.query import Any
        op = self._call_fut("(a == 1) | (a == 2) | (a == 3)")
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

    def test_all(self):
        from repoze.catalog.query import All
        op = self._call_fut("(a == 1) & (a == 2) & (a == 3)")
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
