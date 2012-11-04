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
"""Abstract base class for full text index with relevance ranking.
"""
import math

from persistent import Persistent
from zope.interface import implementer

import BTrees
from BTrees import Length
from BTrees.IOBTree import IOBTree

from ..interfaces import (
    IIndexInjection,
    IIndexStatistics,
    )
from .interfaces import (
    IExtendedQuerying,
    ILexiconBasedIndex,
    )
from . import widcode
from .setops import (
    mass_weightedIntersection,
    mass_weightedUnion,
    )

@implementer(
    IIndexInjection,
    IIndexStatistics,
    ILexiconBasedIndex,
    IExtendedQuerying
    )
class BaseIndex(Persistent):

    family = BTrees.family64

    lexicon = property(lambda self: self._lexicon,)

    def __init__(self, lexicon, family=None):
        if family is not None:
            self.family = family
        self._lexicon = lexicon
        self.reset()

    def reset(self):
        # wid -> {docid -> weight}; t -> D -> w(D, t)
        # Different indexers have different notions of term weight, but we
        # expect each indexer to use ._wordinfo to map wids to its notion
        # of a docid-to-weight map.
        # There are two kinds of OOV words:  wid 0 is explicitly OOV,
        # and it's possible that the lexicon will return a non-zero wid
        # for a word we don't currently know about.  For example, if we
        # unindex the last doc containing a particular word, that wid
        # remains in the lexicon, but is no longer in our _wordinfo map;
        # lexicons can also be shared across indices, and some other index
        # may introduce a lexicon word we've never seen.
        # A word is in-vocabulary for this index if and only if
        # _wordinfo.has_key(wid).  Note that wid 0 must not be a key.
        # This does not use the BTree family since wids are always "I"
        # flavor trees.
        self._wordinfo = IOBTree()

        # docid -> weight
        # Different indexers have different notions of doc weight, but we
        # expect each indexer to use ._docweight to map docids to its
        # notion of what a doc weight is.
        self._docweight = self.family.IF.BTree()

        # docid -> WidCode'd list of wids
        # Used for un-indexing, and for phrase search.
        self._docwords = self.family.IO.BTree()

        # Use a BTree length for efficient length computation w/o conflicts
        self.word_count = Length.Length()
        self.indexed_count = Length.Length()

    def word_count(self):
        """Return the number of words in the index."""
        # This must be overridden by subclasses which do not set the
        # attribute on their instances.
        raise NotImplementedError

    def indexed_count(self):
        """Return the number of documents in the index."""
        # This must be overridden by subclasses which do not set the
        # attribute on their instances.
        raise NotImplementedError

    def get_words(self, docid):
        """Return a list of the wordids for a given docid."""
        return widcode.decode(self._docwords[docid])

    def document_repr(self, docid, default=None):
        try:
            words = []
            wids = self.get_words(docid)
            for wid in wids:
                words.append(self._lexicon.get_word(wid))
            return str(' '.join(words))
        except KeyError:
            return default

    # A subclass may wish to extend or override this.
    def index_doc(self, docid, text):
        if docid in self._docwords:
            return self.reindex_doc(docid, text)
        wids = self._lexicon.sourceToWordIds(text)
        wid2weight, docweight = self._get_frequencies(wids)
        self._mass_add_wordinfo(wid2weight, docid)
        self._docweight[docid] = docweight
        self._docwords[docid] = widcode.encode(wids)
        try:
            self.indexed_count.change(1)
        except AttributeError:
            # upgrade indexed_count to Length object
            self.indexed_count = Length.Length(len(self._docweight))
        return len(wids)

    # A subclass may wish to extend or override this.  This is for adjusting
    # to a new version of a doc that already exists.  The goal is to be
    # faster than simply unindexing the old version in its entirety and then
    # adding the new version in its entirety.
    def reindex_doc(self, docid, text):
        # Touch as few docid->w(docid, score) maps in ._wordinfo as possible.
        old_wids = self.get_words(docid)
        old_wid2w, old_docw = self._get_frequencies(old_wids)

        new_wids = self._lexicon.sourceToWordIds(text)
        new_wid2w, new_docw = self._get_frequencies(new_wids)

        old_widset = self.family.IF.TreeSet(old_wid2w.keys())
        new_widset = self.family.IF.TreeSet(new_wid2w.keys())

        IF = self.family.IF
        in_both_widset = IF.intersection(old_widset, new_widset)
        only_old_widset = IF.difference(old_widset, in_both_widset)
        only_new_widset = IF.difference(new_widset, in_both_widset)
        del old_widset, new_widset

        for wid in only_old_widset.keys():
            self._del_wordinfo(wid, docid)

        for wid in only_new_widset.keys():
            self._add_wordinfo(wid, new_wid2w[wid], docid)

        for wid in in_both_widset.keys():
            # For the Okapi indexer, the "if" will trigger only for words
            # whose counts have changed.  For the cosine indexer, the "if"
            # may trigger for every wid, since W(d) probably changed and
            # W(d) is divided into every score.
            newscore = new_wid2w[wid]
            if old_wid2w[wid] != newscore:
                self._add_wordinfo(wid, newscore, docid)

        self._docweight[docid] = new_docw
        self._docwords[docid] = widcode.encode(new_wids)
        return len(new_wids)

    # Subclass must override.
    def _get_frequencies(self, wids):
        # Compute term frequencies and a doc weight, whatever those mean
        # to an indexer.
        # Return pair:
        #    {wid0: w(d, wid0), wid1: w(d, wid1),  ...],
        #    docweight
        # The wid->weight mappings are fed into _add_wordinfo, and docweight
        # becomes the value of _docweight[docid].
        raise NotImplementedError

    def has_doc(self, docid):
        return docid in self._docwords

    # A subclass may wish to extend or override this.
    def unindex_doc(self, docid):
        if docid not in self._docwords:
            return
        for wid in self.family.IF.TreeSet(self.get_words(docid)).keys():
            self._del_wordinfo(wid, docid)
        del self._docwords[docid]
        del self._docweight[docid]
        try:
            self.indexed_count.change(-1)
        except AttributeError:
            # upgrade indexed_count to Length object
            self.indexed_count = Length.Length(len(self._docweight))

    def search(self, term):
        wids = self._lexicon.termToWordIds(term)
        if not wids:
            return None # All docs match
        wids = self._remove_oov_wids(wids)
        return mass_weightedUnion(self._search_wids(wids), self.family)

    def search_glob(self, pattern):
        wids = self._lexicon.globToWordIds(pattern)
        wids = self._remove_oov_wids(wids)
        return mass_weightedUnion(self._search_wids(wids), self.family)

    def search_phrase(self, phrase):
        wids = self._lexicon.termToWordIds(phrase)
        cleaned_wids = self._remove_oov_wids(wids)
        if len(wids) != len(cleaned_wids):
            # At least one wid was OOV:  can't possibly find it.
            return self.family.IF.BTree()
        scores = self._search_wids(wids)
        hits = mass_weightedIntersection(scores, self.family)
        if not hits:
            return hits
        code = widcode.encode(wids)
        result = self.family.IF.BTree()
        for docid, weight in hits.items():
            docwords = self._docwords[docid]
            if docwords.find(code) >= 0:
                result[docid] = weight
        return result

    def _remove_oov_wids(self, wids):
        return filter(self._wordinfo.has_key, wids)

    # Subclass must override.
    # The workhorse.  Return a list of (IFBucket, weight) pairs, one pair
    # for each wid t in wids.  The IFBucket, times the weight, maps D to
    # TF(D,t) * IDF(t) for every docid D containing t.  wids must not
    # contain any OOV words.
    def _search_wids(self, wids):
        raise NotImplementedError

    # Subclass must override.
    # It's not clear what it should do.  It must return an upper bound on
    # document scores for the query.  It would be nice if a document score
    # divided by the query's query_weight gave the proabability that a
    # document was relevant, but nobody knows how to do that.  For
    # CosineIndex, the ratio is the cosine of the angle between the document
    # and query vectors.  For OkapiIndex, the ratio is a (probably
    # unachievable) upper bound with no "intuitive meaning" beyond that.
    def query_weight(self, terms):
        raise NotImplementedError

    DICT_CUTOFF = 10

    def _add_wordinfo(self, wid, f, docid):
        # Store a wordinfo in a dict as long as there are less than
        # DICT_CUTOFF docids in the dict.  Otherwise use an IFBTree.

        # The pickle of a dict is smaller than the pickle of an
        # IFBTree, substantially so for small mappings.  Thus, we use
        # a dictionary until the mapping reaches DICT_CUTOFF elements.

        # The cutoff is chosen based on the implementation
        # characteristics of Python dictionaries.  The dict hashtable
        # always has 2**N slots and is resized whenever it is 2/3s
        # full.  A pickled dict with 10 elts is half the size of an
        # IFBTree with 10 elts, and 10 happens to be 2/3s of 2**4.  So
        # choose 10 as the cutoff for now.

        # The IFBTree has a smaller in-memory representation than a
        # dictionary, so pickle size isn't the only consideration when
        # choosing the threshold.  The pickle of a 500-elt dict is 92%
        # of the size of the same IFBTree, but the dict uses more
        # space when it is live in memory.  An IFBTree stores two C
        # arrays of ints, one for the keys and one for the values.  It
        # holds up to 120 key-value pairs in a single bucket.
        doc2score = self._wordinfo.get(wid)
        if doc2score is None:
            doc2score = {} # XXX Holy ConflictError, Batman!
            try:
                self.word_count.change(1)
            except AttributeError:
                # upgrade word_count to Length object
                self.word_count = Length.Length(len(self._wordinfo))
                self.word_count.change(1)
        else:
            # _add_wordinfo() is called for each update.  If the map
            # size exceeds the DICT_CUTOFF, convert to an IFBTree.
            # Obscure:  First check the type.  If it's not a dict, it
            # can't need conversion, and then we can avoid an expensive
            # len(IFBTree).
            if (isinstance(doc2score, type({})) and
                len(doc2score) == self.DICT_CUTOFF):
                doc2score = self.family.IF.BTree(doc2score)
        doc2score[docid] = f
        self._wordinfo[wid] = doc2score # not redundant:  Persistency!

    #    self._mass_add_wordinfo(wid2weight, docid)
    #
    # is the same as
    #
    #    for wid, weight in wid2weight.items():
    #        self._add_wordinfo(wid, weight, docid)
    #
    # except that _mass_add_wordinfo doesn't require so many function calls.
    def _mass_add_wordinfo(self, wid2weight, docid):
        dicttype = type({})
        get_doc2score = self._wordinfo.get
        new_word_count = 0
        for wid, weight in wid2weight.items():
            doc2score = get_doc2score(wid)
            if doc2score is None:
                doc2score = {}
                new_word_count += 1
            elif (isinstance(doc2score, dicttype) and
                  len(doc2score) == self.DICT_CUTOFF):
                doc2score = self.family.IF.BTree(doc2score)
            doc2score[docid] = weight
            self._wordinfo[wid] = doc2score # not redundant:  Persistency!
        try:
            self.word_count.change(new_word_count)
        except AttributeError:
            # upgrade word_count to Length object
            self.word_count = Length.Length(len(self._wordinfo))

    def _del_wordinfo(self, wid, docid):
        doc2score = self._wordinfo[wid]
        del doc2score[docid]
        if doc2score:
            self._wordinfo[wid] = doc2score # not redundant:  Persistency!
        else:
            del self._wordinfo[wid]
            try:
                self.word_count.change(-1)
            except AttributeError:
                # upgrade word_count to Length object
                self.word_count = Length.Length(len(self._wordinfo))

def inverse_doc_frequency(term_count, num_items):
    """Return the inverse doc frequency for a term,

    that appears in term_count items in a collection with num_items
    total items.
    """
    # implements IDF(q, t) = log(1 + N/f(t))
    return math.log(1.0 + float(num_items) / term_count)
