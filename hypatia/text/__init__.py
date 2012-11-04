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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Text index.
"""
import sys

from persistent import Persistent
from zope.interface import implementer

from hypatia.interfaces import (
    IIndex,
    IIndexStatistics,
    IIndexSort,
    )

from .lexicon import (
    CaseNormalizer,
    Lexicon,
    Splitter,
    StopWordRemover,
    )
from .okapiindex import OkapiIndex
from .queryparser import QueryParser

from ..util import BaseIndexMixin 
from .. import query

_marker = object()

@implementer(
    IIndex,
    IIndexSort,
    IIndexStatistics
    )
class TextIndex(BaseIndexMixin, Persistent):
    def __init__(self, discriminator, lexicon=None, index=None,
                 family=None):
        if family is not None:
            self.family = family
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        _explicit_lexicon = True
        if lexicon is None:
            _explicit_lexicon = False
            lexicon = Lexicon(Splitter(), CaseNormalizer(), StopWordRemover())
        if index is None:
            index = OkapiIndex(lexicon, family=self.family) # override family
        self.lexicon = _explicit_lexicon and lexicon or index.lexicon
        self.index = index
        self.reset()

    def reset(self):
        self._not_indexed = self.family.IF.TreeSet()
        self.index.reset()

    def document_repr(self, docid, default=None):
        return self.index.document_repr(docid, default)

    def index_doc(self, docid, obj):
        text = self.discriminate(obj, _marker)

        if text is _marker:
            # unindex the previous value
            self.unindex_doc(docid)
            # Store docid in set of unindexed docids
            self._not_indexed.add(docid)
            return None

        if docid in self._not_indexed:
            # Remove from set of unindexed docs if it was in there.
            self._not_indexed.remove(docid)

        self.index.index_doc(docid, text)

    def unindex_doc(self, docid):
        _not_indexed = self._not_indexed
        if docid in _not_indexed:
            _not_indexed.remove(docid)
        self.index.unindex_doc(docid)

    def reindex_doc(self, docid, object):
        # index_doc knows enough about reindexing to do the right thing
        return self.index_doc(docid, object)

    def indexed(self):
        return self.index._docwords.keys()

    def indexed_count(self):
        return self.index.indexed_count()

    def not_indexed(self):
        return self._not_indexed

    def word_count(self):
        """Return the number of words in the index."""
        return self.index.word_count()

    def apply(self, querytext, start=0, count=None):
        parser = QueryParser(self.lexicon)
        tree = parser.parseQuery(querytext)
        results = tree.executeQuery(self.index)
        if results:
            qw = self.index.query_weight(tree.terms())
            
            # Hack to avoid ZeroDivisionError
            if qw == 0:
                qw = 1.0

            qw *= 1.0

            for docid, score in results.iteritems():
                try:
                    results[docid] = score/qw
                except TypeError:
                    # We overflowed the score, perhaps wildly unlikely.
                    # Who knows.
                    results[docid] = sys.maxint/10

        return results
 
    def applyContains(self, value):
        return self.apply(value)

    def contains(self, value):
        return query.Contains(self, value)

    def applyNotContains(self, *args, **kw):
        return self._negate(self.applyContains, *args, **kw)

    def notcontains(self, value):
        return query.NotContains(self, value)

    applyEq = applyContains
    eq = contains

    applyNotEq = applyNotContains
    noteq = notcontains

    def sort(self, result, reverse=False, limit=None, sort_type=None):
        """Sort by text relevance.

        This only works if the query includes at least one text query,
        leading to a weighted result.  This method raises TypeError
        if the result is not weighted.

        A weighted result is a dictionary-ish object that has docids
        as keys and floating point weights as values.  This method
        sorts the dictionary by weight and returns the sorted
        docids as a list.
        """
        if not result:
            return result

        if not hasattr(result, 'items'):
            raise TypeError(
                "Unable to sort by relevance because the search "
                "result does not contain weights. To produce a weighted "
                "result, include a text search in the query.")

        items = [(weight, docid) for (docid, weight) in result.items()]
        # when reverse is false, output largest weight first.
        # when reverse is true, output smallest weight first.
        items.sort(reverse=not reverse)
        result = [docid for (weight, docid) in items]
        if limit:
            result = result[:limit]
        return result
    
