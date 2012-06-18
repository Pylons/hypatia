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
"""Query Engine tests
"""
import unittest

class FauxIndex(object):

    def _get_family(self):
        import BTrees
        return BTrees.family32
    family = property(_get_family,)

    def search(self, term):
        b = self.family.IF.Bucket()
        if term == "foo":
            b[1] = b[3] = 1
        elif term == "bar":
            b[1] = b[2] = 1
        elif term == "ham":
            b[1] = b[2] = b[3] = b[4] = 1
        return b

class TestQueryEngine(unittest.TestCase):

    def _makeIndexAndParser(self):
        from ..lexicon import Lexicon
        from ..lexicon import Splitter
        from ..queryparser import QueryParser
        lexicon = Lexicon(Splitter())
        parser = QueryParser(lexicon)
        index = FauxIndex()
        return index, parser

    def _compareSet(self, set, dict):
        d = {}
        for k, v in set.items():
            d[k] = v
        self.assertEqual(d, dict)

    def _compareQuery(self, query, dict):
        index, parser = self._makeIndexAndParser()
        tree = parser.parseQuery(query)
        set = tree.executeQuery(index)
        self._compareSet(set, dict)

    def testExecuteQuery(self):
        self._compareQuery("foo AND bar", {1: 2})
        self._compareQuery("foo OR bar", {1: 2, 2: 1, 3:1})
        self._compareQuery("foo AND NOT bar", {3: 1})
        self._compareQuery("foo AND foo AND foo", {1: 3, 3: 3})
        self._compareQuery("foo OR foo OR foo", {1: 3, 3: 3})
        self._compareQuery("ham AND NOT foo AND NOT bar", {4: 1})
        self._compareQuery("ham OR foo OR bar", {1: 3, 2: 2, 3: 2, 4: 1})
        self._compareQuery("ham AND foo AND bar", {1: 3})

    def testInvalidQuery(self):
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        from ..parsetree import QueryError
        index, parser = self._makeIndexAndParser()
        tree = NotNode(AtomNode("foo"))
        self.assertRaises(QueryError, tree.executeQuery, index)

