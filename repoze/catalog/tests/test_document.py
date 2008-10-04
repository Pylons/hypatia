import unittest

class TestDocumentMap(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.document import DocumentMap
        return DocumentMap

    def _makeOne(self):
        return self._getTargetClass()()

    def test_add(self):
        map = self._makeOne()
        address1id = map.add('/address1')
        address2id = map.add('/address2')
        newaddress2id = map.add('/address3', address2id)
        self.assertEqual(map.docid_to_address[address1id], '/address1')
        self.assertEqual(map.address_to_docid['/address1'], address1id)
        self.assertEqual(map.docid_to_address[address2id], '/address3')
        self.assertEqual(map.address_to_docid['/address3'], address2id)
        self.assertEqual(newaddress2id, address2id)

    def test_remove_docid_exists(self):
        map = self._makeOne()
        map.add('/address1', 1)
        result = map.remove_docid(1)
        self.assertEqual(result, True)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)

    def test_remove_docid_doesntexist(self):
        map = self._makeOne()
        result = map.remove_docid(1)
        self.assertEqual(result, False)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)
        
    def test_remove_address_exists(self):
        map = self._makeOne()
        map.add('/address1', 1)
        result = map.remove_address('/address1')
        self.assertEqual(result, True)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)

    def test_remove_address_doesntexist(self):
        map = self._makeOne()
        result = map.remove_address('/address1')
        self.assertEqual(result, False)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)

    def test_docid_for_address(self):
        map = self._makeOne()
        map.add('/address1', 1)
        self.assertEqual(map.docid_for_address('/address1'), 1)
        self.assertEqual(map.docid_for_address('/notexist'), None)

    def test_address_for_docid(self):
        map = self._makeOne()
        map.add('/address1', 1)
        self.assertEqual(map.address_for_docid(1), '/address1')
        self.assertEqual(map.address_for_docid(2), None)

    def test_new_docid(self):
        map = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        map._randrange = randrange
        map.add('/whatever', 0)
        self.assertEqual(map.new_docid(), 1)
        
