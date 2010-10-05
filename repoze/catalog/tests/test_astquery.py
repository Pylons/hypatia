import unittest

class Test_generate_query(unittest.TestCase):
    def _call_fut(self, expr):
        import sys
        frame = sys._getframe(1)
        locals().update(frame.f_locals)
        from repoze.catalog.astquery import generate_query as fut
        return fut(expr)

    def test_not_an_expression(self):
        self.assertRaises(ValueError, self._call_fut, 'a = 1')

    def test_multiple_expressions(self):
        self.assertRaises(ValueError, self._call_fut, 'a == 1\nb == 2\n')

    def test_unhandled_expression(self):
        self.assertRaises(ValueError, self._call_fut, 'a | b')

    def test_non_string_index_name(self):
        # == is not commutative in this context, sorry.
        self.assertRaises(ValueError, self._call_fut, '1 == a')

    def test_bad_value_name(self):
        self.assertRaises(NameError, self._call_fut, 'a == b')

    def test_bad_boolean_op(self):
        self.assertRaises(ValueError, self._call_fut, '1 or 2')

    def test_or_not(self):
        self.assertRaises(
            ValueError, self._call_fut, "a == 1 or not(b == 2 and c== 3)")

    def test_bad_not(self):
        self.assertRaises(
            ValueError, self._call_fut, "not 1")

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
        self.assertEqual(self._call_fut('(a, b, c)'), (1, 2, 3))

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
        foo = 6
        lt = self._call_fut("a < foo")
        self.failUnless(isinstance(lt, Lt))
        self.assertEqual(lt.index_name, 'a')
        self.assertEqual(lt.value, 6)

    def test_le(self):
        from repoze.catalog.query import Le
        foo = 6
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

    def test_or(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import Or
        op = self._call_fut("a == 1 or b == 2")
        self.failUnless(isinstance(op, Or))
        self.assertEqual(len(op.queries), 2)
        query = op.queries[0]
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.queries[1]
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)

    def test_and(self):
        from repoze.catalog.query import Eq
        from repoze.catalog.query import And
        op = self._call_fut("a == 1 and b == 2")
        self.failUnless(isinstance(op, And))
        self.assertEqual(len(op.queries), 2)
        query = op.queries[0]
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = op.queries[1]
        self.failUnless(isinstance(query, Eq))
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)

    def test_any(self):
        from repoze.catalog.query import Any
        op = self._call_fut("a == 1 or a == 2")
        self.failUnless(isinstance(op, Any))
        self.assertEqual(op.index_name, 'a')
        self.assertEqual(op.value, [1, 2])

    def test_all(self):
        from repoze.catalog.query import All
        op = self._call_fut("a == 1 and a == 2") # Could be keyword index
        self.failUnless(isinstance(op, All))
        self.assertEqual(op.index_name, 'a')
        self.assertEqual(op.value, [1, 2])

    def test_nested_bool(self):
        from repoze.catalog.query import And
        from repoze.catalog.query import Or
        from repoze.catalog.query import Eq
        op = self._call_fut("a == 1 and b == 2 or c == 3")
        self.failUnless(isinstance(op, Or))
        self.assertEqual(len(op.queries), 2)
        subop = op.queries[0]
        self.failUnless(isinstance(subop, And))
        self.assertEqual(len(subop.queries), 2)
        query = subop.queries[0]
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        query = subop.queries[1]
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)
        query = op.queries[1]
        self.assertEqual(query.index_name, 'c')
        self.assertEqual(query.value, 3)

    def test_and_not(self):
        from repoze.catalog.query import And
        from repoze.catalog.query import Not
        from repoze.catalog.query import Or
        from repoze.catalog.query import Eq
        op = self._call_fut("a == 1 and not(b == 2 or c == 3)")
        self.failUnless(isinstance(op, And))
        self.assertEqual(len(op.queries), 2)
        query = op.queries[0]
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        subop = op.queries[1]
        self.failUnless(isinstance(subop, Not))
        subop = subop.query
        self.failUnless(isinstance(subop, Or))
        self.assertEqual(len(subop.queries), 2)
        query = subop.queries[0]
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)
        query = subop.queries[1]
        self.assertEqual(query.index_name, 'c')
        self.assertEqual(query.value, 3)

    def test_move_nots_to_end(self):
        from repoze.catalog.query import And
        from repoze.catalog.query import Not
        from repoze.catalog.query import Or
        from repoze.catalog.query import Eq
        op = self._call_fut("not(b == 2 or c == 3) and a == 1")
        self.failUnless(isinstance(op, And))
        self.assertEqual(len(op.queries), 2)
        query = op.queries[0]
        self.assertEqual(query.index_name, 'a')
        self.assertEqual(query.value, 1)
        subop = op.queries[1]
        self.failUnless(isinstance(subop, Not))
        subop = subop.query
        self.failUnless(isinstance(subop, Or))
        self.assertEqual(len(subop.queries), 2)
        query = subop.queries[0]
        self.assertEqual(query.index_name, 'b')
        self.assertEqual(query.value, 2)
        query = subop.queries[1]
        self.assertEqual(query.index_name, 'c')
        self.assertEqual(query.value, 3)



