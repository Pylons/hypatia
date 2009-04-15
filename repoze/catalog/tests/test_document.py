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

    def test_add_metadata_not_in_addressmap(self):
        map = self._makeOne()
        self.assertRaises(KeyError, map.add_metadata, 1, {'a':'1'})

    def test_add_metadata_in_addressmap(self):
        map = self._makeOne()
        docid = map.add('/address1')
        map.add_metadata(docid, {'a':1, 'b':2})
        self.assertEqual(map.docid_to_metadata[docid]['a'], 1)
        self.assertEqual(map.docid_to_metadata[docid]['b'], 2)

    def test_add_metadata_no_values(self):
        map = self._makeOne()
        docid = map.add('/address1')
        map.add_metadata(docid, {})
        self.failIf(docid in map.docid_to_metadata)
       
    def test_remove_metadata_nokeys_nodocid(self):
        map = self._makeOne()
        self.assertRaises(KeyError, map.remove_metadata, 1)
        
    def test_remove_metadata_nokeys_docid(self):
        map = self._makeOne()
        docid = map.add('/address1')
        map.docid_to_metadata[docid] = None
        map.remove_metadata(docid)
        self.failIf(docid in map.docid_to_metadata)

    def test_remove_metadata_keys_nodocid(self):
        map = self._makeOne()
        self.assertRaises(KeyError, map.remove_metadata, 1, 'a')

    def test_remove_metadata_keys_docid(self):
        map = self._makeOne()
        docid = map.add('/address1')
        map.docid_to_metadata[docid] = {'a':1, 'b':2, 'c':3}
        map.remove_metadata(docid, 'a', 'b')
        self.assertEqual(map.docid_to_metadata[docid], {'c':3})
        map.remove_metadata(docid, 'c')
        self.failIf(docid in map.docid_to_metadata)

    def test_get_metadata_no_mainbtree(self):
        map = self._makeOne()
        map.docid_to_metadata = None
        self.assertRaises(KeyError, map.get_metadata, 1)

    def test_get_metadata_not_in_map(self):
        map = self._makeOne()
        self.assertRaises(KeyError, map.get_metadata, 1)

    def test_get_metadata_nokeys(self):
        map = self._makeOne()
        map.docid_to_metadata[1] = {'a':1, 'b':2}
        self.assertEqual(dict(map.get_metadata(1)), {'a':1, 'b':2})

    def test_remove_docid_exists(self):
        map = self._makeOne()
        map.add('/address1', 1)
        map.docid_to_metadata[1] = None
        result = map.remove_docid(1)
        self.assertEqual(result, True)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)
        self.failIf(1 in map.docid_to_metadata)

    def test_remove_docid_doesntexist(self):
        map = self._makeOne()
        result = map.remove_docid(1)
        self.assertEqual(result, False)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)

    def test_remove_address_exists(self):
        map = self._makeOne()
        map.add('/address1', 1)
        map.docid_to_metadata[1] = None
        result = map.remove_address('/address1')
        self.assertEqual(result, True)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.address_to_docid.get('/address1'), None)
        self.failIf(1 in map.docid_to_metadata)

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

    def test_check_metadata(self):
        map = self._makeOne()
        map.docid_to_metadata = None
        map._check_metadata()
        self.failIf(map.docid_to_metadata is None)
        
        
