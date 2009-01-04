import bisect
import heapq
from itertools import islice

from zope.interface import implements

from zope.index.field import FieldIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = []

FWSCAN = 'fwscan'
NBEST = 'nbest'
TIMSORT = 'timsort'

class CatalogFieldIndex(CatalogIndex, FieldIndex):
    implements(ICatalogIndex)

    def unindex_doc(self, docid):
        """See interface IInjection.

        Base class overridden to be able to unindex None values. """
        rev_index = self._rev_index
        value = rev_index.get(docid, _marker)
        if value is _marker:
            return # not in index

        del rev_index[docid]

        try:
            set = self._fwd_index[value]
            set.remove(docid)
        except KeyError:
            # This is fishy, but we don't want to raise an error.
            # We should probably log something.
            # but keep it from throwing a dirty exception
            set = 1

        if not set:
            del self._fwd_index[value]

        self._num_docs.change(-1)
                
    def sort(self, docids, reverse=False, limit=None, sort_type=None):
        if not docids:
            return []
            
        numdocs = self._num_docs.value
        if not numdocs:
            return []

        if limit is not None:
            limit = int(limit)
            if limit < 1:
                raise ValueError('limit must be 1 or greater')

        if reverse:
            return self.sort_reverse(docids, limit, numdocs, sort_type)
        else:
            return self.sort_forward(docids, limit, numdocs, sort_type)

    def sort_forward(self, docids, limit, numdocs, sort_type=None):

        rlen = len(docids)

        # See http://www.zope.org/Members/Caseman/ZCatalog_for_2.6.1
        # for an overview of why we bother doing all this work to
        # choose the right sort algorithm.

        if sort_type is None:

            if limit and limit < 300:
                # nbest tends to win at very small limit sizes
                # XXX compare nbest to timsort
                sort_type = NBEST

            elif fwscan_wins(limit, rlen, numdocs):
                sort_type = FWSCAN
                
            else:
                sort_type = TIMSORT

        if sort_type == FWSCAN:
            return self.scan_forward(docids, limit)
        elif sort_type == NBEST:
            return self.nbest_ascending(docids, limit)
        elif sort_type == TIMSORT:
            return self.timsort_ascending(docids, limit)
        else:
            raise ValueError('Unknown sort type %s' % sort_type)

    def sort_reverse(self, docids, limit, numdocs, sort_type=None):
        if sort_type is None:
            # XXX this needs work.  See
            # http://www.zope.org/Members/Caseman/ZCatalog_for_2.6.1
            # for an overview of why we bother doing all this work to
            # choose the right sort algorithm.

            rlen = len(docids)
            if limit:
                if (limit < 300) or (limit/float(rlen) > 0.09):
                    sort_type = NBEST
                else:
                    sort_type = TIMSORT
            else:
                sort_type = TIMSORT

        if sort_type == NBEST:
            return self.nbest_descending(docids, limit)
        elif sort_type == TIMSORT:
            return self.timsort_descending(docids, limit)
        else:
            raise ValueError('Unknown sort type %s' % sort_type)
 
    def scan_forward(self, docids, limit=None):
        fwd_index = self._fwd_index

        sets = []
        n = 0
        for set in fwd_index.values():
            for docid in set:
                if docid in docids:
                    n+=1
                    yield docid
                    if limit and n >= limit:
                        raise StopIteration

    def nbest_ascending(self, docids, limit):
        if limit is None:
            raise RuntimeError, 'n-best used without limit'

        # lifted from heapq.nsmallest

        h = nsort(docids, self._rev_index)
        it = iter(h)
        result = sorted(islice(it, 0, limit))
        if not result:
            raise StopIteration
        insort = bisect.insort
        pop = result.pop
        los = result[-1]    # los --> Largest of the nsmallest
        for elem in it:
            if los <= elem:
                continue
            insort(result, elem)
            pop()
            los = result[-1]

        for value, docid in result:
            yield docid

    def nbest_descending(self, docids, limit):
        if limit is None:
            raise RuntimeError, 'N-Best used without limit'
        iterable = nsort(docids, self._rev_index)
        for value, docid in heapq.nlargest(limit, iterable):
            yield docid
    
    def timsort_ascending(self, docids, limit):
        return self._timsort(docids, limit, reverse=False)

    def timsort_descending(self, docids, limit):
        return self._timsort(docids, limit, reverse=True)

    def _timsort(self, docids, limit=None, reverse=False):
        n = 0
        marker = _marker
        _missing = []

        def get(k, rev_index=self._rev_index, marker=marker):
            v = rev_index.get(k, marker)
            if v is marker:
                _missing.append(k)
            return v
        
        for docid in sorted(docids, key=get, reverse=reverse):
            if docid in _missing:
                # skip docids not in this index
                continue
            n += 1
            yield docid
            if limit and n >= limit:
                raise StopIteration

def nsort(docids, rev_index):
    for docid in docids:
        try:
            yield (rev_index[docid], docid)
        except KeyError:
            continue

def fwscan_wins(limit, rlen, numdocs):
    docratio = rlen / float(numdocs)

    if limit:
        limitratio = limit / float(numdocs)
    else:
        limitratio = 1

    div = 65536.0
    
    if docratio >= 16384/div:
        # forward scan tends to beat nbest or timsort reliably when
        # the rlen is greater than a quarter of the number of
        # documents in the index
        return True

    if docratio >= 256/div:
        # depending on the limit ratio, forward scan still has a
        # chance to win over nbest or timsort even if the rlen is
        # smaller than a quarter of the number of documents in the
        # index, beginning at a docratio of 256/65536.0.  XXX It'd be
        # nice to figure out a more concise way to express this.
        if 512/div <= docratio < 1204/div and limitratio <= 4/div:
            return True
        elif  1024/div <= docratio < 2048/div and limitratio <= 32/div:
            return True
        elif 2048/div <= docratio < 4096/div and limitratio <= 128/div:
            return True
        elif 4096/div <= docratio < 8192/div and limitratio <= 512/div:
            return True
        elif 8192/div <= docratio < 16384/div and limitratio <= 4096/div:
            return True

    return False
