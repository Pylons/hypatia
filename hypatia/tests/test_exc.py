import unittest

class TestBadResults(unittest.TestCase):
    def _makeOne(self, resultset):
        from .. import exc
        return exc.BadResults(resultset)

    def test_it(self):
        inst = self._makeOne(123)
        self.assertEqual(inst.resultset, 123)
        
