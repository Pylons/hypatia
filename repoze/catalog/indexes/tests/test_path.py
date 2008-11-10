##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""PathIndex unit tests.

"""

import unittest

class PathIndexTests(unittest.TestCase):
    """ Test PathIndex objects
    """
    def _getTargetClass(self):
        from repoze.catalog.indexes.path import CatalogPathIndex
        return CatalogPathIndex

    def _makeOne(self, values=None):
        if values is None:
            values = {}
        index = self._getTargetClass()('path')
        for doc_id, path in values.items():
            index.index_doc(doc_id, path)
        return index

    def test_class_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyClass
        from repoze.catalog.interfaces import ICatalogIndex
        verifyClass(ICatalogIndex, self._getTargetClass())

    def test_empty_index(self):
        index = self._makeOne({})
        self.assertEqual(index.numObjects() ,0)
        self.assertEqual(index.getEntryForObject(1234), None)
        index.unindex_doc(1234) # nothrow
        result = index.apply({"suxpath":"xxx"})
        self.assertEqual(list(result), [])

    def test_nonempty_index(self):
        index = self._makeOne(VALUES)
        self.assertEqual(index.numObjects(), 18)

    def test_unindex_doc(self):
        index = self._makeOne(VALUES)

        for doc_id in VALUES.keys():
            index.unindex_doc(doc_id)

        self.assertEqual(index.numObjects(), 0)
        self.assertEqual(len(index._index), 0)
        self.assertEqual(len(index._unindex), 0)

    def test_reindex_doesnt_dupe(self):
        index = self._makeOne()
        o = Dummy('/foo/bar')
        index.index_doc(1, o)
        self.assertEqual(index.numObjects(), 1)
        index.index_doc(1, o)
        self.assertEqual(index.numObjects(), 1)

    def test_unindex_nomatch_doesnt_raise(self):
        index = self._makeOne()
        # this should not raise an error
        index.unindex_doc(-1)

        # nor should this
        index._unindex[1] = "/broken/thing"
        index.unindex_doc(1)

    def test_searches_against_root_wo_level(self):
        index = self._makeOne(VALUES)
        expected = range(1,19)

        results = list(index.apply({'query': '/'}).keys())
        self.assertEqual(results, expected)

    def test_searches_against_root_w_level(self):
        index = self._makeOne(VALUES)
        comp = "/"
        level = 0
        expected = range(1,19)

        results = list(index.apply({'query': '/', 'level': 0}).keys())
        self.assertEqual(results, expected)

    def test_root_aa_wo_level(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,7,8,9]

        results = list(index.apply({'query': '/aa'}).keys())
        self.assertEqual(results, expected)

    def test_aa_explicit_level_0(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,7,8,9]

        results = list(index.apply({'query': 'aa', 'level': 0}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('aa', 0)]}).keys())
        self.assertEqual(results, expected)

    def test_aa_level_1(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,10,11,12]

        results = list(index.apply({'query': 'aa', 'level': 1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('aa', 1)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_level_0(self):
        index = self._makeOne(VALUES)
        expected = [10,11,12,13,14,15,16,17,18]

        results = list(index.apply({'query': 'bb', 'level': 0}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb', 0)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_level_1(self):
        index = self._makeOne(VALUES)
        expected = [4,5,6,13,14,15]

        results = list(index.apply({'query': 'bb', 'level': 1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb', 1)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_cc_level_0(self):
        index = self._makeOne(VALUES)
        expected = [16,17,18]

        results = list(index.apply({'query': 'bb/cc', 'level': 0}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb/cc', 0)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_cc_level_1(self):
        index = self._makeOne(VALUES)
        expected = [6,15]

        results = list(index.apply({'query': 'bb/cc', 'level': 1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb/cc', 1)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_aa_level_0(self):
        index = self._makeOne(VALUES)
        expected = [10,11,12]

        results = list(index.apply({'query': 'bb/aa', 'level': 0}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb/aa', 0)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_aa_level_1(self):
        index = self._makeOne(VALUES)
        expected = [4,13]

        results = list(index.apply({'query': 'bb/aa', 'level': 1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb/aa', 1)]}).keys())
        self.assertEqual(results, expected)

    def test_aa_cc_level_neg1(self):
        index = self._makeOne(VALUES)
        expected = [3,7,8,9,12]

        results = list(index.apply({'query': 'aa/cc', 'level': -1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('aa/cc', -1)]}).keys())
        self.assertEqual(results, expected)

    def test_bb_bb_level_neg1(self):
        index = self._makeOne(VALUES)
        expected = [5,13,14,15]

        results = list(index.apply({'query': 'bb/bb', 'level': -1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('bb/bb', -1)]}).keys())
        self.assertEqual(results, expected)

    def test_18_html_level_3(self):
        index = self._makeOne(VALUES)
        expected = [18]

        results = list(index.apply({'query': '18.html', 'level': 3}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('18.html', 3)]}).keys())
        self.assertEqual(results, expected)

    def test_18_html_level_neg1(self):
        index = self._makeOne(VALUES)
        expected = [18]

        results = list(index.apply({'query': '18.html', 'level': -1}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('18.html', -1)]}).keys())
        self.assertEqual(results, expected)

    def test_cc_18_html_level_2(self):
        index = self._makeOne(VALUES)
        expected = [18]

        results = list(index.apply({'query': 'cc/18.html', 'level': 2}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('cc/18.html', 2)]}).keys())
        self.assertEqual(results, expected)

    def test_cc_18_html_level_neg1(self):
        index = self._makeOne(VALUES)
        expected = [18]

        results = list(index.apply({'query': 'cc/18.html', 'level': -1}
                                  ).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('cc/18.html', -1)]}).keys())
        self.assertEqual(results, expected)

    def test_aa_bb_implicit_OR_level_1(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,10,11,12,13,14,15]
        results = list(index.apply({'query': ['aa', 'bb'],
                                    'level': 1,
                                   }).keys())
        self.assertEqual(results, expected)

    def test_aa_bb_explicit_OR_level_1(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,10,11,12,13,14,15]
        results = list(index.apply({'query': ['aa', 'bb'],
                                    'level': 1,
                                    'operator': 'or',
                                   }).keys())
        self.assertEqual(results, expected)

    def test_aa_bb_xx_implicit_OR_level_1(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,10,11,12,13,14,15]
        results = list(index.apply({'query': ['aa', 'bb', 'xx'],
                                    'level': 1,
                                   }).keys())
        self.assertEqual(results, expected)

    def test_aa_bb_xx_explicit_OR_level_1(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,10,11,12,13,14,15]
        results = list(index.apply({'query': ['aa', 'bb', 'xx'],
                                    'level': 1,
                                    'operator': 'or',
                                   }).keys())
        self.assertEqual(results, expected)

    def test_cc_level_1_cc_level_2_implicit_OR(self):
        index = self._makeOne(VALUES)
        expected = [3,6,7,8,9,12,15,16,17,18]
        results = list(index.apply({'query': [('cc', 1), ('cc', 2)],
                                   }).keys())
        self.assertEqual(results, expected)

    def test_cc_level_1_cc_level_2_explicit_OR(self):
        index = self._makeOne(VALUES)
        expected = [3,6,7,8,9,12,15,16,17,18]
        results = list(index.apply({'query': [('cc', 1), ('cc', 2)],
                                    'operator': 'or',
                                   }).keys())
        self.assertEqual(results, expected)

    def test_aa_AND_bb_level_1(self):
        index = self._makeOne(VALUES)
        expected = []
        results = list(index.apply({'query': ['aa', 'bb'],
                                    'level': 1,
                                    'operator': 'and',
                                   }).keys())
        self.assertEqual(results, expected)

    def test_aa_level_0_AND_bb_level_1(self):
        index = self._makeOne(VALUES)
        expected = [4, 5, 6]
        results = list(index.apply({'query': [('aa', 0), ('bb', 1)],
                                    'operator': 'and',
                                   }).keys())
        self.assertEqual(results, expected)

    def test_aa_level_0_AND_cc_level_2(self):
        index = self._makeOne(VALUES)
        expected = [3, 6, 9]
        results = list(index.apply({'query': [('aa', 0), ('cc', 2)],
                                    'operator': 'and',
                                   }).keys())
        self.assertEqual(results, expected)

    def test_query_path_included_with_childrent(self):
        index = self._makeOne()
        index.index_doc(1, Dummy("/ff"))
        index.index_doc(2, Dummy("/ff/gg"))
        index.index_doc(3, Dummy("/ff/gg/3.html"))
        index.index_doc(4, Dummy("/ff/gg/4.html"))
        result = list(index.apply({'query':'/ff/gg'}).keys())
        self.assertEqual(result, [2, 3, 4])

class Dummy:

    def __init__( self, path):
        self.path = path

VALUES = {
    1 : Dummy("/aa/aa/aa/1.html"),
    2 : Dummy("/aa/aa/bb/2.html"),
    3 : Dummy("/aa/aa/cc/3.html"),
    4 : Dummy("/aa/bb/aa/4.html"),
    5 : Dummy("/aa/bb/bb/5.html"),
    6 : Dummy("/aa/bb/cc/6.html"),
    7 : Dummy("/aa/cc/aa/7.html"),
    8 : Dummy("/aa/cc/bb/8.html"),
    9 : Dummy("/aa/cc/cc/9.html"),
    10 : Dummy("/bb/aa/aa/10.html"),
    11 : Dummy("/bb/aa/bb/11.html"),
    12 : Dummy("/bb/aa/cc/12.html"),
    13 : Dummy("/bb/bb/aa/13.html"),
    14 : Dummy("/bb/bb/bb/14.html"),
    15 : Dummy("/bb/bb/cc/15.html"),
    16 : Dummy("/bb/cc/aa/16.html"),
    17 : Dummy("/bb/cc/bb/17.html"),
    18 : Dummy("/bb/cc/cc/18.html")
}
