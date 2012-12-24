import unittest

_marker = object()


class _KeywordIndexTestsBase:

    def _getTargetClass(self):
        from . import KeywordIndex
        return KeywordIndex

    def _populate(self, index):

        index.index_doc(1, ('zope', 'CMF', 'Zope3'))
        index.index_doc(2, ('the', 'quick', 'brown', 'FOX'))
        index.index_doc(3, ('Zope',))
        index.index_doc(4, ())
        index.index_doc(5, ('cmf',))

    _populated_doc_count = 4
    _populated_word_count = 9

    def test_normalize(self):
        index = self._makeOne()
        self.assertEqual(index.normalize(['Foo']), ['Foo'])

    def test_simplesearch(self):
        index = self._makeOne()
        self._populate(index)
        self._search(index, [''],      self.IFSet())
        self._search(index, 'cmf',     self.IFSet([5]))
        self._search(index, ['cmf'],   self.IFSet([5]))
        self._search(index, ['Zope'],  self.IFSet([3]))
        self._search(index, ['Zope3'], self.IFSet([1]))
        self._search(index, ['foo'],   self.IFSet())

    def test_search_and(self):
        index = self._makeOne()
        self._populate(index)
        self._search_and(index, ('CMF', 'Zope3'), self.IFSet([1]))
        self._search_and(index, ('CMF', 'zope'),  self.IFSet([1]))
        self._search_and(index, ('cmf', 'zope4'), self.IFSet())
        self._search_and(index, ('quick', 'FOX'), self.IFSet([2]))

    def test_search_or(self):
        index = self._makeOne()
        self._populate(index)
        self._search_or(index, ('cmf', 'Zope3'), self.IFSet([1, 5]))
        self._search_or(index, ('cmf', 'zope'),  self.IFSet([1, 5]))
        self._search_or(index, ('cmf', 'zope4'), self.IFSet([5]))
        self._search_or(index, ('zope', 'Zope'), self.IFSet([1,3]))

    def test_apply(self):
        index = self._makeOne()
        self._populate(index)
        self._apply(index, ('CMF', 'Zope3'), self.IFSet([1]))
        self._apply(index, ('CMF', 'zope'),  self.IFSet([1]))
        self._apply(index, ('cmf', 'zope4'), self.IFSet())
        self._apply(index, ('quick', 'FOX'), self.IFSet([2]))

    def test_apply_and(self):
        index = self._makeOne()
        self._populate(index)
        self._apply_and(index, ('CMF', 'Zope3'), self.IFSet([1]))
        self._apply_and(index, ('CMF', 'zope'),  self.IFSet([1]))
        self._apply_and(index, ('cmf', 'zope4'), self.IFSet())
        self._apply_and(index, ('quick', 'FOX'), self.IFSet([2]))

    def test_apply_or(self):
        index = self._makeOne()
        self._populate(index)
        self._apply_or(index, ('cmf', 'Zope3'), self.IFSet([1, 5]))
        self._apply_or(index, ('cmf', 'zope'),  self.IFSet([1, 5]))
        self._apply_or(index, ('cmf', 'zope4'), self.IFSet([5]))
        self._apply_or(index, ('zope', 'Zope'), self.IFSet([1,3]))

    def test_apply_with_only_tree_set(self):
        index = self._makeOne()
        index.tree_threshold = 0
        self._populate(index)
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFTreeSet()))
        self._apply_and(index, ('CMF', 'Zope3'), self.IFSet([1]))
        self._apply_and(index, ('CMF', 'zope'),  self.IFSet([1]))
        self._apply_and(index, ('cmf', 'zope4'), self.IFSet())
        self._apply_and(index, ('quick', 'FOX'), self.IFSet([2]))

    def test_apply_with_mix_of_tree_set_and_simple_set(self):
        index = self._makeOne()
        index.tree_threshold = 2
        self._populate(index)
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFSet()))
        self._apply_and(index, ('CMF', 'Zope3'), self.IFSet([1]))
        self._apply_and(index, ('CMF', 'zope'),  self.IFSet([1]))
        self._apply_and(index, ('cmf', 'zope4'), self.IFSet())
        self._apply_and(index, ('quick', 'FOX'), self.IFSet([2]))

        
    def test_apply_doesnt_mutate_query(self):
        # Some previous version of zope.index munged the query dict
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        query = {'operator': 'or', 'query': [5]}
        result = index.apply(FrozenDict(query))
        self.assertEqual(list(result), [2, 3])
        self.assertEqual(query, {'operator': 'or', 'query': [5]})

    def test_applyAny(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        result = index.applyAny([5, 9])
        self.assertEqual(list(result), [2, 3, 4, 5])

    def test_applyNotAny(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        result = index.applyNotAny([5, 9])
        self.assertEqual(list(result), [1])

    def test_applyAll(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        result = index.applyAll([5, 9])
        self.assertEqual(list(result), [])

    def test_applyNotAll(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        result = index.applyNotAll([5, 9])
        self.assertEqual(list(result), [1, 2, 3, 4, 5])

    def test_applyEq(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        result = index.applyEq(5)
        self.assertEqual(list(result), [2, 3])

    def test_applyNotEq(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        result = index.applyNotEq(5)
        self.assertEqual(list(result), [1, 4, 5])

    def test_applyNotEq_with_unindexed_docs(self):

        def discriminator(obj, default):
            if isinstance(obj, list):
                return obj
            return default

        index = self._makeOne(discriminator)
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        index.index_doc(6, (5, 6))
        result = index.applyNotEq(5)
        self.assertEqual(list(result), [1, 4, 5, 6])

    def test_applyNotEq_nothing_indexed(self):
        def discriminator(obj, default):
            return default
        index = self._makeOne(discriminator)
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        index.index_doc(6, (5, 6))
        result = index.applyNotEq(5)
        self.assertEqual(list(result), [1, 2, 3, 4, 5, 6])


    def test_optimize_converts_to_tree_set(self):
        index = self._makeOne()
        self._populate(index)
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFSet()))
        index.tree_threshold = 0
        index.optimize()
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFTreeSet()))

    def test_docids(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        index.index_doc(2, [3, 4, 5])
        index.index_doc(3, [5, 6, 7])
        index.index_doc(4, [7, 8, 9])
        index.index_doc(5, [9, 10])
        index.index_doc(6, (5, 6))
        self.assertEqual(set(index.docids()),
                         set((1, 2, 3, 4, 5, 6)))

    def test_docids_with_indexed_and_not_indexed(self):
        index = self._makeOne()
        index.index_doc(1, [1])
        index.index_doc(2, _marker)
        self.assertEqual(set([1, 2]), set(index.docids()))

    def test_optimize_converts_to_simple_set(self):
        index = self._makeOne()
        index.tree_threshold = 0
        self._populate(index)
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFTreeSet()))
        index.tree_threshold = 99
        index.optimize()
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFSet()))

    def test_optimize_leaves_words_alone(self):
        index = self._makeOne()
        self._populate(index)
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFSet()))
        index.tree_threshold = 99
        index.optimize()
        self.assertEqual(type(index._fwd_index['zope']),
            type(self.IFSet()))

    def test_index_with_empty_sequence_unindexes(self):
        index = self._makeOne()
        self._populate(index)
        self._search(index, 'cmf', self.IFSet([5]))
        index.index_doc(5, ())
        self._search(index, 'cmf', self.IFSet([]))

