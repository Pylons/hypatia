import bisect
import heapq
from itertools import islice

from zope.interface import implements

from zope.index.field import FieldIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = []

class CatalogFieldIndex(CatalogIndex, FieldIndex):
    implements(ICatalogIndex)
    scan_slope = 247.95
    scan_icept = .596
    nbest_percent = .09
    force_scan = False
    force_nbest = False
    force_brute = False

    def sort(self, docids, reverse=False, limit=None):
        if limit is not None:
            limit = int(limit)
            if limit < 1:
                raise ValueError('limit must be 1 or greater')

        if not docids:
            return []
            
        numdocs = self._num_docs.value
        if not numdocs:
            return []

        if reverse:
            return self.sort_reverse(docids, limit, numdocs)
        else:
            return self.sort_forward(docids, limit, numdocs)

    def sort_forward(self, docids, limit, numdocs):

        rev_index = self._rev_index
        fwd_index = self._fwd_index

        rlen = len(docids)

        # for unit testing
        if self.force_scan:
            return self.scan_forward(docids, limit)
        elif self.force_nbest:
            return self.nbest_ascending(docids, limit)
        elif self.force_brute:
            return self.bruteforce_ascending(docids, limit)

        if limit:
            # Forward scan "wins" when the supplied limit is below a
            # point on a linear scale.  If limit < scanlimit, it means
            # that the limit is below the line on a graph represented
            # by y=mx+b where m=scan_slope and b=scan_intercept, using
            # (float(rlen)/numdocs) as "x", solving for the maximum
            # limit as y.  The default line slope and intercept was
            # computed using these two points: point1 = (.01372, 4),
            # point2 = (.562, 140), based on emprical testing using an
            # index that had about 67000 total documentids in it
            # against a ZEO server with a zodb cache size=300000 and
            # zeo cache size of 1GB on Mac OS X.  Forward-scan has a
            # very limited set of uses; its only used when the limit
            # is very small and the ratio of numdocs/rlen is very
            # high; it's also probably very punitive when the ZODB
            # cache size is too small for the application being used,
            # as disk activity will dwarf any presumed savings.
            scanlimit = self.scan_slope*(float(rlen)/numdocs) + self.scan_icept
            if limit < scanlimit:
                return self.scan_forward(docids, limit)
            elif limit / float(rlen) > self.nbest_percent:
                # the nbest_percent constant compared against limit /
                # float(rlen) above is an educated guess (see
                # http://www.zope.org/Members/Caseman/ZCatalog_for_2.6.1
                # for overall explanation of n-best)
                return self.nbest_ascending(docids, limit)

        return self.bruteforce_ascending(docids, limit)

    def sort_reverse(self, docids, limit, numdocs):

        # for unit testing
        if self.force_nbest:
            return self.nbest_descending(docids, limit)
        elif self.force_brute:
            return self.bruteforce_descending(docids, limit)

        rlen = len(docids)
            
        if limit and ( (limit/float(rlen)) > self.nbest_percent):
            # the nbest_percent constant compared against limit /
            # float(rlen) above is an educated guess (see
            # http://www.zope.org/Members/Caseman/ZCatalog_for_2.6.1
            # for overall explanation of n-best)
            return self.nbest_descending(docids, limit)

        return self.bruteforce_descending(docids, limit)

    def scan_forward(self, docids, limit=None):
        fwd_index = self._fwd_index

        sets = []
        n = 0
        isect = self.family.IF.intersection
        for set in fwd_index.values():
            if set:
                set = isect(docids, set)
            if set:
                for docid in set:
                    n+=1
                    yield docid
                    if limit and n >= limit:
                        raise StopIteration

    def nbest_ascending(self, docids, limit):
        if limit is None:
            raise RuntimeError, 'n-best used without limit'

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
        rev_index = self._rev_index
        iterable = nsort(docids, rev_index)
        for value, docid in heapq.nlargest(limit, iterable):
            yield docid
    
    def bruteforce_ascending(self, docids, limit):
        return self._bruteforce(docids, limit, reverse=False)

    def bruteforce_descending(self, docids, limit):
        return self._bruteforce(docids, limit, reverse=True)

    def _bruteforce(self, docids, limit, reverse):
        rev_index = self._rev_index
        marker = _marker
        n = 0
        for docid in sorted(docids, key=rev_index.get, reverse=reverse):
            if rev_index.get(docid, marker) is not marker:
                # we skip docids that are not in this index (as
                # per Z2 catalog implementation)
                n += 1
                yield docid
                if limit and n >= limit:
                    raise StopIteration

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
                
def nsort(docids, rev_index, marker=_marker):
    for docid in docids:
        val = rev_index.get(docid, marker)
        if val is not marker:
            yield (val, docid)
