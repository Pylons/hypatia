import unittest

_marker = object()


class PathIndexTests(unittest.TestCase):
    """ Test PathIndex objects
    """
    def _getTargetClass(self):
        from repoze.catalog.indexes.path import CatalogPathIndex
        return CatalogPathIndex

    def _makeOne(self, values=None, discriminator=_marker):
        if values is None:
            values = {}
        def _discriminator(obj, default):
            if obj is _marker:
                return default
            return obj.path
        if discriminator is _marker:
            discriminator = _discriminator
        index = self._getTargetClass()(discriminator)
        for doc_id, path in values.items():
            index.index_doc(doc_id, path)
        return index

    def test_class_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyClass
        from repoze.catalog.interfaces import ICatalogIndex
        verifyClass(ICatalogIndex, self._getTargetClass())

    def test_instance_conforms_to_ICatalogIndex(self):
        from zope.interface.verify import verifyObject
        from repoze.catalog.interfaces import ICatalogIndex
        verifyObject(ICatalogIndex, self._makeOne())

    def test_ctor_callback_discriminator(self):
        def _discriminator(obj, default):
            """ """
        index = self._makeOne(discriminator=_discriminator)
        self.failUnless(index.discriminator is _discriminator)

    def test_ctor_string_discriminator(self):
        index = self._makeOne(discriminator='abc')
        self.assertEqual(index.discriminator, 'abc')

    def test_ctor_bad_discriminator(self):
        self.assertRaises(ValueError, self._makeOne, discriminator=object())

    def test_empty_index(self):
        index = self._makeOne({})
        self.assertEqual(index.numObjects() ,0)
        self.assertEqual(index._depth, 0)
        self.assertEqual(index.getEntryForObject(1234), None)
        index.unindex_doc(1234) # nothrow
        result = index.apply({"suxpath":"xxx"})
        self.assertEqual(list(result), [])

    def test_nonempty_index(self):
        index = self._makeOne(VALUES)
        self.assertEqual(index.numObjects(), 18)
        self.assertEqual(index.getEntryForObject(1), '/aa/aa/aa/1.html')

    def test_clear(self):
        index = self._makeOne(VALUES)
        index.clear()
        self.assertEqual(index.numObjects(), 0)
        self.assertEqual(index.getEntryForObject(1), None)
        self.assertEqual(index._depth, 0)

    def test_insertEntry_new_component_new_level(self):
        index = self._makeOne()
        index.insertEntry('aaa', 1, 1)
        self.assertEqual(len(index._index), 1)
        self.assertEqual(len(index._index['aaa']), 1)
        self.assertEqual(list(index._index['aaa'][1]), [1])
        self.assertEqual(index._depth, 1)

    def test_insertEntry_existing_component_new_level(self):
        index = self._makeOne()
        index._index['aaa'] = {2: FakeTreeSet()}
        index._depth = 2
        index.insertEntry('aaa', 1, 1)
        self.assertEqual(len(index._index), 1)
        self.assertEqual(len(index._index['aaa']), 2)
        self.assertEqual(list(index._index['aaa'][1]), [1])
        self.assertEqual(index._depth, 2)

    def test_insertEntry_existing_component_exsiting_level(self):
        index = self._makeOne()
        fts = FakeTreeSet()
        index._index['aaa'] = {2: fts}
        index._depth = 2
        index.insertEntry('aaa', 1, 2)
        self.assertEqual(len(index._index), 1)
        self.assertEqual(len(index._index['aaa']), 1)
        self.failUnless(index._index['aaa'][2] is fts)
        self.assertEqual(list(index._index['aaa'][2]), [1])
        self.assertEqual(index._depth, 2)

    def test_index_doc_callback_returns_nondefault(self):
        def callback(ob, default):
            return ob
        index = self._makeOne(discriminator=callback)
        index.index_doc(1, '/a/b/c')
        self.assertEqual(len(index._index), 3)
        self.assertEqual(list(index._index['a'][0]), [1])
        self.assertEqual(list(index._index['b'][1]), [1])
        self.assertEqual(list(index._index['c'][2]), [1])
        self.assertEqual(index._depth, 2)

    def test_index_doc_string_discrim(self):
        index = self._makeOne(discriminator='abc')
        class Dummy:
            abc = '/a/b/c'
        dummy = Dummy()
        index.index_doc(1, dummy)
        self.assertEqual(len(index._index), 3)
        self.assertEqual(list(index._index['a'][0]), [1])
        self.assertEqual(list(index._index['b'][1]), [1])
        self.assertEqual(list(index._index['c'][2]), [1])
        self.assertEqual(index._depth, 2)

    def test_index_doc_string_discrim_tuple_value(self):
        index = self._makeOne(discriminator='abc')
        class Dummy:
            abc = ('', 'a', 'b', 'c')
        dummy = Dummy()
        index.index_doc(1, dummy)
        self.assertEqual(len(index._index), 3)
        self.assertEqual(list(index._index['a'][0]), [1])
        self.assertEqual(list(index._index['b'][1]), [1])
        self.assertEqual(list(index._index['c'][2]), [1])
        self.assertEqual(index._depth, 2)

    def test_index_doc_string_discrim_list_value(self):
        index = self._makeOne(discriminator='abc')
        class Dummy:
            abc = ['', 'a', 'b', 'c']
        dummy = Dummy()
        index.index_doc(1, dummy)
        self.assertEqual(len(index._index), 3)
        self.assertEqual(list(index._index['a'][0]), [1])
        self.assertEqual(list(index._index['b'][1]), [1])
        self.assertEqual(list(index._index['c'][2]), [1])
        self.assertEqual(index._depth, 2)

    def test_index_doc_missing_value_unindexes(self):
        index = self._makeOne(discriminator='abc')
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = '/a/b/c'
        index.index_doc(1, dummy)
        del dummy.abc
        index.index_doc(1, dummy)
        self.failIf('a' in index._index)
        self.failIf('b' in index._index)
        self.failIf('c' in index._index)
        self.assertEqual(index._depth, 2)

    def test_index_doc_persistent_value_raises(self):
        from persistent import Persistent
        index = self._makeOne(discriminator='abc')
        class Dummy:
            pass
        dummy = Dummy()
        dummy.abc = Persistent()
        self.assertRaises(ValueError, index.index_doc, 1, dummy)

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

    def test_searches_against_root_plain_string(self):
        index = self._makeOne(VALUES)
        expected = range(1,19)

        results = list(index.apply('/').keys())
        self.assertEqual(results, expected)

    def test_searches_against_root_tuple(self):
        index = self._makeOne(VALUES)
        expected = range(1,19)

        results = list(index.apply(('',)).keys())
        self.assertEqual(results, expected)

    def test_searches_against_root_list(self):
        index = self._makeOne(VALUES)
        expected = range(1,19)

        results = list(index.apply(['']).keys())
        self.assertEqual(results, expected)

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

    def test_root_aa_tuple(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,7,8,9]

        results = list(index.apply(('/aa', '/cc')).keys())
        self.assertEqual(results, expected)

    def test_root_aa_list(self):
        index = self._makeOne(VALUES)
        expected = [1,2,3,4,5,6,7,8,9]

        results = list(index.apply(['/aa', '/cc']).keys())
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

    def test_aa_level_4(self):
        index = self._makeOne(VALUES)
        expected = []

        results = list(index.apply({'query': 'aa', 'level': 4}).keys())
        self.assertEqual(results, expected)

        results = list(index.apply({'query': [('aa', 4)]}).keys())
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

    def test_applyEq(self):
        index = self._makeOne(VALUES)
        expected = range(1,19)

        results = list(index.applyEq('/').keys())
        self.assertEqual(results, expected)

    def test_applyNotEq(self):
        index = self._makeOne(VALUES)
        expected = range(1,10)

        results = list(index.applyNotEq('/bb').keys())
        self.assertEqual(results, expected)

    def test_docids(self):
        index = self._makeOne(VALUES)
        self.assertEquals(set(index.docids()), set(range(1, 19)))

    def test_unindex_doc_removes_from_docids(self):
        index = self._makeOne(VALUES)
        index.index_doc(20, _marker)
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_index_doc_then_missing_value(self):
        index = self._makeOne(VALUES)
        self.assertEqual(set([3]), set(index.applyEq('/aa/aa/cc/3.html')))
        self.failUnless(3 in index.docids())
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq('/aa/aa/cc/3.html')))
        self.failUnless(3 in index.docids())

    def test_index_doc_missing_value_then_with_value(self):
        index = self._makeOne()
        index.index_doc(20, _marker)
        self.assertEqual(set(), set(index.applyEq('/cmr')))
        self.failUnless(20 in index.docids())
        index.index_doc(20, Dummy('/cmr/ljb'))
        self.assertEqual(set([20]), set(index.applyEq('/cmr')))
        self.failUnless(20 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        index = self._makeOne()
        index.index_doc(20, _marker)
        self.assertEqual(set(), set(index.applyEq('/cmr')))
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.assertEqual(set(), set(index.applyEq('/cmr')))
        self.failIf(20 in index.docids())

    def test_docids_with_indexed_and_not_indexed(self):
        index = self._makeOne()
        index.index_doc(1, Dummy('/cmr/ljb'))
        index.index_doc(2, _marker)
        self.assertEqual(set([1, 2]), set(index.docids()))


class FakeTreeSet(set):
    def insert(self, thing):
        self.add(thing)


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
