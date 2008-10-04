from zope.interface import implements

from zope.index.keyword import KeywordIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    normalize = False
    implements(ICatalogIndex)

    def apply(self, query):
        operator = 'and'
        if isinstance(query, dict):
            if 'operator' in query:
                operator = query.pop('operator')
            query = query['query']
        return self.search(query, operator=operator)

    def _insert_forward(self, docid, words):
        """insert a sequence of words into the forward index """

        idx = self._fwd_index
        has_key = idx.has_key
        for word in words:
            if not has_key(word):
                idx[word] = self.family.IF.Set()
            idx[word].insert(docid)

    def search(self, query, operator='and'):
        """Execute a search given by 'query'."""
        if isinstance(query, basestring):
            query = [query]

        f = {'and' : self.family.IF.intersection,
             'or' : self.family.IF.union,
             }[operator]
    
        rs = None
        for word in query:
            docids = self._fwd_index.get(word, self.family.IF.Set())
            rs = f(rs, docids)
            
        if rs:
            return rs
        else:
            return self.family.IF.Set()

