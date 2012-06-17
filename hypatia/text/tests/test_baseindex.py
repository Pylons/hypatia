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

class BaseIndexTestBase:
    # Subclasses must define '_getBTreesFamily'
    def _getTargetClass(self):
        from ..baseindex import BaseIndex
        return BaseIndex

    def _makeOne(self, family=None):
        from ..lexicon import Lexicon
        from ..lexicon import Splitter
        if family is None:
            family = self._getBTreesFamily()
        lexicon = Lexicon(Splitter())
        return self._getTargetClass()(lexicon, family=family)

    def test_class_conforms_to_IInjection(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IInjection
        verifyClass(IInjection, self._getTargetClass())

    def test_instance_conforms_to_IInjection(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IInjection
        verifyObject(IInjection, self._makeOne())

    def test_class_conforms_to_IStatistics(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IStatistics
        verifyClass(IStatistics, self._getTargetClass())

    def test_instance_conforms_to_IStatistics(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IStatistics
        verifyObject(IStatistics, self._makeOne())

    def test_class_conforms_to_ILexiconBasedIndex(self):
        from zope.interface.verify import verifyClass
        from ..interfaces import ILexiconBasedIndex
        verifyClass(ILexiconBasedIndex, self._getTargetClass())

    def test_instance_conforms_to_ILexiconBasedIndex(self):
        from zope.interface.verify import verifyObject
        from ..interfaces import ILexiconBasedIndex
        verifyObject(ILexiconBasedIndex, self._makeOne())

    def test_class_conforms_to_IExtendedQuerying(self):
        from zope.interface.verify import verifyClass
        from ..interfaces import IExtendedQuerying
        verifyClass(IExtendedQuerying, self._getTargetClass())

    def test_instance_conforms_to_IExtendedQuerying(self):
        from zope.interface.verify import verifyObject
        from ..interfaces import IExtendedQuerying
        verifyObject(IExtendedQuerying, self._makeOne())

    def test_empty(self):
        index = self._makeOne()
        self.assertEqual(len(index._wordinfo), 0)
        self.assertEqual(len(index._docweight), 0)
        self.assertEqual(len(index._docwords), 0)
        self.assertEqual(index.wordCount(), 0)
        self.assertEqual(index.documentCount(), 0)
        self.failIf(index.has_doc(1))

    def test_clear_doesnt_lose_family(self):
        import BTrees
        index = self._makeOne(family=BTrees.family64)
        index.clear()
        self.failUnless(index.family is BTrees.family64)

    def test_wordCount_method_raises_NotImplementedError(self):
        class DerviedDoesntSet_wordCount(self._getTargetClass()):
            def __init__(self):
                pass
        index = DerviedDoesntSet_wordCount()
        self.assertRaises(NotImplementedError, index.wordCount)

    def test_documentCount_method_raises_NotImplementedError(self):
        class DerviedDoesntSet_documentCount(self._getTargetClass()):
            def __init__(self):
                pass
        index = DerviedDoesntSet_documentCount()
        self.assertRaises(NotImplementedError, index.documentCount)

    def test_index_doc_simple(self):
        index = self._makeOne()

        # Fake out _get_frequencies, which is supposed to be overridden.
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies

        count = index.index_doc(1, 'one two three')

        self.assertEqual(count, 3)
        self.assertEqual(index.wordCount(), 3)
        self.failUnless(index._lexicon._wids['one'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['two'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['three'] in index._wordinfo)
        self.assertEqual(index.documentCount(), 1)
        self.failUnless(index.has_doc(1))
        self.failUnless(1 in index._docwords)
        self.failUnless(1 in index._docweight)
        wids = index.get_words(1)
        self.assertEqual(len(wids), 3)
        self.failUnless(index._lexicon._wids['one'] in wids)
        self.failUnless(index._lexicon._wids['two'] in wids)
        self.failUnless(index._lexicon._wids['three'] in wids)

    def test_index_doc_existing_docid(self):
        index = self._makeOne()

        # Fake out _get_frequencies, which is supposed to be overridden.
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies

        index.index_doc(1, 'one two three')
        count = index.index_doc(1, 'two three four')

        self.assertEqual(count, 3)
        self.assertEqual(index.wordCount(), 3)
        self.failIf(index._lexicon._wids['one'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['two'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['three'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['four'] in index._wordinfo)
        wids = index.get_words(1)
        self.assertEqual(len(wids), 3)
        self.failIf(index._lexicon._wids['one'] in wids)
        self.failUnless(index._lexicon._wids['two'] in wids)
        self.failUnless(index._lexicon._wids['three'] in wids)
        self.failUnless(index._lexicon._wids['four'] in wids)

    def test_index_doc_upgrades_wordCount_documentCount(self):
        index = self._makeOne()

        # Simulate old instances which didn't have these as attributes
        del index.wordCount
        del index.documentCount

        # Fake out _get_frequencies, which is supposed to be overridden.
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies

        count = index.index_doc(1, 'one two three')

        self.assertEqual(count, 3)
        self.assertEqual(index.wordCount(), 3)
        self.assertEqual(index.documentCount(), 1)

    def test__reindex_doc_identity(self):
        index = self._makeOne()

        # Fake out _get_frequencies, which is supposed to be overridden.
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies

        index.index_doc(1, 'one two three')

        # Don't mutate _wordinfo if no changes
        def _dont_go_here(*args, **kw):
            assert 0
        index._add_wordinfo = index._del_wordinfo = _dont_go_here

        count = index._reindex_doc(1, 'one two three')

        self.assertEqual(count, 3)
        self.assertEqual(index.wordCount(), 3)
        self.failUnless(index._lexicon._wids['one'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['two'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['three'] in index._wordinfo)
        wids = index.get_words(1)
        self.assertEqual(len(wids), 3)
        self.failUnless(index._lexicon._wids['one'] in wids)
        self.failUnless(index._lexicon._wids['two'] in wids)
        self.failUnless(index._lexicon._wids['three'] in wids)

    def test__reindex_doc_disjoint(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        # Fake out _get_frequencies, which is supposed to be overridden.
        index._get_frequencies = _faux_get_frequencies

        index.index_doc(1, 'one two three')
        count = index._reindex_doc(1, 'four five six')

        self.assertEqual(count, 3)
        self.assertEqual(index.wordCount(), 3)
        self.failIf(index._lexicon._wids['one'] in index._wordinfo)
        self.failIf(index._lexicon._wids['two'] in index._wordinfo)
        self.failIf(index._lexicon._wids['three'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['four'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['five'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['six'] in index._wordinfo)
        wids = index.get_words(1)
        self.assertEqual(len(wids), 3)
        self.failIf(index._lexicon._wids['one'] in wids)
        self.failIf(index._lexicon._wids['two'] in wids)
        self.failIf(index._lexicon._wids['three'] in wids)
        self.failUnless(index._lexicon._wids['four'] in wids)
        self.failUnless(index._lexicon._wids['five'] in wids)
        self.failUnless(index._lexicon._wids['six'] in wids)

    def test__reindex_doc_subset(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        # Fake out _get_frequencies, which is supposed to be overridden.
        index._get_frequencies = _faux_get_frequencies

        index.index_doc(1, 'one two three')
        count = index._reindex_doc(1, 'two three')

        self.assertEqual(count, 2)
        self.assertEqual(index.wordCount(), 2)
        self.failIf(index._lexicon._wids['one'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['two'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['three'] in index._wordinfo)
        wids = index.get_words(1)
        self.assertEqual(len(wids), 2)
        self.failIf(index._lexicon._wids['one'] in wids)
        self.failUnless(index._lexicon._wids['two'] in wids)
        self.failUnless(index._lexicon._wids['three'] in wids)

    def test__reindex_doc_superset(self): # TODO
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        # Fake out _get_frequencies, which is supposed to be overridden.
        index._get_frequencies = _faux_get_frequencies

        index.index_doc(1, 'one two three')
        count = index._reindex_doc(1, 'one two three four five six')

        self.assertEqual(count, 6)
        self.assertEqual(index.wordCount(), 6)
        self.failUnless(index._lexicon._wids['one'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['two'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['three'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['four'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['five'] in index._wordinfo)
        self.failUnless(index._lexicon._wids['six'] in index._wordinfo)
        wids = index.get_words(1)
        self.assertEqual(len(wids), 6)
        self.failUnless(index._lexicon._wids['one'] in wids)
        self.failUnless(index._lexicon._wids['two'] in wids)
        self.failUnless(index._lexicon._wids['three'] in wids)
        self.failUnless(index._lexicon._wids['four'] in wids)
        self.failUnless(index._lexicon._wids['five'] in wids)
        self.failUnless(index._lexicon._wids['six'] in wids)

    def test__get_frequencies_raises_NotImplementedError(self):
        index = self._makeOne()
        self.assertRaises(NotImplementedError, index._get_frequencies, ())

    def test_unindex_doc_simple(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        # Fake out _get_frequencies, which is supposed to be overridden.
        index._get_frequencies = _faux_get_frequencies
        index.index_doc(1, 'one two three')
        index.unindex_doc(1)
        self.assertEqual(index.wordCount(), 0)
        self.failIf(index._lexicon._wids['one'] in index._wordinfo)
        self.failIf(index._lexicon._wids['two'] in index._wordinfo)
        self.failIf(index._lexicon._wids['three'] in index._wordinfo)
        self.assertEqual(index.documentCount(), 0)
        self.failIf(index.has_doc(1))
        self.failIf(1 in index._docwords)
        self.failIf(1 in index._docweight)
        self.assertRaises(KeyError, index.get_words, 1)

    def test_unindex_doc_upgrades_wordCount_documentCount(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        # Fake out _get_frequencies, which is supposed to be overridden.
        index._get_frequencies = _faux_get_frequencies
        index.index_doc(1, 'one two three')
        # Simulate old instances which didn't have these as attributes
        del index.wordCount
        del index.documentCount
        index.unindex_doc(1)
        self.assertEqual(index.wordCount(), 0)
        self.failIf(index._lexicon._wids['one'] in index._wordinfo)
        self.failIf(index._lexicon._wids['two'] in index._wordinfo)
        self.failIf(index._lexicon._wids['three'] in index._wordinfo)
        self.assertEqual(index.documentCount(), 0)
        self.failIf(index.has_doc(1))
        self.failIf(1 in index._docwords)
        self.failIf(1 in index._docweight)
        self.assertRaises(KeyError, index.get_words, 1)

    def test_search_w_empty_term(self):
        index = self._makeOne()
        self.assertEqual(index.search(''), None)

    def test_search_w_oov_term(self):
        index = self._makeOne()
        def _faux_search_wids(wids):
            assert len(wids) == 0
            return []
        index._search_wids = _faux_search_wids
        self.assertEqual(dict(index.search('nonesuch')), {})

    def test_search_hit(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies
        def _faux_search_wids(wids):
            assert len(wids) == 1
            assert index._lexicon._wids['hit'] in wids
            result = index.family.IF.Bucket()
            result[1] = 1.0
            return [(result, 1)]
        index._search_wids = _faux_search_wids
        index.index_doc(1, 'hit')
        self.assertEqual(dict(index.search('hit')), {1: 1.0})

    def test_search_glob_w_empty_term(self):
        index = self._makeOne()
        def _faux_search_wids(wids):
            assert len(wids) == 0
            return []
        index._search_wids = _faux_search_wids
        self.assertEqual(dict(index.search_glob('')), {})

    def test_search_glob_w_oov_term(self):
        index = self._makeOne()
        def _faux_search_wids(wids):
            assert len(wids) == 0
            return []
        index._search_wids = _faux_search_wids
        self.assertEqual(dict(index.search_glob('nonesuch*')), {})

    def test_search_glob_hit(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies
        def _faux_search_wids(wids):
            assert len(wids) == 1
            assert index._lexicon._wids['hitter'] in wids
            result = index.family.IF.Bucket()
            result[1] = 1.0
            return [(result, 1)]
        index._search_wids = _faux_search_wids
        index.index_doc(1, 'hitter')
        self.assertEqual(dict(index.search_glob('hit*')), {1: 1.0})

    def test_search_phrase_w_empty_term(self):
        index = self._makeOne()
        def _faux_search_wids(wids):
            assert len(wids) == 0
            return []
        index._search_wids = _faux_search_wids
        self.assertEqual(dict(index.search_phrase('')), {})

    def test_search_phrase_w_oov_term(self):
        index = self._makeOne()
        self.assertEqual(dict(index.search_phrase('nonesuch')), {})

    def test_search_phrase_hit(self):
        index = self._makeOne()
        def _faux_get_frequencies(wids):
            return dict([(y, x) for x, y in enumerate(wids)]), 1
        index._get_frequencies = _faux_get_frequencies
        def _faux_search_wids(wids):
            assert len(wids) == 3
            assert index._lexicon._wids['hit'] in wids
            assert index._lexicon._wids['the'] in wids
            assert index._lexicon._wids['nail'] in wids
            result = index.family.IF.Bucket()
            result[1] = 1.0
            return [(result, 1)]
        index._search_wids = _faux_search_wids
        index.index_doc(1, 'hit the nail on the head')
        self.assertEqual(dict(index.search_phrase('hit the nail')), {1: 1.0})

    def test__search_wids_raises_NotImplementedError(self):
        index = self._makeOne()
        self.assertRaises(NotImplementedError, index._search_wids, ())

    def test_query_weight_raises_NotImplementedError(self):
        index = self._makeOne()
        self.assertRaises(NotImplementedError, index.query_weight, ())

    def test__add_wordinfo_simple(self):
        index = self._makeOne()
        # Simulate old instances which didn't have these as attributes
        index._add_wordinfo(123, 4, 1)
        self.assertEqual(index.wordCount(), 1)
        self.assertEqual(index._wordinfo[123], {1: 4})

    def test__add_wordinfo_upgrades_wordCount(self):
        index = self._makeOne()
        # Simulate old instances which didn't have these as attributes
        del index.wordCount
        index._add_wordinfo(123, 4, 1)
        self.assertEqual(index.wordCount(), 1)

    def test__add_wordinfo_promotes_dict_to_tree_at_DICT_CUTOFF(self):
        index = self._makeOne()
        index.DICT_CUTOFF = 2
        index._add_wordinfo(123, 4, 1)
        index._add_wordinfo(123, 5, 2)
        self.failUnless(isinstance(index._wordinfo[123], dict))
        index._add_wordinfo(123, 6, 3)
        self.failUnless(isinstance(index._wordinfo[123],
                                   index.family.IF.BTree))
        self.assertEqual(dict(index._wordinfo[123]), {1: 4, 2: 5, 3: 6})

    def test__mass_add_wordinfo_promotes_dict_to_tree_at_DICT_CUTOFF(self):
        index = self._makeOne()
        index.DICT_CUTOFF = 2
        index._add_wordinfo(123, 4, 1)
        index._add_wordinfo(123, 5, 2)
        index._mass_add_wordinfo({123: 6, 124: 1}, 3)
        self.failUnless(isinstance(index._wordinfo[123],
                                   index.family.IF.BTree))
        self.assertEqual(dict(index._wordinfo[123]), {1: 4, 2: 5, 3: 6})

    def test__del_wordinfo_no_residual_docscore(self):
        index = self._makeOne()
        # Simulate old instances which didn't have these as attributes
        index._add_wordinfo(123, 4, 1)
        index._del_wordinfo(123, 1)
        self.assertEqual(index.wordCount(), 0)
        self.assertRaises(KeyError, index._wordinfo.__getitem__, 123)

    def test__del_wordinfo_w_residual_docscore(self):
        index = self._makeOne()
        # Simulate old instances which didn't have these as attributes
        index._add_wordinfo(123, 4, 1)
        index._add_wordinfo(123, 5, 2)
        index._del_wordinfo(123, 1)
        self.assertEqual(index.wordCount(), 1)
        self.assertEqual(index._wordinfo[123], {2: 5})

    def test__del_wordinfo_upgrades_wordCount(self):
        index = self._makeOne()
        index._add_wordinfo(123, 4, 1)
        # Simulate old instances which didn't have these as attributes
        del index.wordCount
        index._del_wordinfo(123, 1)
        self.assertEqual(index.wordCount(), 0)

class BaseIndexTest32(BaseIndexTestBase, unittest.TestCase):

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family32

class BaseIndexTest64(BaseIndexTestBase, unittest.TestCase):

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family64

def test_suite():
    return unittest.TestSuite((
                      unittest.makeSuite(BaseIndexTest32),
                      unittest.makeSuite(BaseIndexTest64),
                    ))
