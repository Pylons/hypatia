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
"""Text Index Tests
"""
import unittest

_marker = object()

class TextIndexTests(unittest.TestCase):

    def _getTargetClass(self):
        from .. import TextIndex
        return TextIndex

    def _makeOne(self, discriminator=_marker, lexicon=_marker, index=_marker,
                 family=None):
        def _discriminator(obj, default):
            if obj is _marker:
                return default
            return obj
        if discriminator is _marker:
            discriminator = _discriminator
        if lexicon is _marker:
            if index is _marker: # defaults
                return self._getTargetClass()(discriminator=discriminator,
                                              family=family)
            else:
                return self._getTargetClass()(discriminator=discriminator,
                                              index=index, family=family)
        else:
            if index is _marker:
                return self._getTargetClass()(discriminator=discriminator,
                                              lexicon=lexicon, family=family)
            else:
                return self._getTargetClass()(discriminator=discriminator,
                                              lexicon=lexicon,
                                              index=index,
                                              family=family)

    def test_class_conforms_to_IIndexStatistics(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IIndexStatistics
        verifyClass(IIndexStatistics, self._getTargetClass())

    def test_instance_conforms_to_IIndexStatistics(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IIndexStatistics
        verifyObject(IIndexStatistics, self._makeOne())

    def test_class_conforms_to_IIndex(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IIndex
        verifyClass(IIndex, self._getTargetClass())

    def test_instance_conforms_to_IIndex(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IIndex
        verifyObject(IIndex, self._makeOne())

    def test_class_conforms_to_IIndexSort(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IIndexSort
        verifyClass(IIndexSort, self._getTargetClass())

    def test_instance_conforms_to_IIndexSort(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IIndexSort
        verifyObject(IIndexSort, self._makeOne())

    def test_document_repr(self):
        doc = "simple document contains five words"
        index = self._makeOne()
        index.index_doc(1, doc)
        self.assertEqual(
            index.document_repr(1),
            'simple document contains five words'
            )
        self.assertEqual(
            index.document_repr(50), None
            )

    def test_ctor_defaults(self):
        index = self._makeOne()
        from ..lexicon import CaseNormalizer
        from ..lexicon import Lexicon
        from ..lexicon import Splitter
        from ..lexicon import StopWordRemover
        from ..okapiindex import OkapiIndex
        self.failUnless(isinstance(index.index, OkapiIndex))
        self.failUnless(isinstance(index.lexicon, Lexicon))
        self.failUnless(index.index._lexicon is index.lexicon)
        pipeline = index.lexicon._pipeline
        self.assertEqual(len(pipeline), 3)
        self.failUnless(isinstance(pipeline[0], Splitter))
        self.failUnless(isinstance(pipeline[1], CaseNormalizer))
        self.failUnless(isinstance(pipeline[2], StopWordRemover))

    def test_ctor_explicit_lexicon(self):
        from ..okapiindex import OkapiIndex
        lexicon = object()
        index = self._makeOne(lexicon=lexicon)
        self.failUnless(index.lexicon is lexicon)
        self.failUnless(isinstance(index.index, OkapiIndex))
        self.failUnless(index.index._lexicon is lexicon)

    def test_ctor_explicit_family(self):
        import BTrees
        index = self._makeOne(family=BTrees.family32)
        self.failUnless(index.family is BTrees.family32)

    def test_ctor_explicit_index(self):
        lexicon = object()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(index=okapi)
        self.failUnless(index.index is okapi)
        # See LP #232516
        self.failUnless(index.lexicon is lexicon)

    def test_ctor_explicit_lexicon_and_index(self):
        lexicon = object()
        okapi = DummyIndex()
        index = self._makeOne(lexicon=lexicon, index=okapi)
        self.failUnless(index.lexicon is lexicon)
        self.failUnless(index.index is okapi)

    def test_ctor_callback_discriminator(self):
        def _discriminator(obj, default):
            """ """
        index = self._makeOne(discriminator=_discriminator)
        self.failUnless(index.discriminator is _discriminator)

    def test_ctor_string_discriminator(self):
        index = self._makeOne(discriminator='abc')
        self.assertEqual(index.discriminator, 'abc')

    def test_ctor_bad_discriminator(self):
        self.assertRaises(ValueError, self._makeOne, object())

    def test_index_doc(self):
        lexicon = object()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(lexicon=lexicon, index=okapi)
        index.index_doc(1, 'cats and dogs')
        self.assertEqual(okapi._indexed[0], (1, 'cats and dogs'))

    def test_index_doc_then_missing_value(self):
        index = self._makeOne()
        index.index_doc(3, u'Am I rich yet?')
        self.assertEqual(set([3]), set(index.applyContains('rich')))
        self.failUnless(3 in index.docids())
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq('rich')))
        self.failUnless(3 in index.docids())

    def test_index_doc_missing_value_then_with_value(self):
        index = self._makeOne()
        index.index_doc(20, _marker)
        self.assertEqual(set(), set(index.applyContains('rich')))
        self.failUnless(20 in index.docids())
        index.index_doc(20, u'Am I rich yet?')
        self.assertEqual(set([20]), set(index.applyContains('rich')))
        self.failUnless(20 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        index = self._makeOne()
        index.index_doc(20, _marker)
        self.assertEqual(set(), set(index.applyEq('/cmr')))
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.assertEqual(set(), set(index.applyEq('/cmr')))
        self.failIf(20 in index.docids())

    def test_unindex_doc(self):
        lexicon = object()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(lexicon=lexicon, index=okapi)
        index.unindex_doc(1)
        self.assertEqual(okapi._unindexed[0], 1)

    def test_unindex_doc_removes_from_docids(self):
        index = self._makeOne()
        index.index_doc(20, _marker)
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_reindex_doc_doesnt_unindex(self):
        index = self._makeOne()
        index.index_doc(5, 'now is the time')
        index.unindex_doc = lambda *args, **kw: 1/0
        index.reindex_doc(5, 'now is the time')

    def test_reset(self):
        lexicon = object()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(lexicon=lexicon, index=okapi)
        index.reset()
        self.failUnless(okapi._cleared)

    def test_indexed_count(self):
        lexicon = object()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(lexicon=lexicon, index=okapi)
        self.assertEqual(index.indexed_count(), 4)

    def test_word_count(self):
        lexicon = object()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(lexicon=lexicon, index=okapi)
        self.assertEqual(index.word_count(), 45)

    def test_apply_no_results(self):
        lexicon = DummyLexicon()
        okapi = DummyOkapi(lexicon, {})
        index = self._makeOne(lexicon=lexicon, index=okapi)
        self.assertEqual(index.apply('anything'), {})
        self.assertEqual(okapi._query_weighted, [])
        self.assertEqual(okapi._searched, ['anything'])

    def test_apply_w_results(self):
        lexicon = DummyLexicon()
        okapi = DummyOkapi(lexicon)
        index = self._makeOne(lexicon=lexicon, index=okapi)
        results = index.apply('anything')
        self.assertEqual(results[1], 14.0 / 42.0)
        self.assertEqual(results[2], 7.4 / 42.0)
        self.assertEqual(results[3], 3.2 / 42.0)
        self.assertEqual(okapi._query_weighted[0], ['anything'])
        self.assertEqual(okapi._searched, ['anything'])

    def test_apply_w_results_zero_query_weight(self):
        lexicon = DummyLexicon()
        okapi = DummyOkapi(lexicon)
        okapi._query_weight = 0
        index = self._makeOne(lexicon=lexicon, index=okapi)
        results = index.apply('anything')
        self.assertEqual(results[1], 14.0)
        self.assertEqual(results[2], 7.4)
        self.assertEqual(results[3], 3.2)
        self.assertEqual(okapi._query_weighted[0], ['anything'])
        self.assertEqual(okapi._searched, ['anything'])

    def test_apply_w_results_bogus_query_weight(self):
        import sys
        DIVISOR = sys.maxint / 10
        lexicon = DummyLexicon()
        # cause TypeError in division
        okapi = DummyOkapi(lexicon, {1: '14.0', 2: '7.4', 3: '3.2'})
        index = self._makeOne(lexicon=lexicon, index=okapi)
        results = index.apply('anything')
        self.assertEqual(results[1], DIVISOR)
        self.assertEqual(results[2], DIVISOR)
        self.assertEqual(results[3], DIVISOR)
        self.assertEqual(okapi._query_weighted[0], ['anything'])
        self.assertEqual(okapi._searched, ['anything'])

    def test_applyNotContains(self):
        index = self._makeOne()
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        result = sorted(index.applyNotContains('time'))
        self.assertEqual(result, [2])

    def test_applyNotContains_with_unindexed_doc(self):
        def discriminator(obj, default):
            if isinstance(obj, basestring):
                return obj
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        index.index_doc(3, 3)
        result = sorted(index.applyNotContains('time'))
        self.assertEqual(result, [2, 3])

    def test_applyNotContains_nothing_indexed(self):
        def discriminator(obj, default):
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        index.index_doc(3, 3)
        result = sorted(index.applyNotContains('time'))
        self.assertEqual(result, [1, 2, 3])
        
    def test_sort_no_results(self):
        index = self._makeOne()
        self.assertEqual([], index.sort([]))

    def test_sort_without_weights(self):
        index = self._makeOne()
        self.assertRaises(TypeError, index.sort, [1])

    def test_sort_unlimited_forward(self):
        index = self._makeOne()
        results = {-2: 5.0, 3: 3.0, 0: 4.5}
        expect = [-2, 0, 3]
        self.assertEqual(index.sort(results), expect)

    def test_sort_unlimited_reverse(self):
        index = self._makeOne()
        results = {-2: 5.0, 3: 3.0, 0: 4.5}
        expect = [3, 0, -2]
        self.assertEqual(index.sort(results, reverse=True), expect)

    def test_sort_limited(self):
        index = self._makeOne()
        results = {-2: 5.0, 3: 3.0, 0: 4.5}
        expect = [-2, 0]
        self.assertEqual(index.sort(results, limit=2), expect)

    def test_docids(self):
        index = self._makeOne()
        index.index_doc(1, u'now is the time')
        index.index_doc(2, u"l'ora \xe9 ora")
        index.index_doc(3, u"you have nice hair.")
        self.assertEqual(set(index.docids()), set((1, 2, 3)))

    def test_docids_with_indexed_and_not_indexed(self):
        index = self._makeOne()
        index.index_doc(1, u'Am I rich yet?')
        index.index_doc(2, _marker)
        self.assertEqual(set([1, 2]), set(index.docids()))

    def test_contains(self):
        from .. import query
        index = self._makeOne()
        result = index.contains(1)
        self.assertEqual(result.__class__, query.Contains)
        self.assertEqual(result._value, 1)
        
    def test_notcontains(self):
        from .. import query
        index = self._makeOne()
        result = index.notcontains(1)
        self.assertEqual(result.__class__, query.NotContains)
        self.assertEqual(result._value, 1)

    def test_eq(self):
        from .. import query
        index = self._makeOne()
        result = index.eq(1)
        self.assertEqual(result.__class__, query.Contains)
        self.assertEqual(result._value, 1)
        
    def test_noteq(self):
        from .. import query
        index = self._makeOne()
        result = index.noteq(1)
        self.assertEqual(result.__class__, query.NotContains)
        self.assertEqual(result._value, 1)

class DummyOkapi:

    _cleared = False
    _document_count = 4
    _word_count = 45
    _query_weight = 42.0

    def __init__(self, lexicon, search_results=None):
        self.lexicon = lexicon
        self._indexed = []
        self._unindexed = []
        self._searched = []
        self._query_weighted = []
        if search_results is None:
            search_results = {1: 14.0, 2: 7.4, 3: 3.2}
        self._search_results = search_results

    def index_doc(self, docid, text):
        self._indexed.append((docid, text))

    def unindex_doc(self, docid):
        self._unindexed.append(docid)

    def reset(self):
        self._cleared = True

    def indexed_count(self):
        return self._document_count

    def word_count(self):
        return self._word_count

    def query_weight(self, terms):
        self._query_weighted.append(terms)
        return self._query_weight

    def search(self, term):
        self._searched.append(term)
        return self._search_results

    search_phrase = search_glob = search

class DummyLexicon:
    def parseTerms(self, term):
        return term

class DummyIndex:
    def reset(self):
        self.cleared = True