class _ThirtyTwoBitBase:

    def _get_family(self):
        import BTrees
        return BTrees.family32

    def IFSet(self, *args, **kw):
        from BTrees.IFBTree import IFSet
        return IFSet(*args, **kw)

    def IFTreeSet(self, *args, **kw):
        from BTrees.IFBTree import IFTreeSet
        return IFTreeSet(*args, **kw)

class _SixtyFourBitBase:

    def _get_family(self):
        import BTrees
        return BTrees.family64

    def IFSet(self, *args, **kw):
        from BTrees.LFBTree import LFSet
        return LFSet(*args, **kw)

    def IFTreeSet(self, *args, **kw):
        from BTrees.LFBTree import LFTreeSet
        return LFTreeSet(*args, **kw)

class _TestCaseBase:

    def _makeOne(self, discriminator=_marker, family=_marker):
        def _discriminator(obj, default):
            if obj is _marker:
                return default
            return obj
        if discriminator is _marker:
            discriminator = _discriminator
        if family is _marker:
            family = self._get_family()
        return self._getTargetClass()(discriminator=discriminator,
                                      family=family)
    

    def _search(self, index, query, expected, mode='and'):
        results = index.search(query, mode)

        # results and expected are IFSets() but we can not
        # compare them directly since __eq__() does not seem
        # to be implemented for BTrees
        self.assertEqual(results.keys(), expected.keys())

    def _search_and(self, index, query, expected):
        return self._search(index, query, expected, 'and')

    def _search_or(self, index, query, expected):
        return self._search(index, query, expected, 'or')

    def _apply(self, index, query, expected, mode='and'):
        results = index.apply(query)
        self.assertEqual(results.keys(), expected.keys())

    def _apply_and(self, index, query, expected):
        results = index.apply({'operator': 'and', 'query': query})
        self.assertEqual(results.keys(), expected.keys())

    def _apply_or(self, index, query, expected):
        results = index.apply({'operator': 'or', 'query': query})
        self.assertEqual(results.keys(), expected.keys())

    def test_class_conforms_to_IIndexInjection(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IIndexInjection
        verifyClass(IIndexInjection, self._getTargetClass())

    def test_instance_conforms_to_IIndexInjection(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IIndexInjection
        verifyObject(IIndexInjection, self._makeOne())

    def test_class_conforms_to_IIndexStatistics(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IIndexStatistics
        verifyClass(IIndexStatistics, self._getTargetClass())

    def test_instance_conforms_to_IIndexStatistics(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IIndexStatistics
        verifyObject(IIndexStatistics, self._makeOne())

    def test_class_conforms_to_IKeywordQuerying(self):
        from zope.interface.verify import verifyClass
        from .interfaces import IKeywordQuerying
        verifyClass(IKeywordQuerying, self._getTargetClass())

    def test_instance_conforms_to_IKeywordQuerying(self):
        from zope.interface.verify import verifyObject
        from .interfaces import IKeywordQuerying
        verifyObject(IKeywordQuerying, self._makeOne())

    def test_class_conforms_to_IIndex(self):
        from zope.interface.verify import verifyClass
        from hypatia.interfaces import IIndex
        verifyClass(IIndex, self._getTargetClass())

    def test_instance_conforms_to_IIndex(self):
        from zope.interface.verify import verifyObject
        from hypatia.interfaces import IIndex
        verifyObject(IIndex, self._makeOne())
        
    def test_document_repr(self):
        index = self._makeOne()
        self._populate(index)
        self.assertTrue('CMF' in index.document_repr(1))
        self.assertEqual(index.document_repr(50, True), True)

    def test_ctor_defaults(self):
        index = self._makeOne()
        self.failUnless(index.family is self._get_family())

    def test_ctor_explicit_family(self):
        import BTrees
        index = self._makeOne(family=BTrees.family32)
        self.failUnless(index.family is BTrees.family32)

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
        
    def test_empty_index(self):
        index = self._makeOne()
        self.assertEqual(index.indexed_count(), 0)
        self.assertEqual(index.word_count(), 0)
        self.failIf(index.has_doc(1))

    def test_index_doc_string_value_raises(self):
        index = self._makeOne()
        self.assertRaises(TypeError, index.index_doc, 1, 'albatross')

    def test_index_doc_single(self):
        index = self._makeOne()
        index.index_doc(1, ('albatross', 'cormorant'))
        self.assertEqual(index.indexed_count(), 1)
        self.assertEqual(index.word_count(), 2)
        self.failUnless(index.has_doc(1))
        self.failUnless('albatross' in index._fwd_index)
        self.failUnless('cormorant' in index._fwd_index)

    def test_index_doc_existing(self):
        index = self._makeOne()
        index.index_doc(1, ('albatross', 'cormorant'))
        index.index_doc(1, ('buzzard', 'cormorant'))
        self.assertEqual(index.indexed_count(), 1)
        self.assertEqual(index.word_count(), 2)
        self.failUnless(index.has_doc(1))
        self.failIf('albatross' in index._fwd_index)
        self.failUnless('buzzard' in index._fwd_index)
        self.failUnless('cormorant' in index._fwd_index)

    def test_index_doc_many(self):
        index = self._makeOne()
        self._populate(index)
        self.assertEqual(index.indexed_count(), self._populated_doc_count)
        self.assertEqual(index.word_count(), self._populated_word_count)
        for docid in range(1, 6):
            if docid == 4:
                self.failIf(index.has_doc(docid))
            else:
                self.failUnless(index.has_doc(docid))

    def test_index_doc_then_missing_value(self):
        index = self._makeOne()
        index.index_doc(20, [1, 2, 3])
        self.assertEqual(set([20]), set(index.applyEq(2)))
        self.failUnless(20 in index.docids())
        index.index_doc(20, _marker)
        self.assertEqual(set(), set(index.applyEq(2)))
        self.failUnless(20 in index.docids())

    def test_index_doc_missing_value_then_with_value(self):
        index = self._makeOne()
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())
        index.index_doc(3, [3, 4, 5])
        self.assertEqual(set([3]), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        index = self._makeOne()
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())
        index.unindex_doc(3)
        self.assertEqual(set(), set(index.applyEq(4)))
        docids = index.docids()
        self.failIf(3 in docids)

    def test_index_doc_value_is_marker(self):
        index = self._makeOne()
        # this should never be raised
        index.unindex_doc = lambda *arg, **kw: 0/1
        index.index_doc(1, _marker)
        self.assertTrue(1 in index._not_indexed)
        index.index_doc(1, _marker)
        self.assertTrue(1 in index._not_indexed)

    def test_index_doc_same_value(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2])
        self.assertEqual(sorted(index._fwd_index[1]), [1])
        index.index_doc(1, [1, 2])
        self.assertEqual(sorted(index._fwd_index[1]), [1])

    def test_reindex_doc_doesnt_unindex(self):
        index = self._makeOne()
        index.index_doc(5, [1])
        index.unindex_doc = lambda *args, **kw: 1 / 0
        index.reindex_doc(5, [1])

    def test_reindex_doc_same_values(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        self.assertEqual(index.indexed_count(), 1)
        index.reindex_doc(1, [1, 2, 3])
        self.assertEqual(index.indexed_count(), 1)
        self.failUnless(1 in index._rev_index)
        self.failUnless(1 in index._fwd_index[1])
        self.failUnless(1 in index._fwd_index[2])
        self.failUnless(1 in index._fwd_index[3])
        self.failIf(4 in index._fwd_index)

    def test_reindex_doc_different_values(self):
        index = self._makeOne()
        index.index_doc(1, [1, 2, 3])
        self.assertEqual(index.indexed_count(), 1)
        index.reindex_doc(1, [2, 3, 4])
        self.assertEqual(index.indexed_count(), 1)
        self.failUnless(1 in index._rev_index)
        self.failIf(1 in index._fwd_index.get(1, []))
        self.failUnless(1 in index._fwd_index[2])
        self.failUnless(1 in index._fwd_index[3])
        self.failUnless(1 in index._fwd_index[4])

    def test_reset(self):
        index = self._makeOne()
        self._populate(index)
        index.reset()
        self.assertEqual(index.indexed_count(), 0)
        self.assertEqual(index.word_count(), 0)
        for docid in range(1, 6):
            self.failIf(index.has_doc(docid))

    def test_unindex_doc_missing(self):
        index = self._makeOne()
        index.unindex_doc(1) # doesn't raise

    def test_unindex_no_residue(self):
        index = self._makeOne()
        index.index_doc(1, ('albatross', ))
        index.unindex_doc(1)
        self.assertEqual(index.indexed_count(), 0)
        self.assertEqual(index.word_count(), 0)
        self.failIf(index.has_doc(1))

    def test_unindex_w_residue(self):
        index = self._makeOne()
        index.index_doc(1, ('albatross', ))
        index.index_doc(2, ('albatross', 'cormorant'))
        index.unindex_doc(1)
        self.assertEqual(index.indexed_count(), 1)
        self.assertEqual(index.word_count(), 2)
        self.failIf(index.has_doc(1))

    def test_unindex_doc_removes_from_docids(self):
        index = self._makeOne()
        index.index_doc(20, [1, 2, 3])
        self.failUnless(20 in index.docids())
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_hasdoc(self):
        index = self._makeOne()
        self._populate(index)
        self.assertEqual(index.has_doc(1), 1)
        self.assertEqual(index.has_doc(2), 1)
        self.assertEqual(index.has_doc(3), 1)
        self.assertEqual(index.has_doc(4), 0)
        self.assertEqual(index.has_doc(5), 1)
        self.assertEqual(index.has_doc(6), 0)

    def test_search_bad_operator(self):
        index = self._makeOne()
        self.assertRaises(TypeError, index.search, 'whatever', 'maybe')

    def test_any(self):
        from .. import query
        index = self._makeOne()
        result = index.any([1])
        self.assertEqual(result.__class__, query.Any)
        self.assertEqual(result._value, [1])
        
    def test_notany(self):
        from .. import query
        index = self._makeOne()
        result = index.notany([1])
        self.assertEqual(result.__class__, query.NotAny)
        self.assertEqual(result._value, [1])

    def test_all(self):
        from .. import query
        index = self._makeOne()
        result = index.all([1])
        self.assertEqual(result.__class__, query.All)
        self.assertEqual(result._value, [1])
        
    def test_notall(self):
        from .. import query
        index = self._makeOne()
        result = index.notall([1])
        self.assertEqual(result.__class__, query.NotAll)
        self.assertEqual(result._value, [1])

    def test_eq(self):
        from .. import query
        index = self._makeOne()
        result = index.eq(1)
        self.assertEqual(result.__class__, query.Eq)
        self.assertEqual(result._value, 1)
        
    def test_noteq(self):
        from .. import query
        index = self._makeOne()
        result = index.noteq(1)
        self.assertEqual(result.__class__, query.NotEq)
        self.assertEqual(result._value, 1)


class KeywordIndexTests32(_KeywordIndexTestsBase,
                          _ThirtyTwoBitBase,
                          _TestCaseBase,
                          unittest.TestCase):
    pass

class KeywordIndexTests64(_KeywordIndexTestsBase,
                          _SixtyFourBitBase,
                          _TestCaseBase,
                          unittest.TestCase):
    pass

class FrozenDict(dict):
    def _forbidden(self, *args, **kw):
        assert 0 # pragma: no cover
    __setitem__ = __delitem__ = clear = update = _forbidden

