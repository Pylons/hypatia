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
"""Lexicon
"""
import re

from zope.interface import implementer

from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.Length import Length

from persistent import Persistent

from .interfaces import ILexicon
from .interfaces import IPipelineElement
from .interfaces import ISplitter
from .stopdict import get_stopdict
from .parsetree import QueryError
from .._compat import u


@implementer(ILexicon)
class Lexicon(Persistent):

    def __init__(self, *pipeline):
        self._wids = OIBTree()  # word -> wid
        self._words = IOBTree() # wid -> word
        # wid 0 is reserved for words that aren't in the lexicon (OOV -- out
        # of vocabulary).  This can happen, e.g., if a query contains a word
        # we never saw before, and that isn't a known stopword (or otherwise
        # filtered out).  Returning a special wid value for OOV words is a
        # way to let clients know when an OOV word appears.
        self.word_count = Length()
        self._pipeline = pipeline

    def word_count(self):
        """Return the number of unique terms in the lexicon."""
        # overridden per instance
        return len(self._wids)

    def words(self):
        return self._wids.keys()

    def wids(self):
        return self._words.keys()

    def items(self):
        return self._wids.items()

    def sourceToWordIds(self, text):
        if text is None:
            text = ''
        last = _text2list(text)
        for element in self._pipeline:
            last = element.process(last)
        if not isinstance(self.word_count, Length):
            # Make sure word_count is overridden with a BTrees.Length.Length
            self.word_count = Length(self.word_count())        
        # Strategically unload the length value so that we get the most
        # recent value written to the database to minimize conflicting wids
        # Because length is independent, this will load the most
        # recent value stored, regardless of whether MVCC is enabled
        self.word_count._p_deactivate()
        return [self._getWordIdCreate(x) for x in last]

    def termToWordIds(self, text):
        last = _text2list(text)
        for element in self._pipeline:
            last = element.process(last)
        wids = []
        for word in last:
            wids.append(self._wids.get(word, 0))
        return wids

    def parseTerms(self, text):
        last = _text2list(text)
        for element in self._pipeline:
            process = getattr(element, "processGlob", element.process)
            last = process(last)
        return last

    def isGlob(self, word):
        return "*" in word or "?" in word

    def get_word(self, wid):
        return self._words[wid]

    def get_wid(self, word):
        return self._wids.get(word, 0)

    def globToWordIds(self, pattern):
        # Implement * and ? just as in the shell, except the pattern
        # must not start with either of these
        prefix = ""
        while pattern and pattern[0] not in "*?":
            prefix += pattern[0]
            pattern = pattern[1:]
        if not pattern:
            # There were no globbing characters in the pattern
            wid = self._wids.get(prefix, 0)
            if wid:
                return [wid]
            else:
                return []
        if not prefix:
            # The pattern starts with a globbing character.
            # This is too efficient, so we raise an exception.
            raise QueryError(
                "pattern %r shouldn't start with glob character" % pattern)
        pat = prefix
        for c in pattern:
            if c == "*":
                pat += ".*"
            elif c == "?":
                pat += "."
            else:
                pat += re.escape(c)
        pat += "$"
        prog = re.compile(pat)
        keys = self._wids.keys(prefix) # Keys starting at prefix
        wids = []
        for key in keys:
            if not key.startswith(prefix):
                break
            if prog.match(key):
                wids.append(self._wids[key])
        return wids

    def _getWordIdCreate(self, word):
        wid = self._wids.get(word)
        if wid is None:
            wid = self._new_wid()
            self._wids[word] = wid
            self._words[wid] = word
        return wid

    def _new_wid(self):
        count = self.word_count
        count.change(1)
        while count() in self._words:
            # just to be safe
            count.change(1)
        return count()

def _text2list(text):
    # Helper: splitter input may be a string or a list of strings
    try:
        text + u('')
    except:
        return text
    else:
        return [text]

# Sample pipeline elements

@implementer(ISplitter)
class Splitter(object):

    rx = re.compile(r"(?u)\w+")
    rxGlob = re.compile(r"(?u)\w+[\w*?]*") # See globToWordIds() above

    def process(self, lst):
        result = []
        for s in lst:
            result += self.rx.findall(s)
        return result

    def processGlob(self, lst):
        result = []
        for s in lst:
            result += self.rxGlob.findall(s)
        return result

@implementer(IPipelineElement)
class CaseNormalizer(object):

    def process(self, lst):
        return [w.lower() for w in lst]

@implementer(IPipelineElement)
class StopWordRemover(object):

    dict = get_stopdict().copy()

    def process(self, lst):
        return [w for w in lst if w not in self.dict]

class StopWordAndSingleCharRemover(StopWordRemover):

    dict = get_stopdict().copy()
    for c in range(255):
        dict[chr(c)] = None
