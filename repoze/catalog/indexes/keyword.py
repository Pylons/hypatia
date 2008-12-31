from zope.interface import implements

from zope.index.keyword import KeywordIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    normalize = False # override base index: dont try to normalize case
    implements(ICatalogIndex)

    def apply(self, query):
        operator = 'and'
        if isinstance(query, dict):
            if 'operator' in query:
                operator = query.pop('operator')
            query = query['query']
        return self.search(query, operator=operator)

    def _insert_forward(self, docid, words):
        """insert a sequence of words into the forward index.

        Base class overridden to use IF.Set rather than IISet so we
        can merge results with other indexes.
        """

        idx = self._fwd_index
        has_key = idx.has_key
        for word in words:
            if not has_key(word):
                idx[word] = self.family.IF.Set()
            idx[word].insert(docid)

    def search(self, query, operator='and'):
        """Execute a search given by 'query'.

        Base class overridden to use multiunion rather than calling
        union repeatedly (much, much faster); also if it's an
        intersection, sort from smallest to largest before
        intersecting.  Also, use an IF.Set rather than an II.Set so we
        can merge results with other indexes.  We also pay no
        attention to the ``normalize`` attribute, unlike the base
        index (it's useless to try to normalize here; it's the app's
        job, and values might not even be strings).
        """
        if isinstance(query, basestring):
            query = [query]

        sets = []
        is_and = operator == 'and'

        if operator == 'and':
            for word in query:
                docids = self._fwd_index.get(word)
                if not docids:
                    return []
                sets.append(docids)
            rs = None
            # sort smallest to largest set so we intersect the smallest
            # number of document identifiers possible
            sets.sort(key=len)
            for set in sets:
                rs = self.family.IF.intersection(rs, set)
                if not rs:
                    break
        else:
            for word in query:
                docids = self._fwd_index.get(word)
                if docids:
                    sets.append(docids)
            rs = self.family.IF.multiunion(sets)

        if rs:
            return rs
        else:
            return self.family.IF.Set()

