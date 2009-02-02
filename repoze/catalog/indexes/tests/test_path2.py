import unittest

class CatalogPathIndex2Tests(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.path2 import CatalogPathIndex2
        return CatalogPathIndex2

    def _makeOne(self, values=None):
        if values is None:
            values = {}
        index = self._getTargetClass()('path')
        for doc_id, path in values.items():
            index.index_doc(doc_id, path)
        return index

    def test_class_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyClass
        from repoze.catalog.interfaces import ICatalogIndex
        verifyClass(ICatalogIndex, self._getTargetClass())

    def test_instance_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyObject
        from repoze.catalog.interfaces import ICatalogIndex
        verifyObject(ICatalogIndex, self._makeOne())

    def test_throws_on_no_query(self):
        index = self._makeOne({})
        self.assertRaises(KeyError, index.apply, {})

    def test_empty_index(self):
        index = self._makeOne({})
        self.assertEqual(index.numObjects() ,0)

    def test_unindex_works_if_nonexisting(self):
        index = self._makeOne({})
        index.unindex_doc(1234) # nothrow

    def test_nonempty_index(self):
        index = self._makeOne(VALUES)
        self.assertEqual(index.numObjects(), 22)

    def test_unindex_doc(self):
        index = self._makeOne(VALUES)

        for doc_id in VALUES.keys():
            index.unindex_doc(doc_id)

        self.assertEqual(index.numObjects(), 0)
        self.assertEqual(list(index.adjacency.keys()), [])
        self.assertEqual(list(index.disjoint.keys()), [])
        self.assertEqual(list(index.path_to_docid.keys()), [])
        self.assertEqual(list(index.docid_to_path.keys()), [])

    def test_reindex_doesnt_dupe(self):
        index = self._makeOne()
        o = Dummy('/foo/bar')
        index.index_doc(1, o)
        self.assertEqual(index.numObjects(), 1)
        index.index_doc(1, o)
        self.assertEqual(index.numObjects(), 1)

    def test_unindex_nomatch_doesnt_raise(self):
        index = self._makeOne()
        # this should not raise an error
        index.unindex_doc(-1)

    def test_search_root_nodepth(self):
        index = self._makeOne(VALUES)
        result = index.search('/')
        self.assertEqual(sorted(result), range(1, 21))

    def test_search_root_depth_0(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=0)
        self.assertEqual(sorted(result), [])

    def test_search_root_depth_1(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=1)
        self.assertEqual(sorted(result), [1,5])

    def test_search_aa_nodepth(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa')
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_search_aa_depth_0(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', depth=0)
        self.assertEqual(sorted(result), [])

    def test_search_aa_depth_1(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', depth=1)
        self.assertEqual(sorted(result), [2,3,4])

    def test_search_bb_nodepth(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb')
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])

    def test_search_bb_depth_0(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', depth=0)
        self.assertEqual(sorted(result), [])

    def test_search_b_depth_1(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', depth=1)
        self.assertEqual(sorted(result), [6,7,8])

    def test_search_with_tuple(self):
        index = self._makeOne(VALUES)
        result = index.search(('', 'bb'))
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])

    def test_disjoint_resolved(self):
        index = self._makeOne(VALUES)
        result = index.search('/disjoint')
        self.assertEqual(sorted(result), [])
        index.index_doc(22, Dummy('/disjoint'))
        result = index.search('/disjoint')
        self.assertEqual(sorted(result), [21])

    def test_apply_path_string(self):
        index = self._makeOne(VALUES)
        result = index.apply('/aa')
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])
        
    def test_apply_path_dict(self):
        index = self._makeOne(VALUES)
        result = index.apply({'query':'/aa', 'level':1})
        self.assertEqual(sorted(result), [2, 3, 4])
        
        
class Dummy:

    def __init__( self, path):
        self.path = path

VALUES = {
    0 : Dummy('/'),
    1 : Dummy('/aa'),
    2 : Dummy('/aa/aa'),
    3 : Dummy('/aa/bb'),
    4 : Dummy('/aa/cc'),
    5 : Dummy('/bb'),
    6 : Dummy('/bb/aa'),
    7 : Dummy('/bb/bb'),
    8 : Dummy('/bb/cc'),
    9 : Dummy("/aa/aa/1.html"),
    10 : Dummy("/aa/aa/2.html"),
    11 : Dummy("/aa/bb/3.html"),
    12 : Dummy("/aa/bb/4.html"),
    13 : Dummy("/aa/cc/5.html"),
    14 : Dummy("/aa/cc/6.html"),
    15 : Dummy("/bb/aa/7.html"),
    16 : Dummy("/bb/aa/8.html"),
    17 : Dummy("/bb/bb/9.html"),
    18 : Dummy("/bb/bb/10.html"),
    19 : Dummy("/bb/cc/11.html"),
    20 : Dummy("/bb/cc/12.html"),
    21 : Dummy('/disjoint/entry')
    }
