import unittest

class Test_generate_query(unittest.TestCase):
    def _call_fut(self, expr, foo=None):
        from repoze.catalog.astquery import generate_query as fut
        return fut(expr)

    def test_not_an_expression(self):
        self.assertRaises(ValueError, self._call_fut, 'a = 1', 1)

    def test_multiple_expressions(self):
        self.assertRaises(ValueError, self._call_fut, 'a == 1\nb == 2\n', 1)

    def test_unhandled_expression(self):
        self.assertRaises(ValueError, self._call_fut, 'a | b')

    def test_non_string_index_name(self):
        # == is not commutative in this context, sorry.
        self.assertRaises(ValueError, self._call_fut, '1 == a')

    def test_bad_value_name(self):
        self.assertRaises(NameError, self._call_fut, 'a == b')

    def test_num(self):
        self.assertEqual(self._call_fut('1'), 1)

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
        lt = self._call_fut("a < foo", foo=6)
        self.failUnless(isinstance(lt, Lt))
        self.assertEqual(lt.index_name, 'a')
        self.assertEqual(lt.value, 6)

    def test_le(self):
        from repoze.catalog.query import Le
        le = self._call_fut("a <= foo", foo=6)
        self.failUnless(isinstance(le, Le))
        self.assertEqual(le.index_name, 'a')
        self.assertEqual(le.value, 6)

    def test_gt(self):
        from repoze.catalog.query import Gt
        gt = self._call_fut('b > 2')
        self.failUnless(isinstance(gt, Gt))
        self.assertEqual(gt.index_name, 'b')
        self.assertEqual(gt.value, 2)

    def test_ge(self):
        from repoze.catalog.query import Ge
        ge = self._call_fut("a >= foo", foo=6)
        self.failUnless(isinstance(ge, Ge))
        self.assertEqual(ge.index_name, 'a')
        self.assertEqual(ge.value, 6)
