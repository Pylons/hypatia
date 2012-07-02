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
"""Text Index Tests
"""
import unittest

class IndexTestBase:
    # Subclasses must define '_getTargetClass' and '_getBTreesFamily'
    def _makeOne(self):
        from ..lexicon import Lexicon
        from ..lexicon import Splitter
        lexicon = Lexicon(Splitter())
        return self._getTargetClass()(lexicon, family=self._getBTreesFamily())

    def _check_index_has_document(self, index, docid, word_count=5):
        self.assertEqual(index.indexed_count(), 1)
        self.assertEqual(index.word_count(), word_count)
        self.assertEqual(index._lexicon.word_count(), word_count)
        self.assert_(index.has_doc(docid))
        self.assert_(index._docweight[docid])
        self.assertEqual(len(index._docweight), 1)
        self.assertEqual(len(index._wordinfo), word_count)
        self.assertEqual(len(index._docwords), 1)
        self.assertEqual(len(index.get_words(docid)), word_count)
        self.assertEqual(len(index._wordinfo),
                         index.word_count())
        for map in index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(docid))

    def _check_index_is_empty(self, index):
        self.assertEqual(len(index._docweight), 0)
        self.assertEqual(len(index._wordinfo), 0)
        self.assertEqual(len(index._docwords), 0)
        self.assertEqual(len(index._wordinfo),
                         index.word_count())

    def test_empty(self):
        index = self._makeOne()
        self._check_index_is_empty(index)

    def test_index_document(self):
        doc = "simple document contains five words"
        index = self._makeOne()
        self.assert_(not index.has_doc(1))
        index.index_doc(1, doc)
        self._check_index_has_document(index, 1)

    def test_unindex_document(self):
        doc = "simple document contains five words"
        index = self._makeOne()
        index.index_doc(1, doc)
        index.unindex_doc(1)
        self._check_index_is_empty(index)

    def test_unindex_document_absent_docid(self):
        doc = "simple document contains five words"
        index = self._makeOne()
        index.index_doc(1, doc)
        index.unindex_doc(2)
        self._check_index_has_document(index, 1)

    def test_reset(self):
        doc = "simple document contains five words"
        index = self._makeOne()
        index.index_doc(1, doc)
        index.reset()
        self._check_index_is_empty(index)

    def test_index_two_documents(self):
        doc1 = "simple document contains five words"
        doc2 = "another document just four"
        index = self._makeOne()
        index.index_doc(1, doc1)
        index.index_doc(2, doc2)
        self.failUnless(index._docweight[2])
        self.assertEqual(len(index._docweight), 2)
        self.assertEqual(len(index._wordinfo), 8)
        self.assertEqual(len(index._docwords), 2)
        self.assertEqual(len(index.get_words(2)), 4)
        self.assertEqual(len(index._wordinfo),
                         index.word_count())
        wids = index._lexicon.termToWordIds("document")
        self.assertEqual(len(wids), 1)
        document_wid = wids[0]
        for wid, map in index._wordinfo.items():
            if wid == document_wid:
                self.assertEqual(len(map), 2)
                self.assert_(map.has_key(1))
                self.assert_(map.has_key(2))
            else:
                self.assertEqual(len(map), 1)

    def test_index_two_unindex_one(self):
        # index two documents, unindex one, and test the results
        doc1 = "simple document contains five words"
        doc2 = "another document just four"
        index = self._makeOne()
        index.index_doc(1, doc1)
        index.index_doc(2, doc2)
        index.unindex_doc(1)
        self.assertEqual(len(index._docweight), 1)
        self.assert_(index._docweight[2])
        self.assertEqual(len(index._wordinfo), 4)
        self.assertEqual(len(index._docwords), 1)
        self.assertEqual(len(index.get_words(2)), 4)
        self.assertEqual(len(index._wordinfo),
                         index.word_count())
        for map in index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(2))

    def test_index_duplicated_words(self):
        doc = "very simple repeat repeat repeat document test"
        index = self._makeOne()
        index.index_doc(1, doc)
        self.assert_(index._docweight[1])
        self.assertEqual(len(index._wordinfo), 5)
        self.assertEqual(len(index._docwords), 1)
        self.assertEqual(len(index.get_words(1)), 7)
        self.assertEqual(len(index._wordinfo),
                         index.word_count())
        wids = index._lexicon.termToWordIds("repeat")
        self.assertEqual(len(wids), 1)
        for wid, map in index._wordinfo.items():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(1))

    def test_simple_query_oneresult(self):
        index = self._makeOne()
        index.index_doc(1, 'not the same document')
        results = index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_simple_query_noresults(self):
        index = self._makeOne()
        index.index_doc(1, 'not the same document')
        results = index.search("frobnicate")
        self.assertEqual(list(results.keys()), [])

    def test_query_oneresult(self):
        index = self._makeOne()
        index.index_doc(1, 'not the same document')
        index.index_doc(2, 'something about something else')
        results = index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_search_phrase(self):
        index = self._makeOne()
        index.index_doc(1, "the quick brown fox jumps over the lazy dog")
        index.index_doc(2, "the quick fox jumps lazy over the brown dog")
        results = index.search_phrase("quick brown fox")
        self.assertEqual(list(results.keys()), [1])

    def test_search_glob(self):
        index = self._makeOne()
        index.index_doc(1, "how now brown cow")
        index.index_doc(2, "hough nough browne cough")
        index.index_doc(3, "bar brawl")
        results = index.search_glob("bro*")
        self.assertEqual(list(results.keys()), [1, 2])
        results = index.search_glob("b*")
        self.assertEqual(list(results.keys()), [1, 2, 3])

class CosineIndexTest32(IndexTestBase, unittest.TestCase):

    def _getTargetClass(self):
        from ..cosineindex import CosineIndex
        return CosineIndex

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family32

class OkapiIndexTest32(IndexTestBase, unittest.TestCase):

    def _getTargetClass(self):
        from ..okapiindex import OkapiIndex
        return OkapiIndex

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family32

class CosineIndexTest64(IndexTestBase, unittest.TestCase):

    def _getTargetClass(self):
        from ..cosineindex import CosineIndex
        return CosineIndex

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family64

class OkapiIndexTest64(IndexTestBase, unittest.TestCase):

    def _getTargetClass(self):
        from ..okapiindex import OkapiIndex
        return OkapiIndex

    def _getBTreesFamily(self):
        import BTrees
        return BTrees.family64

