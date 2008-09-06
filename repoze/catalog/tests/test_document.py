import unittest

class TestDocumentMap(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.document import DocumentMap
        return DocumentMap

    def _makeOne(self):
        return self._getTargetClass()()

    def test_add(self):
        map = self._makeOne()
        map.add(1, '/path1')
        map.add(2, '/path2')
        map.add(2, '/anotherpath2')
        self.assertEqual(map.docid_to_path[1], '/path1')
        self.assertEqual(map.path_to_docid['/path1'], 1)
        self.assertEqual(map.docid_to_path[2], '/anotherpath2')
        self.assertEqual(map.path_to_docid['/anotherpath2'], 2)

    def test_remove_docid_exists(self):
        map = self._makeOne()
        map.add(1, '/path1')
        map.remove_docid(1)
        self.assertEqual(map.docid_to_path.get(1), None)
        self.assertEqual(map.path_to_docid.get('/path1'), None)

    def test_remove_docid_doesntexist(self):
        map = self._makeOne()
        map.remove_docid(1)
        self.assertEqual(map.docid_to_path.get(1), None)
        self.assertEqual(map.path_to_docid.get('/path1'), None)
        
    def test_remove_path_exists(self):
        map = self._makeOne()
        map.add(1, '/path1')
        map.remove_path('/path1')
        self.assertEqual(map.docid_to_path.get(1), None)
        self.assertEqual(map.path_to_docid.get('/path1'), None)

    def test_remove_path_doesntexist(self):
        map = self._makeOne()
        map.remove_path('/path1')
        self.assertEqual(map.docid_to_path.get(1), None)
        self.assertEqual(map.path_to_docid.get('/path1'), None)

    def test_docid_for_path(self):
        map = self._makeOne()
        map.add(1, '/path1')
        self.assertEqual(map.docid_for_path('/path1'), 1)
        self.assertEqual(map.docid_for_path('/notexist'), None)

    def test_path_for_docid(self):
        map = self._makeOne()
        map.add(1, '/path1')
        self.assertEqual(map.path_for_docid(1), '/path1')
        self.assertEqual(map.path_for_docid(2), None)
