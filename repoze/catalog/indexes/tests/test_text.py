import unittest

class TestCatalogTextIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.text import CatalogTextIndex
        return CatalogTextIndex

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

    def test_apply(self):
        index = self._makeOne()
        index.index_doc(1, 'now is the time')
        index.index_doc(2, 'for all good men')
        index.index_doc(3, 'to come to')
        index.index_doc(4, 'the aid of') 
        index.index_doc(5, 'their country')
        index.index_doc(6, 'country music')
        index.index_doc(7, 'is good music')
        result = index.apply('country')
        self.assertEqual(list(result), [5, 6])
        result = index.apply('good')
        self.assertEqual(list(result), [2, 7])
        result = index.apply('time')
        self.assertEqual(list(result), [1])

    def test_reindex_doc(self):
        index = self._makeOne()
        index.reindex_doc(1, 'now is the time')
        result = index.apply('time')
        self.assertEqual(list(result), [1])
        
        
        

