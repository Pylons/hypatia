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
"""Set Options tests
"""
import unittest
import BTrees

_marker = object()

class Test_mass_weightedIntersection(unittest.TestCase):

    family = BTrees.family64

    def _callFUT(self, L, family=_marker):
        from ..setops import mass_weightedIntersection
        if family is _marker:
            return mass_weightedIntersection(L)
        return mass_weightedIntersection(L, family)

    def test_empty_list_no_family(self):
        from BTrees.LFBTree import LFBucket
        t = self._callFUT([])
        self.assertEqual(len(t), 0)
        self.assertEqual(t.__class__, LFBucket)

    def test_empty_list_family32(self):
        import BTrees
        from BTrees.IFBTree import IFBucket
        t = self._callFUT([], BTrees.family32)
        self.assertEqual(len(t), 0)
        self.assertEqual(t.__class__, IFBucket)

    def test_empty_list_family64(self):
        import BTrees
        from BTrees.LFBTree import LFBucket
        t = self._callFUT([], BTrees.family64)
        self.assertEqual(len(t), 0)
        self.assertEqual(t.__class__, LFBucket)

    def test_identity_tree(self):
        IFBTree = self.family.IF.BTree
        x = IFBTree([(1, 2)])
        result = self._callFUT([(x, 1)])
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.items()), list(x.items()))

    def test_identity_bucket(self):
        IFBucket = self.family.IF.Bucket
        x = IFBucket([(1, 2)])
        result = self._callFUT([(x, 1)])
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.items()), list(x.items()))

    def test_scalar_multiply_tree(self):
        IFBTree = self.family.IF.BTree
        x = IFBTree([(1, 2), (2, 3), (3, 4)])
        allkeys = list(x.keys())
        for factor in 0, 1, 5, 10:
            result = self._callFUT([(x, factor)])
            self.assertEqual(allkeys, list(result.keys()))
            for key in x.keys():
                self.assertEqual(result[key], x[key]*factor)

    def test_scalar_multiply_bucket(self):
        IFBucket = self.family.IF.Bucket
        x = IFBucket([(1, 2), (2, 3), (3, 4)])
        allkeys = list(x.keys())
        for factor in 0, 1, 5, 10:
            result = self._callFUT([(x, factor)])
            self.assertEqual(allkeys, list(result.keys()))
            for key in x.keys():
                self.assertEqual(result[key], x[key]*factor)

    def test_pairs(self):
        IFBTree = self.family.IF.BTree
        IFBucket = self.family.IF.Bucket
        t1 = IFBTree([(1, 10), (3, 30), (7, 70)])
        t2 = IFBTree([(3, 30), (5, 50), (7, 7), (9, 90)])
        allkeys = [1, 3, 5, 7, 9]
        b1 = IFBucket(t1)
        b2 = IFBucket(t2)
        for x in t1, t2, b1, b2:
            for key in x.keys():
                self.assertEqual(key in allkeys, 1)
            for y in t1, t2, b1, b2:
                for w1, w2 in (0, 0), (1, 10), (10, 1), (2, 3):
                    expected = []
                    for key in allkeys:
                        if x.has_key(key) and y.has_key(key):
                            result = x[key] * w1 + y[key] * w2
                            expected.append((key, result))
                    expected.sort()
                    got = self._callFUT([(x, w1), (y, w2)])
                    self.assertEqual(expected, list(got.items()))
                    got = self._callFUT([(y, w2), (x, w1)])
                    self.assertEqual(expected, list(got.items()))

    def testMany(self):
        import random
        IFBTree = self.family.IF.BTree
        N = 15  # number of IFBTrees to feed in
        L = []
        commonkey = N * 1000
        allkeys = {commonkey: 1}
        for i in range(N):
            t = IFBTree()
            t[commonkey] = i
            for j in range(N-i):
                key = i + j
                allkeys[key] = 1
                t[key] = N*i + j
            L.append((t, i+1))
        random.shuffle(L)
        allkeys = allkeys.keys()
        allkeys.sort()

        # Test the intersection.
        expected = []
        for key in allkeys:
            sum = 0
            for t, w in L:
                if t.has_key(key):
                    sum += t[key] * w
                else:
                    break
            else:
                # We didn't break out of the loop so it's in the intersection.
                expected.append((key, sum))
        # print 'intersection', expected
        got = self._callFUT(L)
        self.assertEqual(expected, list(got.items()))

