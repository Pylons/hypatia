import unittest

class TestCatalogKeywordIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.keyword import CatalogKeywordIndex
        return CatalogKeywordIndex

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass(lambda x, default: x)

    def test_class_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyClass
        from repoze.catalog.interfaces import ICatalogIndex
        verifyClass(ICatalogIndex, self._getTargetClass())

    def test_instance_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyObject
        from repoze.catalog.interfaces import ICatalogIndex
        verifyObject(ICatalogIndex, self._makeOne())

    def test_apply_with_dict_operator_or(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9]) 
        index.index_doc(5, [9,10])
        result = index.apply({'operator':'or', 'query':[5]})
        self.assertEqual(list(result), [2,3])

    def test_apply_with_dict_operator_and(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9]) 
        index.index_doc(5, [9,10])
        result = index.apply({'operator':'and', 'query':[5, 6]})
        self.assertEqual(list(result), [3])

    def test_apply_with_empty_result_first(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9]) 
        index.index_doc(5, [9,10])
        result = index.apply({'operator':'and', 'query':[11,5]})
        self.assertEqual(list(result), [])
        
    def test_apply_with_empty_result_last(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9]) 
        index.index_doc(5, [9,10])
        result = index.apply({'operator':'and', 'query':[5,11]})
        self.assertEqual(list(result), [])

    def test_apply_doesnt_mutate_query(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        index.index_doc(2, [3,4,5])
        index.index_doc(3, [5,6,7])
        index.index_doc(4, [7,8,9]) 
        index.index_doc(5, [9,10])
        query = {'operator':'or', 'query':[5]}
        result = index.apply(query)
        self.assertEqual(list(result), [2,3])
        self.assertEqual(query, {'operator':'or', 'query':[5]})

    def test_reindex_doc(self):
        index = self._makeOne()
        index.index_doc(1, [1,2,3])
        self.assertEqual(index.documentCount(), 1)
        index.reindex_doc(1, [1,2,3])
        self.assertEqual(index.documentCount(), 1)
        index.reindex_doc(50, [1])
        self.assertEqual(index.documentCount(), 2)
        
