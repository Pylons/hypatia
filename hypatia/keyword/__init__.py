from zope.interface import implementer

from ..interfaces import (
    IIndex,
    IIndexStatistics,
    )
from ..util import BaseIndexMixin

from persistent import Persistent

from BTrees.Length import Length

from .interfaces import IKeywordQuerying
from .. import query

_marker = object()

@implementer(
    IIndex,
    IIndexStatistics,
    IKeywordQuerying,
    )
class KeywordIndex(BaseIndexMixin, Persistent):
    """
    Keyword index.

    Query types supported:

    - Eq

    - NotEq

    - In

    - NotIn

    - Any

    - NotAny

    - All

    - NotAll

    """

    # If a word is referenced by at least tree_threshold docids,
    # use a TreeSet for that word instead of a Set.
    tree_threshold = 64

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

        # The forward index maps index keywords to a sequence of docids
        self._fwd_index = self.family.OO.BTree()

        # The reverse index maps a docid to its keywords
        # TODO: Using a vocabulary might be the better choice to store
        # keywords since it would allow use to use integers instead of strings
        self._rev_index = self.family.IO.BTree()
        self._num_docs = Length(0)
        self._not_indexed = self.family.IF.TreeSet()

    def reindex_doc(self, docid, value):
        # the base index' index_doc method special-cases a reindex
        return self.index_doc(docid, value)

    def has_doc(self, docid):
        return bool(self._rev_index.has_key(docid))

    def indexed(self):
        return self._rev_index.keys()

    def not_indexed(self):
        return self._not_indexed

    def word_count(self):
        """Return the number of indexed words"""
        return len(self._fwd_index)

    def applyAny(self, values):
        return self.apply({'query': values, 'operator': 'or'})

    def any(self, value):
        return query.Any(self, value)

    def applyNotAny(self, *args, **kw):
        return self._negate(self.applyAny, *args, **kw)

    def notany(self, value):
        return query.NotAny(self, value)

    def applyAll(self, values):
        return self.apply({'query': values, 'operator': 'and'})

    def all(self, value):
        return query.All(self, value)

    def applyNotAll(self, *args, **kw):
        return self._negate(self.applyAll, *args, **kw)

    def notall(self, value):
        return query.NotAll(self, value)

    def applyEq(self, value):
        return self.apply([value])

    def eq(self, value):
        return query.Eq(self, value)

    def applyNotEq(self, *args, **kw):
        return self._negate(self.applyEq, *args, **kw)

    def noteq(self, value):
        return query.NotEq(self, value)

    def normalize(self, seq):
        """Perform normalization on sequence of keywords.

        Return normalized sequence. This method may be
        overriden by subclasses.

        """
        return seq

    def document_repr(self, docid, default=None):
        result = self._rev_index.get(docid, default)
        if result is not default:
            return repr(result)
        return default

    def index_doc(self, docid, obj):
        seq = self.discriminate(obj, _marker)

        if seq is _marker:
            if not (docid in self._not_indexed):
                # unindex the previous value
                self.unindex_doc(docid)
                # Store docid in set of unindexed docids
                self._not_indexed.add(docid)
            return None

        if docid in self._not_indexed:
            # Remove from set of unindexed docs if it was in there.
            self._not_indexed.remove(docid)

        if isinstance(seq, basestring):
            raise TypeError('seq argument must be a list/tuple of strings')

        old_kw = self._rev_index.get(docid, None)
        if not seq:
            if old_kw:
                self.unindex_doc(docid)
            return

        seq = self.normalize(seq)

        new_kw = self.family.OO.Set(seq)

        if old_kw is None:
            self._insert_forward(docid, new_kw)
            self._insert_reverse(docid, new_kw)
            self._num_docs.change(1)
        else:
            # determine added and removed keywords
            kw_added = self.family.OO.difference(new_kw, old_kw)
            kw_removed = self.family.OO.difference(old_kw, new_kw)

            if not (kw_added or kw_removed):
                return

            # removed keywords are removed from the forward index
            for word in kw_removed:
                fwd = self._fwd_index[word]
                fwd.remove(docid)
                if not fwd:
                    del self._fwd_index[word]

            # now update reverse and forward indexes
            self._insert_forward(docid, kw_added)
            self._insert_reverse(docid, new_kw)

    def unindex_doc(self, docid):
        _not_indexed = self._not_indexed
        if docid in _not_indexed:
            _not_indexed.remove(docid)
        
        idx  = self._fwd_index

        try:
            for word in self._rev_index[docid]:
                idx[word].remove(docid)
                if not idx[word]:
                    del idx[word]
        except KeyError:
            msg = 'WAAA!  Inconsistent'
            return

        try:
            del self._rev_index[docid]
        except KeyError: #pragma NO COVERAGE
            msg = 'WAAA!  Inconsistent'

        self._num_docs.change(-1)

    def _insert_forward(self, docid, words):
        """insert a sequence of words into the forward index """

        idx = self._fwd_index
        get_word_idx = idx.get
        IF = self.family.IF
        Set = IF.Set
        TreeSet = IF.TreeSet
        for word in words:
            word_idx = get_word_idx(word)
            if word_idx is None:
                idx[word] = word_idx = Set()
            word_idx.insert(docid)
            if (not isinstance(word_idx, TreeSet) and
                    len(word_idx) >= self.tree_threshold):
                # Convert to a TreeSet.
                idx[word] = TreeSet(word_idx)

    def _insert_reverse(self, docid, words):
        """ add words to forward index """

        if words:
            self._rev_index[docid] = words

    def search(self, query, operator='and'):
        """Execute a search given by 'query'."""
        if isinstance(query, basestring):
            query = [query]

        query = self.normalize(query)

        sets = []
        for word in query:
            docids = self._fwd_index.get(word, self.family.IF.Set())
            sets.append(docids)

        if operator == 'or':
            rs = self.family.IF.multiunion(sets)
        elif operator == 'and':
            # sort smallest to largest set so we intersect the smallest
            # number of document identifiers possible
            sets.sort(key=len)
            rs = None
            for set in sets:
                rs = self.family.IF.intersection(rs, set)
                if not rs:
                    break
        else:
            raise TypeError('Keyword index only supports `and` and `or` '
                            'operators, not `%s`.' % operator)

        if rs:
            return rs
        else:
            return self.family.IF.Set()

    def apply(self, query):
        operator = 'and'
        if isinstance(query, dict):
            if 'operator' in query:
                operator = query['operator']
            query = query['query']
        return self.search(query, operator=operator)

    def optimize(self):
        """Optimize the index. Call this after changing tree_threshold.

        This converts internal data structures between
        Sets and TreeSets based on tree_threshold.
        """
        idx = self._fwd_index
        IF = self.family.IF
        Set = IF.Set
        TreeSet = IF.TreeSet
        items = list(self._fwd_index.items())
        for word, word_idx in items:
            if len(word_idx) >= self.tree_threshold:
                if not isinstance(word_idx, TreeSet):
                    # Convert to a TreeSet.
                    idx[word] = TreeSet(word_idx)
            else:
                if isinstance(word_idx, TreeSet):
                    # Convert to a Set.
                    idx[word] = Set(word_idx)