class Test_mass_weightedUnion(unittest.TestCase):

    family = BTrees.family64

    def _callFUT(self, L, family=_marker):
        from ..setops import mass_weightedUnion
        if family is _marker:
            return mass_weightedUnion(L)
        return mass_weightedUnion(L, family)

    def test_empty_list_no_family(self):
        from BTrees.LFBTree import LFBucket
        t = self._callFUT([])
        self.assertEqual(len(t), 0)
        self.assertEqual(t.__class__, LFBucket)

    def test_empty_list_family32(self):
        import BTrees
        from BTrees.IFBTree import IFBucket
        t = self._callFUT([], BTrees.family32)
        self.assertEqual(len(t), 0)
        self.assertEqual(t.__class__, IFBucket)

    def test_empty_list_family64(self):
        import BTrees
        from BTrees.LFBTree import LFBucket
        t = self._callFUT([], BTrees.family64)
        self.assertEqual(len(t), 0)
        self.assertEqual(t.__class__, LFBucket)

    def test_identity_tree(self):
        IFBTree = self.family.IF.BTree
        x = IFBTree([(1, 2)])
        result = self._callFUT([(x, 1)])
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.items()), list(x.items()))

    def test_identity_bucket(self):
        IFBucket = self.family.IF.Bucket
        x = IFBucket([(1, 2)])
        result = self._callFUT([(x, 1)])
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.items()), list(x.items()))

    def test_scalar_multiply_tree(self):
        IFBTree = self.family.IF.BTree
        x = IFBTree([(1, 2), (2, 3), (3, 4)])
        allkeys = list(x.keys())
        for factor in 0, 1, 5, 10:
            result = self._callFUT([(x, factor)])
            self.assertEqual(allkeys, list(result.keys()))
            for key in x.keys():
                self.assertEqual(result[key], x[key]*factor)

    def test_scalar_multiply_bucket(self):
        IFBucket = self.family.IF.Bucket
        x = IFBucket([(1, 2), (2, 3), (3, 4)])
        allkeys = list(x.keys())
        for factor in 0, 1, 5, 10:
            result = self._callFUT([(x, factor)])
            self.assertEqual(allkeys, list(result.keys()))
            for key in x.keys():
                self.assertEqual(result[key], x[key]*factor)

    def test_pairs(self):
        IFBucket = self.family.IF.Bucket
        IFBTree = self.family.IF.BTree
        t1 = IFBTree([(1, 10), (3, 30), (7, 70)])
        t2 = IFBTree([(3, 30), (5, 50), (7, 7), (9, 90)])
        allkeys = [1, 3, 5, 7, 9]
        b1 = IFBucket(t1)
        b2 = IFBucket(t2)
        for x in t1, t2, b1, b2:
            for key in x.keys():
                self.assertEqual(key in allkeys, 1)
            for y in t1, t2, b1, b2:
                for w1, w2 in (0, 0), (1, 10), (10, 1), (2, 3):
                    expected = []
                    for key in allkeys:
                        if x.has_key(key) or y.has_key(key):
                            result = x.get(key, 0) * w1 + y.get(key, 0) * w2
                            expected.append((key, result))
                    expected.sort()
                    got = self._callFUT([(x, w1), (y, w2)])
                    self.assertEqual(expected, list(got.items()))
                    got = self._callFUT([(y, w2), (x, w1)])
                    self.assertEqual(expected, list(got.items()))

    def test_many(self):
        import random
        IFBTree = self.family.IF.BTree
        N = 15  # number of IFBTrees to feed in
        L = []
        commonkey = N * 1000
        allkeys = {commonkey: 1}
        for i in range(N):
            t = IFBTree()
            t[commonkey] = i
            for j in range(N-i):
                key = i + j
                allkeys[key] = 1
                t[key] = N*i + j
            L.append((t, i+1))
        random.shuffle(L)
        allkeys = allkeys.keys()
        allkeys.sort()

        expected = []
        for key in allkeys:
            sum = 0
            for t, w in L:
                if t.has_key(key):
                    sum += t[key] * w
            expected.append((key, sum))
        # print 'union', expected
        got = self._callFUT(L)
        self.assertEqual(expected, list(got.items()))

