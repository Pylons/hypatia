from zope.interface import implements

from zope.index.keyword import KeywordIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    implements(ICatalogIndex)

    def reindex_doc(self, docid, value):
        # the base index' index_doc method special-cases a reindex
        return self.index_doc(docid, value)

    def apply(self, query):
        """ Work around the fact that zope.index's apply method
        actually mutates the query if it's a dict """
        operator = 'and'
        if isinstance(query, dict):
            query = query.copy() # this is the fix
            if 'operator' in query:
                operator = query.pop('operator')
            query = query['query']
        return self.search(query, operator=operator)
