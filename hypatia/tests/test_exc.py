import unittest

class TestResultsException(unittest.TestCase):
    def _makeOne(self, resultset):
        from .. import exc
        return exc.ResultsException(resultset)

    def test_it(self):
        inst = self._makeOne(123)
        self.assertEqual(inst.resultset, 123)
        
