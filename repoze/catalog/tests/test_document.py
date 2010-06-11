import unittest

class TestDocumentMap(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.document import DocumentMap
        return DocumentMap

    def _makeOne(self):
        return self._getTargetClass()()

    def test_docid_for_address_nonesuch(self):
        map = self._makeOne()
        map.add('/address1', 1)
        self.assertEqual(map.docid_for_address('/notexist'), None)

    def test_docid_for_address_existing(self):
        map = self._makeOne()
        map.add('/address1', 1)
        self.assertEqual(map.docid_for_address('/address1'), 1)

    def test_address_for_docid_nonesuch(self):
        map = self._makeOne()
        map.add('/address1', 1)
        self.assertEqual(map.address_for_docid(2), None)

    def test_address_for_docid_existing(self):
        map = self._makeOne()
        map.add('/address1', 1)
        self.assertEqual(map.address_for_docid(1), '/address1')

    def test_add_simple(self):
        map = self._makeOne()
        docid = map.add('/address')
        self.assertEqual(map.address_for_docid(docid), '/address')
        self.assertEqual(map.docid_for_address('/address'), docid)

    def test_add_with_same_address_repeatedly_replaces(self):
        map = self._makeOne()
        map.add('yup', 1)
        map.add('yup', 2)
        map.add('yup', 3)
        self.assertEqual(len(map.docid_to_address), 1)
        self.assertEqual(len(map.address_to_docid), 1)
        self.assertEqual(map.docid_to_address.get(1), None)
        self.assertEqual(map.docid_to_address.get(2), None)
        self.assertEqual(map.docid_to_address.get(3), 'yup')
        self.assertEqual(map.address_to_docid['yup'], 3)

    def test_add_address_None(self):
        map = self._makeOne()
        map.add(None, 1)
        map.add(None, 2)
        self.assertEqual(len(map.docid_to_address), 1)
        self.assertEqual(len(map.address_to_docid), 1)
        self.failIf(1 in map.docid_to_address)
        self.assertEqual(map.docid_to_address.get(2), None)
        self.assertEqual(map.address_to_docid[None], 2)

    def test_add_existing_docid_new_address_replaces_old(self):
        map = self._makeOne()
        old_docid = map.add('/address1')
        new_docid = map.add('/address2', old_docid)
        self.assertEqual(map.address_for_docid(old_docid), '/address2')
        self.assertEqual(map.docid_for_address('/address1'), None)
        self.assertEqual(map.docid_for_address('/address2'), old_docid)
        self.assertEqual(new_docid, old_docid)

    def test_add_existing_docid_removes_metadata(self):
        map = self._makeOne()
        docid = map.add('/address1')
        map.add_metadata(docid, {'a': 1})
        map.add('/address2', docid)
        self.assertRaises(KeyError, map.get_metadata, docid)

    def test_remove_docid_nonesuch(self):
        map = self._makeOne()
        result = map.remove_docid(1)
        self.assertEqual(result, False)
        self.assertEqual(map.address_for_docid(1), None)
        self.assertEqual(map.docid_for_address('/address1'), None)

    def test_remove_docid_existing(self):
        map = self._makeOne()
        map.add('/address1', 1)
        map.add_metadata(1, {'a': 1})
        result = map.remove_docid(1)
        self.assertEqual(result, True)
        self.assertEqual(map.address_for_docid(1), None)
        self.assertEqual(map.docid_for_address('/address1'), None)
        self.assertRaises(KeyError, map.get_metadata, 1)

    def test_remove_docid_map_out_of_sync(self):
        map = self._makeOne()
        map.add('/address1', 1)
        map.add_metadata(1, {'a': 1})
        map.address_to_docid['/address1'] = 2
        result = map.remove_docid(1)
        self.assertEqual(result, True)
        self.assertEqual(map.address_for_docid(1), None)
        self.assertEqual(map.docid_for_address('/address1'), None)
        self.assertRaises(KeyError, map.get_metadata, 1)
        self.assertEqual(list(map.docid_to_address), [])
        self.assertEqual(list(map.address_to_docid), [])

    def test_remove_address_nonesuch(self):
        map = self._makeOne()
        result = map.remove_address('/address1')
        self.assertEqual(result, False)
        self.assertEqual(map.address_for_docid(1), None)
        self.assertEqual(map.docid_for_address('/address1'), None)

    def test_remove_address_exists(self):
        map = self._makeOne()
        map.add('/address1', 1)
        map.docid_to_metadata[1] = None
        result = map.remove_address('/address1')
        self.assertEqual(result, True)
        self.assertEqual(map.address_for_docid(1), None)
        self.assertEqual(map.docid_for_address('/address1'), None)
        self.failIf(1 in map.docid_to_metadata)

    def test_remove_address_map_out_of_sync(self):
        map = self._makeOne()
        map.add('/address1', 1)
        map.add_metadata(1, {'a': 1})
        map.docid_to_address[1] = '/address2'
        map.address_to_docid['/address2'] = 3
        result = map.remove_address('/address1')
        self.assertEqual(result, True)
        self.assertEqual(map.address_for_docid(1), None)
        self.assertEqual(map.docid_for_address('/address1'), None)
        self.assertRaises(KeyError, map.get_metadata, 1)
        self.assertEqual(list(map.docid_to_address), [])
        self.assertEqual(list(map.address_to_docid), [])


    def test_add_metadata_docid_not_in_addressmap(self):
        map = self._makeOne()
        self.assertRaises(KeyError, map.add_metadata, 1, {'a':'1'})

    def test_add_metadata_docid_in_addressmap(self):
        map = self._makeOne()
        docid = map.add('/address1')
        map.add_metadata(docid, {'a':1, 'b':2})
        self.assertEqual(map.get_metadata(docid)['a'], 1)
        self.assertEqual(map.get_metadata(docid)['b'], 2)

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
        self.assertEqual(map.get_metadata(docid), {'c':3})
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
        map.add('/address', 1)
        map.add_metadata(1, {'a':1, 'b':2})
        self.assertEqual(dict(map.get_metadata(1)), {'a':1, 'b':2})

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

    def test__check_metadata_creates_tree(self):
        map = self._makeOne()
        map.docid_to_metadata = None
        map._check_metadata()
        self.failIf(map.docid_to_metadata is None)
        self.assertEqual(dict(map.docid_to_metadata), {})
