##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""A sorting mixin class for FieldIndex-like indexes.
"""
import heapq
import bisect
from itertools import islice

from zope.interface import implementer
from hypatia.interfaces import IIndexSort

@implementer(IIndexSort)
class SortingIndexMixin(object):

    _sorting_num_docs_attr = '_num_docs'   # Length object
    _sorting_fwd_index_attr = '_fwd_index' # forward BTree index
    _sorting_rev_index_attr = '_rev_index' # reverse BTree index

    def sort(self, docids, reverse=False, limit=None):
        if (limit is not None) and (limit < 1):
            raise ValueError('limit value must be 1 or greater')

        numdocs = getattr(self, self._sorting_num_docs_attr).value
        if not numdocs:
            raise StopIteration

        if not isinstance(docids,
                          (self.family.IF.Set, self.family.IF.TreeSet)):
            docids = self.family.IF.Set(docids)
        if not docids:
            raise StopIteration

        rlen = len(docids)

        fwd_index = getattr(self, self._sorting_fwd_index_attr)
        rev_index = getattr(self, self._sorting_rev_index_attr)
        getValue = rev_index.get
        marker = object()

        # use_lazy and use_nbest computations lifted wholesale from
        # Zope2 catalog without questioning reasoning
        use_lazy = rlen > numdocs * (rlen / 100 + 1)
        use_nbest = limit and limit * 4 < rlen

        # overrides for unit tests
        if getattr(self, '_use_lazy', False):
            use_lazy = True
        if getattr(self, '_use_nbest', False):
            use_nbest = True
        
        if use_nbest:
            # this is a sort with a limit that appears useful, try to
            # take advantage of the fact that we can keep a smaller
            # set of simultaneous values in memory; use generators
            # and heapq functions to do so.

            def nsort():
                for docid in docids:
                    val = getValue(docid, marker)
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
                for val in result:
                    yield val[1]

        else:
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
                    for docid in self.family.IF.intersection(docids,
                                                             stored_docids):
                        n += 1
                        yield docid
                        if limit and n >= limit:
                            raise StopIteration
            else:
                # If the result set is not much larger than the number
                # of documents in this index, or if we need to sort in
                # reverse order, use a non-lazy sort.
                n = 0
                for docid in sorted(docids, key=getValue, reverse=reverse):
                    if getValue(docid, marker) is not marker:
                        n += 1
                        yield docid
                        if limit and n >= limit:
                            raise StopIteration
