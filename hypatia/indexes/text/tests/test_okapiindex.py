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
"""Okapi text index tests
"""
import unittest

class OkapiIndexTestBase:
    # Subclasses must define '_getBTreesFamily'
    def _getTargetClass(self):
        from hypatia.indexes.text.okapiindex import OkapiIndex
        return OkapiIndex

    def _makeOne(self):
        from hypatia.indexes.text.lexicon import Lexicon
        from hypatia.indexes.text.lexicon import Splitter
        lexicon = Lexicon(Splitter())
        return self._getTargetClass()(lexicon, family=self._getBTreesFamily())

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
        from hypatia.indexes.text.interfaces import ILexiconBasedIndex
        verifyClass(ILexiconBasedIndex, self._getTargetClass())

    def test_instance_conforms_to_ILexiconBasedIndex(self):
        from zope.interface.verify import verifyObject
        from hypatia.indexes.text.interfaces import ILexiconBasedIndex
        verifyObject(ILexiconBasedIndex, self._makeOne())

    def test_class_conforms_to_IExtendedQuerying(self):
        from zope.interface.verify import verifyClass
        from hypatia.indexes.text.interfaces import IExtendedQuerying
        verifyClass(IExtendedQuerying, self._getTargetClass())

    def test_instance_conforms_to_IExtendedQuerying(self):
        from zope.interface.verify import verifyObject
        from hypatia.indexes.text.interfaces import IExtendedQuerying
        verifyObject(IExtendedQuerying, self._makeOne())

    def test_empty(self):
        index = self._makeOne()
        self.assertEqual(index._totaldoclen(), 0)

    def test_index_doc_updates_totaldoclen(self):
        index = self._makeOne()
        index.index_doc(1, 'one two three')
        index.index_doc(2, 'two three four')
        self.assertEqual(index._totaldoclen(), 6)

    def test_index_doc_existing_updates_totaldoclen(self):
        index = self._makeOne()
        index.index_doc(1, 'one two three')
        index.index_doc(1, 'two three four')
        self.assertEqual(index._totaldoclen(), 3)

    def test_index_doc_upgrades_totaldoclen(self):
        index = self._makeOne()

        # Simulate old instances which didn't have Length attributes
        index._totaldoclen = 0

        index.index_doc(1, 'one two three')

        self.assertEqual(index._totaldoclen(), 3)

    def test__search_wids_non_empty_wids(self):
        TEXT = 'one two three'
        index = self._makeOne()
        index.index_doc(1, TEXT )
        wids = [index._lexicon._wids[x] for x in TEXT.split()]
        relevances = index._search_wids(wids)
        self.assertEqual(len(relevances), len(wids))
        for relevance in relevances:
            self.failUnless(isinstance(relevance[0], index.family.IF.Bucket))
            self.assertEqual(len(relevance[0]), 1)
            self.failUnless(isinstance(relevance[0][1], float))
            self.failUnless(isinstance(relevance[1], int))

    def test__search_wids_old_totaldoclen_no_write_on_read(self):
        index = self._makeOne()
        index.index_doc(1, 'one two three')

        # Simulate old instances which didn't have Length attributes
        index._totaldoclen = 3

        relevances = index._search_wids([1])

        self.failUnless(isinstance(index._totaldoclen, int))

    def test_query_weight_empty_wids(self):
        index = self._makeOne()
        index.index_doc(1, 'one two three')
        self.assertEqual(index.query_weight(()), 0.0)

    def test_query_weight_oov_wids(self):
        index = self._makeOne()
        index.index_doc(1, 'one two three')
        self.assertEqual(index.query_weight(['nonesuch']), 0.0)

    def test_query_weight_hit_single_occurence(self):
        index = self._makeOne()
        index.index_doc(1, 'one two three')
        self.failUnless(0.0 < index.query_weight(['one']))

    def test_query_weight_hit_multiple_occurences(self):
        index = self._makeOne()
        index.index_doc(1, 'one one two three one')
        self.failUnless(0.0 < index.query_weight(['one']))


class OkapiIndexTest32(OkapiIndexTestBase, unittest.TestCase):

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family32

class OkapiIndexTest64(OkapiIndexTestBase, unittest.TestCase):

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family64

def test_suite():
    return unittest.TestSuite((
                      unittest.makeSuite(OkapiIndexTest32),
                      unittest.makeSuite(OkapiIndexTest64),
                    ))
