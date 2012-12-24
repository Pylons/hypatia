##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Field index
"""
import persistent
from BTrees.Length import Length

import bisect
import heapq
from itertools import islice

from zope.interface import implementer

from .. import interfaces
from .. import RangeValue

from ..util import BaseIndexMixin
from .. import query

_marker = []

FWSCAN = 'fwscan'
NBEST = 'nbest'
TIMSORT = 'timsort'

@implementer(
        interfaces.IIndex,
        interfaces.IIndexStatistics,
        )
class FieldIndex(BaseIndexMixin, persistent.Persistent):
    """ Field indexing.

    Query types supported:

    - Eq

    - NotEq

    - Gt

    - Ge

    - Lt

    - Le

    - In

    - NotIn

    - Any

    - NotAny

    - InRange

    - NotInRange
    """

    def __init__(self, discriminator, family=None):
        if family is not None:
            self.family = family
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        self.reset()

    def reset(self):
        """Initialize forward and reverse mappings."""
        # The forward index maps indexed values to a sequence of docids
        self._fwd_index = self.family.OO.BTree()
        # The reverse index maps a docid to its index value
        self._rev_index = self.family.IO.BTree()
        self._num_docs = Length(0)
        self._not_indexed = self.family.IF.TreeSet()

    def not_indexed(self):
        return self._not_indexed

    def not_indexed_count(self):
        return len(self._not_indexed)

    def indexed(self):
        return self._rev_index.keys()

    def indexed_count(self):
        return self._num_docs()

    def word_count(self):
        """See interface IIndexStatistics"""
        return len(self._fwd_index)

    def document_repr(self, docid, default=None):
        result = self._rev_index.get(docid, default)
        if result is not default:
            return repr(result)
        return default

    def index_doc(self, docid, value):
        """See interface IIndexInjection"""
        value = self.discriminate(value, _marker)

        if value is _marker:
            if not (docid in self._not_indexed):
                # unindex the previous value
                self.unindex_doc(docid)
                # Store docid in set of unindexed docids
                self._not_indexed.add(docid)
            return None

        if docid in self._not_indexed:
            # Remove from set of unindexed docs if it was in there.
            self._not_indexed.remove(docid)
        
        rev_index = self._rev_index
        if docid in rev_index:
            if docid in self._fwd_index.get(value, ()):
                # no need to index the doc, its already up to date
                return
            # unindex doc if present
            self.unindex_doc(docid)

        # Insert into forward index.
        set = self._fwd_index.get(value)
        if set is None:
            set = self.family.IF.TreeSet()
            self._fwd_index[value] = set
            
        set.insert(docid)

        # increment doc count
        self._num_docs.change(1)

        # Insert into reverse index.
        rev_index[docid] = value

    def unindex_doc(self, docid):
        """See interface IIndexInjection.
        """
        _not_indexed = self._not_indexed
        if docid in _not_indexed:
            _not_indexed.remove(docid)

        rev_index = self._rev_index
        value = rev_index.get(docid, _marker)
        if value is _marker:
            return # not in index

        del rev_index[docid]

        try:
            set = self._fwd_index[value]
            set.remove(docid)
        except KeyError:    #pragma NO COVERAGE
            # This is fishy, but we don't want to raise an error.
            # We should probably log something.
            # but keep it from throwing a dirty exception
            set = 1

        if not set:
            del self._fwd_index[value]

        self._num_docs.change(-1)

    def reindex_doc(self, docid, value):
        """ See interface IIndexInjection """
        # the base index's index_doc method special-cases a reindex
        return self.index_doc(docid, value)

    def sort(self, docids, reverse=False, limit=None, sort_type=None):
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
            return self.sort_reverse(docids, limit, numdocs, sort_type)
        else:
            return self.sort_forward(docids, limit, numdocs, sort_type)

    def sort_forward(self, docids, limit, numdocs, sort_type=None):

        rlen = len(docids)

        # See http://www.zope.org/Members/Caseman/ZCatalog_for_2.6.1
        # for an overview of why we bother doing all this work to
        # choose the right sort algorithm.

        if sort_type is None:

            if fwscan_wins(limit, rlen, numdocs):
                # forward scan beats both n-best and timsort reliably
                # if this is true
                sort_type = FWSCAN

            elif limit and nbest_ascending_wins(limit, rlen, numdocs):
                # nbest beats timsort reliably if this is true
                sort_type = NBEST

            else:
                sort_type = TIMSORT

        if sort_type == FWSCAN:
            return self.scan_forward(docids, limit)
        elif sort_type == NBEST:
            if limit is None:
                raise ValueError('nbest requires a limit')
            return self.nbest_ascending(docids, limit)
        elif sort_type == TIMSORT:
            return self.timsort_ascending(docids, limit)
        else:
            raise ValueError('Unknown sort type %s' % sort_type)

    def sort_reverse(self, docids, limit, numdocs, sort_type=None):
        if sort_type is None:
            # XXX this needs work.
            rlen = len(docids)
            if limit:
                if (limit < 300) or (limit/float(rlen) > 0.09):
                    sort_type = NBEST
                else:
                    sort_type = TIMSORT
            else:
                sort_type = TIMSORT

        if sort_type == NBEST:
            if limit is None:
                raise ValueError('nbest requires a limit')
            return self.nbest_descending(docids, limit)
        elif sort_type == TIMSORT:
            return self.timsort_descending(docids, limit)
        else:
            raise ValueError('Unknown sort type %s' % sort_type)

    def scan_forward(self, docids, limit=None):
        fwd_index = self._fwd_index

        n = 0
        for set in fwd_index.values():
            for docid in set:
                if docid in docids:
                    n+=1
                    yield docid
                    if limit and n >= limit:
                        raise StopIteration

    def nbest_ascending(self, docids, limit):
        if limit is None: #pragma NO COVERAGE
            raise RuntimeError, 'n-best used without limit'

        # lifted from heapq.nsmallest

        h = nsort(docids, self._rev_index)
        it = iter(h)
        result = sorted(islice(it, 0, limit))
        if not result: #pragma NO COVERAGE
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
        if limit is None: #pragma NO COVERAGE
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

    def search(self, queries, operator='or'):
        sets = []
        for q in queries:
            if isinstance(q, RangeValue):
                q = q.as_tuple()
            else:
                q = (q, q)
            set = self.family.IF.multiunion(self._fwd_index.values(*q))
            sets.append(set)

        result = None

        if len(sets) == 1:
            result = sets[0]
        elif operator == 'and':
            sets.sort()
            for set in sets:
                result = self.family.IF.intersection(set, result)
        else:
            result = self.family.IF.multiunion(sets)

        return result

    def apply(self, q):
        if isinstance(q, dict):
            val = q['query']
            if isinstance(val, RangeValue):
                val = [val]
            elif not isinstance(val, (list, tuple)):
                val = [val]
            operator = q.get('operator', 'or')
            result = self.search(val, operator)
        else:
            if isinstance(q, tuple) and len(q) == 2:
                # b/w compat stupidity; this needs to die
                q = RangeValue(*q)
                q = [q]
            elif not isinstance(q, (list, tuple)):
                q = [q]
            result = self.search(q, 'or')

        return result

    def applyEq(self, value):
        return self.apply(value)

    def eq(self, value):
        return query.Eq(self, value)

    def applyNotEq(self, *args, **kw):
        return self._negate(self.applyEq, *args, **kw)

    def noteq(self, value):
        return query.NotEq(self, value)

    def applyGe(self, min_value):
        return self.applyInRange(min_value, None)

    def ge(self, value):
        return query.Ge(self, value)

    def applyLe(self, max_value):
        return self.applyInRange(None, max_value)

    def le(self, value):
        return query.Le(self, value)

    def applyGt(self, min_value):
        return self.applyInRange(min_value, None, excludemin=True)

    def gt(self, value):
        return query.Gt(self, value)

    def applyLt(self, max_value):
        return self.applyInRange(None, max_value, excludemax=True)

    def lt(self, value):
        return query.Lt(self, value)

    def applyAny(self, values):
        queries = list(values)
        return self.search(queries, operator='or')

    def any(self, value):
        return query.Any(self, value)

    def applyNotAny(self, *args, **kw):
        return self._negate(self.applyAny, *args, **kw)

    def notany(self, value):
        return query.NotAny(self, value)

    def applyInRange(self, start, end, excludemin=False, excludemax=False):
        return self.family.IF.multiunion(
            self._fwd_index.values(
                start, end, excludemin=excludemin, excludemax=excludemax)
        )


    def inrange(self, start, end, excludemin=False, excludemax=False):
        return query.InRange(self, start, end, excludemin, excludemax)

    def applyNotInRange(self, *args, **kw):
        return self._negate(self.applyInRange, *args, **kw)

    def notinrange(self, start, end, excludemin=False, excludemax=False):
        return query.NotInRange(self, start, end, excludemin, excludemax)

def nsort(docids, rev_index):
    for docid in docids:
        try:
            yield (rev_index[docid], docid)
        except KeyError:
            continue


def fwscan_wins(limit, rlen, numdocs):
    """
    Primitive curve-fitting to see if forward scan will beat both
    nbest and timsort for a particular limit/rlen/numdocs tuple.  In
    sortbench tests up to 'numdocs' sizes of 65536, this curve fit had
    a 95%+ accuracy rate, except when 'numdocs' is < 64, then its
    lowest accuracy percentage was 83%.  Thus, it could still use some
    work, but accuracy at very small index sizes is not terribly
    important for the author.
    """
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
        # index, beginning reliably at a docratio of 512/65536.0.  XXX
        # It'd be nice to figure out a more concise way to express
        # this.
        if 512/div <= docratio < 1024/div and limitratio <= 4/div:
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


def nbest_ascending_wins(limit, rlen, numdocs):
    """
    Primitive curve-fitting to see if nbest ascending will beat
    timsort for a particular limit/rlen/numdocs tuple.  XXX This needs
    work, particularly at small index sizes.  It is currently
    optimized for an index size of about 32768 (98% accuracy); it gets
    about 93% accuracy at index size 65536.
    """
    if not limit:
        # n-best can't be used without a limit
        return False
    limitratio = limit / float(numdocs)

    if numdocs <= 768:
        return True

    docratio = rlen / float(numdocs)
    div = 65536.0

    if docratio < 4096/div:
        # nbest tends to win when the rlen is less than about 6% of the
        # numdocs
        return True

    if docratio == 1 and limitratio <= 8192/div:
        return True
    elif 1 > docratio >= 32768/div and limitratio <= 4096/div:
        return True
    elif 32768/div > docratio >= 4096/div and limitratio <= 2048/div:
        return True

    return False


