import unittest

class TestCatalogFieldIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.field import CatalogFieldIndex
        return CatalogFieldIndex

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass(lambda x, default: x)

    def _populateIndex(self, index):
        index.index_doc(5, 1) # docid, obj
        index.index_doc(2, 2)
        index.index_doc(1, 3)
        index.index_doc(3, 4) 
        index.index_doc(4, 5)
        index.index_doc(8, 6)
        index.index_doc(9, 7)
        index.index_doc(7, 8)
        index.index_doc(6, 9)
        index.index_doc(11, 10)
        index.index_doc(10, 11)

    def test_sort_scan_nolimit(self):
        index = self._makeOne()
        index.force_scan = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1)
        self.assertEqual(list(result), [5, 2, 1, 3, 4])

    def test_sort_scan_withlimit(self):
        index = self._makeOne()
        index.force_scan = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_scan_reverse_nolimit(self):
        index = self._makeOne()
        index.force_scan = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True)
        self.assertEqual(list(result), [4, 3, 1, 2, 5])

    def test_sort_scan_reverse_withlimit(self):
        index = self._makeOne()
        index.force_scan = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3, reverse=True)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_brute_nolimit(self):
        index = self._makeOne()
        index.force_brute = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1)
        self.assertEqual(list(result), [5, 2, 1, 3, 4])

    def test_sort_brute_missingdocid(self):
        index = self._makeOne()
        index.force_brute = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1)
        self.assertEqual(list(result), [5, 2, 1, 3, 4]) # 99 not present

    def test_sort_brute_withlimit(self):
        index = self._makeOne()
        index.force_brute = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_brute_reverse_nolimit(self):
        index = self._makeOne()
        index.force_brute = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True)
        self.assertEqual(list(result), [4, 3, 1, 2, 5])

    def test_sort_brute_reverse_withlimit(self):
        index = self._makeOne()
        index.force_brute = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True, limit=3)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_nbest(self):
        index = self._makeOne()
        index.force_nbest = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_nbest_reverse(self):
        index = self._makeOne()
        index.force_nbest = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True, limit=3)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_nbest_missing(self):
        index = self._makeOne()
        index.force_nbest = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, limit=3)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_nbest_missing_reverse(self):
        index = self._makeOne()
        index.force_nbest = True
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, reverse=True, limit=3)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_nodocs(self):
        index = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1)
        self.assertEqual(list(result), [])

    def test_sort_nodocids(self):
        index = self._makeOne()
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet()
        result = index.sort(c1)
        self.assertEqual(list(result), [])

    def test_sort_badlimit(self):
        index = self._makeOne()
        self._populateIndex(index)
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError, index.sort, c1, limit=0)

