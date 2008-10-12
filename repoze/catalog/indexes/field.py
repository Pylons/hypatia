import bisect
import heapq
from itertools import islice

from zope.interface import implements

from zope.index.field import FieldIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

_marker = ()

class CatalogFieldIndex(CatalogIndex, FieldIndex):
    implements(ICatalogIndex)
    use_lazy = False # for unit testing
    use_nbest = False # for unit testing

    def sort(self, docids, reverse=False, limit=None):
        if limit is not None:
            limit = int(limit)
            if limit < 1:
                raise ValueError('limit must be 1 or greater')

        if not docids:
            raise StopIteration
            
        numdocs = self._num_docs.value
        if not numdocs:
            raise StopIteration

        rev_index = self._rev_index
        fwd_index = self._fwd_index

        rlen = len(docids)

        # use_lazy and use_nbest computations lifted wholesale from
        # Zope2 catalog without questioning reasoning
        use_lazy = (rlen > (numdocs * (rlen / 100 + 1)))
        use_nbest = limit and limit * 4 < rlen

        # overrides for unit tests
        if self.use_lazy:
            use_lazy = True
        if self.use_nbest:
            use_nbest = True

        marker = _marker

        if use_nbest:
            # this is a sort with a limit that appears useful, try to
            # take advantage of the fact that we can keep a smaller
            # set of simultaneous values in memory; use generators
            # and heapq functions to do so.
            def nsort():
                for docid in docids:
                    val = rev_index.get(docid, marker)
                    if val is not marker:
                        yield (val, docid)
            iterable = nsort()
            if reverse:
                # we use a generator as an iterable in the reverse
                # sort case because the nlargest implementation does
                # not manifest the whole thing into memory at once if
                # we do so.
                for val in heapq.nlargest(limit, iterable):
                    yield val[1]

            else:
                # lifted from heapq.nsmallest
                it = iter(iterable)
                result = sorted(islice(it, 0, limit))
                if not result:
                    yield StopIteration
                insort = bisect.insort
                pop = result.pop
                los = result[-1]    # los --> Largest of the nsmallest
                for elem in it:
                    if los <= elem:
                        continue
                    insort(result, elem)
                    pop()
                    los = result[-1]
                for val in result:
                    yield val[1]

        else:
            print "use_lazy=%s\treverse=%s" % ( use_lazy, reverse )
            if use_lazy and not reverse:
                # Since this the sort is not reversed, and the number
                # of results in the search result set is much larger
                # than the number of items in this index, we assume it
                # will be fastest to iterate over all of our forward
                # BTree's items instead of using a full sort, as our
                # forward index is already sorted in ascending order
                # by value. The Zope 2 catalog implementation claims
                # that this case is rarely exercised in practice.
                n = 0
                for stored_docids in fwd_index.values():
                    isect = self.family.IF.intersection(docids, stored_docids)
                    for docid in isect:
                        if limit and n >= limit:
                            raise StopIteration
                        n += 1
                        yield docid
            else:
                # If the result set is not much larger than the number
                # of documents in this index, or if we need to sort in
                # reverse order, use a non-lazy sort.
                n = 0
                for docid in sorted(docids, key=rev_index.get, reverse=reverse):
                    if rev_index.get(docid, marker) is not marker:
                        # we skip docids that are not in this index (as
                        # per Z2 catalog implementation)
                        if limit and n >= limit:
                            raise StopIteration
                        n += 1
                        yield docid

    def unindex_doc(self, docid):
        """See interface IInjection; base class overridden to be able
        to index None values """
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

                
