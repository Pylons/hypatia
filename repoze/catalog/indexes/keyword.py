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

        sets = []
        for word in query:
            docids = self._fwd_index.get(word, self.family.IF.Set())
            sets.append(docids)

        if operator == 'or':
            rs = self.family.IF.multiunion(sets)

        else:
            rs = None
            # sort smallest to largest set so we intersect the smallest
            # number of document identifiers possible
            sets.sort(lambda x, y: cmp(len(x), len(y)))
            for set in sets:
                rs = self.family.IF.intersection(rs, set)
                if not rs:
                    break

        if rs:
            return rs
        else:
            return self.family.IF.Set()

