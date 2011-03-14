import unittest

_marker = object()


class TestCatalogFieldIndex(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.field import CatalogFieldIndex
        return CatalogFieldIndex

    def _makeOne(self, discriminator=_marker):
        def _discriminator(obj, default):
            if obj is _marker:
                return default
            return obj
        if discriminator is _marker:
            discriminator = _discriminator
        return self._getTargetClass()(discriminator)

    def _populateIndex(self, index):
        index.index_doc(5, 1)  # docid, obj
        index.index_doc(2, 2)
        index.index_doc(1, 3)
        index.index_doc(3, 4)
        index.index_doc(4, 5)
        index.index_doc(8, 6)
        index.index_doc(9, 7)
        index.index_doc(7, 8)
        index.index_doc(6, 9)
        index.index_doc(11, 10)
        index.index_doc(10, 11)

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
        index = self._makeOne(_discriminator)
        self.failUnless(index.discriminator is _discriminator)

    def test_ctor_string_discriminator(self):
        index = self._makeOne('abc')
        self.assertEqual(index.discriminator, 'abc')

    def test_ctor_bad_discriminator(self):
        self.assertRaises(ValueError, self._makeOne, object())

    def test_reindex_doc_doesnt_unindex(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        index.unindex_doc = lambda *args, **kw: 1 / 0
        index.reindex_doc(5, 1)

    def test_reindex_doc_w_existing_docid_same_value(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        self.assertEqual(index.documentCount(), 1)
        self.assertEqual(index._rev_index[5], 1)
        index.reindex_doc(5, 1)
        self.assertEqual(index.documentCount(), 1)
        self.assertEqual(index._rev_index[5], 1)

    def test_reindex_doc_w_existing_docid_different_value(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        self.assertEqual(index.documentCount(), 1)
        index.reindex_doc(5, 2)
        self.assertEqual(index.documentCount(), 1)
        self.assertEqual(index._rev_index[5], 2)

    def test_reindex_doc_w_new_docid(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        self.assertEqual(index.documentCount(), 1)
        index.reindex_doc(6, 2)
        self.assertEqual(index.documentCount(), 2)
        self.assertEqual(index._rev_index[5], 1)
        self.assertEqual(index._rev_index[6], 2)

    def test_unindex_doc_nonesuch(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        index.unindex_doc(6)
        self.assertEqual(index.documentCount(), 1)

    def test_unindex_doc_no_other_docids_for_value(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        index.unindex_doc(5)
        self.assertEqual(index.documentCount(), 0)
        self.failIf(5 in index._rev_index)
        self.failIf(1 in index._fwd_index)

    def test_unindex_doc_w_other_docids_for_value(self):
        index = self._makeOne()
        index.index_doc(5, 1)
        index.index_doc(6, 1)
        index.unindex_doc(5)
        self.assertEqual(index.documentCount(), 1)
        self.failIf(5 in index._rev_index)
        self.failUnless(1 in index._fwd_index)

    def test_sort_no_docids(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet()
        result = index.sort(c1)
        self.assertEqual(list(result), [])

    def test_sort_no_docs(self):
        index = self._makeOne()
        from BTrees.IFBTree import IFSet
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1)
        self.assertEqual(list(result), [])

    def test_sort_bad_limit(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError, index.sort, c1, limit=0)

    def test_sort_bad_sort_type(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError, index.sort, c1, sort_type='nonesuch')

    def test_sort_bad_sort_type_reverse_fwscan(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import FWSCAN
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError,
                          index.sort, c1, reverse=True, sort_type=FWSCAN)

    def test_sort_bad_sort_type_reverse(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError,
                          index.sort, c1, reverse=True, sort_type='nonesuch')

    def test_sort_noforce_no_limit(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1)
        self.assertEqual(list(result), [5, 2, 1, 3, 4])

    def test_sort_noforce_timsort(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        # Add enough items to make 'fwscan_wins' return False.
        for i in range(100, 10000):
            index.index_doc(i, i)
        c1 = IFSet([1, 2, 3, 4, 5])
        # No 'limit' means timsort
        result = index.sort(c1)
        self.assertEqual(list(result), [5, 2, 1, 3, 4])

    def test_sort_noforce_nbest(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        # Add enough items to make 'fwscan_wins' return False.
        for i in range(100, 10000):
            index.index_doc(i, i)
        c1 = IFSet([1, 2, 3, 4, 5])
        # Reasonable 'limit' means nbest
        result = index.sort(c1, limit=3)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_noforce_w_limit(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_noforce_reverse_no_limit(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True)
        self.assertEqual(list(result), [4, 3, 1, 2, 5])

    def test_sort_noforce_reverse_w_limit(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True, limit=3)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_noforce_reverse_w_limit_timsort(self):
        from BTrees.IFBTree import IFSet
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        # Add enough items to make 'fwscan_wins' return False.
        for i in range(100, 10000):
            index.index_doc(i, i)
            c1.insert(i)
        result = index.sort(c1, reverse=True, limit=301) # waaa
        self.assertEqual(list(result), range(9999, 9698, -1))

    def test_sort_force_fwscan_no_limit(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import FWSCAN
        index = self._makeOne()
        index.force_scan = True
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, sort_type=FWSCAN)
        self.assertEqual(list(result), [5, 2, 1, 3, 4])

    def test_sort_force_fwscan_missing_docid(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import FWSCAN
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, sort_type=FWSCAN)
        r = list(result)
        self.assertEqual(r, [5, 2, 1, 3, 4]) # 99 not present

    def test_sort_force_fwscan_w_limit(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import FWSCAN
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3, sort_type=FWSCAN)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_force_timsort_no_limit(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import TIMSORT
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, sort_type=TIMSORT)
        self.assertEqual(list(result), [5, 2, 1, 3, 4])

    def test_sort_force_timsort_missing_docid(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import TIMSORT
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, sort_type=TIMSORT)
        r = list(result)
        self.assertEqual(r, [5, 2, 1, 3, 4]) # 99 not present

    def test_sort_force_timsort_w_limit(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import TIMSORT
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3, sort_type=TIMSORT)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_force_timsort_reverse_nolimit(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import TIMSORT
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True, sort_type=TIMSORT)
        self.assertEqual(list(result), [4, 3, 1, 2, 5])

    def test_sort_force_timsort_reverse_missing_docid(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import TIMSORT
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, reverse=True, sort_type=TIMSORT)
        r = list(result)
        self.assertEqual(r, [4, 3, 1, 2, 5]) # 99 not present

    def test_sort_force_timsort_reverse_withlimit(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import TIMSORT
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True, limit=3, sort_type=TIMSORT)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_force_nbest_no_limit_raises(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import NBEST
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError, index.sort, c1, sort_type=NBEST)

    def test_sort_force_nbest(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import NBEST
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, limit=3, sort_type=NBEST)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_force_nbest_reverse_no_limit_raises(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import NBEST
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        self.assertRaises(ValueError,
                          index.sort, c1, reverse=True, sort_type=NBEST)

    def test_sort_force_nbest_reverse(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import NBEST
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5])
        result = index.sort(c1, reverse=True, limit=3, sort_type=NBEST)
        self.assertEqual(list(result), [4, 3, 1])

    def test_sort_force_nbest_missing_docid(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import NBEST
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, limit=3, sort_type=NBEST)
        self.assertEqual(list(result), [5, 2, 1])

    def test_sort_force_nbest_reverse_missing_docid(self):
        from BTrees.IFBTree import IFSet
        from repoze.catalog.indexes.field import NBEST
        index = self._makeOne()
        self._populateIndex(index)
        c1 = IFSet([1, 2, 3, 4, 5, 99])
        result = index.sort(c1, reverse=True, limit=3, sort_type=NBEST)
        self.assertEqual(list(result), [4, 3, 1])

    def test_search_single_range_querymember_or(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        from repoze.catalog import RangeValue
        result = index.search([RangeValue(1,1)])
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_search_double_range_querymember_or(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        from repoze.catalog import RangeValue
        result = index.search([RangeValue(1,1), RangeValue(1,2)])
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_search_double_range_querymember_and(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        from repoze.catalog import RangeValue
        result = index.search([RangeValue(1,1), RangeValue(1,2)], 'and')
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_search_single_int_querymember_or(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.search([1])
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_search_double_int_querymember_or(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.search([1, 2])
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_search_double_int_querymember_and(self):
        # this is a nonsensical query
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.search([1, 2], 'and')
        result = sorted(list(result))
        self.assertEqual(result, [])

    def test_apply_dict_single_range(self):
        from repoze.catalog import RangeValue
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query': RangeValue(1,2)})
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_apply_dict_operator_or_with_ranges(self):
        from repoze.catalog import RangeValue
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[RangeValue(1,1), RangeValue(1,2)],
                              'operator':'or'})
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_apply_dict_operator_and_with_ranges_and(self):
        from repoze.catalog import RangeValue
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[RangeValue(1,1), RangeValue(1,2)],
                              'operator':'and'})
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_apply_dict_operator_and_with_ranges_or(self):
        from repoze.catalog import RangeValue
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[RangeValue(1,1), RangeValue(1,2)],
                              'operator':'or'})
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_apply_dict_operator_or_with_single_int(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':1})
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_apply_dict_operator_or_with_list_of_ints_or(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[1,2]})
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_apply_dict_operator_or_with_list_of_ints_and(self):
        # nonsensical query
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[1, 2], 'operator':'and'})
        result = sorted(list(result))
        self.assertEqual(result, [])

    def test_apply_dict_operator_or_with_int_and_range_or(self):
        from repoze.catalog import RangeValue
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[1, RangeValue(1,2)], 'operator':'or'})
        result = sorted(list(result))
        self.assertEqual(result, [2,5,50])

    def test_apply_dict_operator_or_with_int_and_range_and(self):
        from repoze.catalog import RangeValue
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply({'query':[1, RangeValue(1,2)], 'operator':'and'})
        result = sorted(list(result))
        self.assertEqual(result, [5,50])

    def test_apply_nondict_2tuple(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply((1,2))
        result = sorted(list(result))
        self.assertEqual(result, [2, 5,50])

    def test_apply_nondict_int(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply(1)
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_apply_list(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.apply([1,2])
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_applyEq(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyEq(1)
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_applyNotEq(self):
        index = self._makeOne()
        self._populateIndex(index)
        result = index.applyNotEq(1)
        result = sorted(list(result))
        self.assertEqual(result, [1,2,3,4,6,7,8,9,10,11])

    def test_applyNotEq_returns_unindexed_docs(self):
        def discriminator(obj, default):
            if isinstance(obj, int):
                return obj
            return default

        index = self._makeOne(discriminator)
        self._populateIndex(index)
        index.index_doc(50, 1)
        index.index_doc(51, '1')
        result = index.applyNotEq(1)
        result = sorted(list(result))
        self.assertEqual(result, [1,2,3,4,6,7,8,9,10,11,51])

    def test_applyNotEq_nothing_indexed(self):
        index = self._makeOne('foo')
        self._populateIndex(index)
        result = index.applyNotEq(1)
        result = sorted(list(result))
        self.assertEqual(result, [1,2,3,4,5,6,7,8,9,10,11])

    def test_applyGe(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyGe(10)
        result = sorted(list(result))
        self.assertEqual(result, [10, 11])

    def test_applyGt(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyGt(10)
        result = sorted(list(result))
        self.assertEqual(result, [10])

    def test_applyLe(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyLe(2)
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_applyLt(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyLt(2)
        result = sorted(list(result))
        self.assertEqual(result, [5, 50])

    def test_applyAny(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyAny([1, 2, 60])
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 50])

    def test_applyAny_noresults(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyAny([60, 70])
        result = sorted(list(result))
        self.assertEqual(result, [])

    def test_applyNotAny(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(50, 1)
        result = index.applyNotAny([1, 2, 60])
        result = sorted(list(result))
        self.assertEqual(result, [1, 3, 4, 6, 7, 8, 9, 10, 11])

    def test_applyInRange_inclusive_inclusive(self):
        index = self._makeOne()
        self._populateIndex(index)
        result = index.applyInRange(3, 7)
        result = sorted(list(result))
        self.assertEqual(result, [1, 3, 4, 8, 9])

    def test_applyInRange_inclusive_exclusive(self):
        index = self._makeOne()
        self._populateIndex(index)
        result = index.applyInRange(3, 7, excludemax=True)
        result = sorted(list(result))
        self.assertEqual(result, [1, 3, 4, 8])

    def test_applyInRange_exclusive_inclusive(self):
        index = self._makeOne()
        self._populateIndex(index)
        result = index.applyInRange(3, 7, excludemin=True)
        result = sorted(list(result))
        self.assertEqual(result, [3, 4, 8, 9])

    def test_applyInRange_exclusive_exclusive(self):
        index = self._makeOne()
        self._populateIndex(index)
        result = index.applyInRange(3, 7, excludemin=True, excludemax=True)
        result = sorted(list(result))
        self.assertEqual(result, [3, 4, 8])

    def test_applyNotInRange(self):
        index = self._makeOne()
        self._populateIndex(index)
        result = index.applyNotInRange(3, 7)
        result = sorted(list(result))
        self.assertEqual(result, [2, 5, 6, 7, 10, 11])

    def test_docids(self):
        index = self._makeOne()
        self._populateIndex(index)
        self.assertEqual(
            set(index.docids()),
            set((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)))

    def test_unindex_doc_removes_from_docids(self):
        index = self._makeOne()
        index.index_doc(20, _marker)
        index.unindex_doc(20)
        self.failIf(20 in index.docids())

    def test_index_doc_then_missing_value(self):
        index = self._makeOne()
        self._populateIndex(index)
        self.assertEqual(set([3]), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())

    def test_index_doc_missing_value_then_with_value(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())
        index.index_doc(3, 42)
        self.assertEqual(set([3]), set(index.applyEq(42)))
        self.failUnless(3 in index.docids())

    def test_index_doc_missing_value_then_unindex(self):
        index = self._makeOne()
        self._populateIndex(index)
        index.index_doc(3, _marker)
        self.assertEqual(set(), set(index.applyEq(4)))
        self.failUnless(3 in index.docids())
        index.unindex_doc(3)
        self.assertEqual(set(), set(index.applyEq(4)))
        self.failIf(3 in index.docids())

    def test_docids_with_indexed_and_not_indexed(self):
        index = self._makeOne()
        index.index_doc(1, 1)
        index.index_doc(2, _marker)
        self.assertEqual(set([1, 2]), set(index.docids()))


class Test_fwscan_wins(unittest.TestCase):

    def _callFUT(self, limit, rlen, numdocs):
        from repoze.catalog.indexes.field import fwscan_wins
        return fwscan_wins(limit, rlen, numdocs)

    def test_numdocs_zero_raises(self):
        self.assertRaises(ZeroDivisionError, self._callFUT, None, 100, 0)

    def test_no_limit_rlen_gt_one_fourth_numdocs(self):
        self.failUnless(self._callFUT(None, 25, 100))
        self.failUnless(self._callFUT(None, 26, 100))
        self.failUnless(self._callFUT(None, 50, 100))
        self.failUnless(self._callFUT(None, 75, 100))
        self.failUnless(self._callFUT(None, 99, 100))

    def test_no_limit_rlen_ge_one_fourth_numdocs(self):
        self.failIf(self._callFUT(None, 24, 100))
        self.failIf(self._callFUT(None, 23, 100))
        self.failIf(self._callFUT(None, 15, 100))
        self.failIf(self._callFUT(None, 10, 100))
        self.failIf(self._callFUT(None, 5, 100))
        self.failIf(self._callFUT(None, 2, 100))
        self.failIf(self._callFUT(None, 1, 100))

    def test_w_limit_docratio_ge_512_lt_1024_over_div(self):
        self.failUnless(self._callFUT(1, 512, 65536))
        self.failUnless(self._callFUT(2, 512, 65536))
        self.failUnless(self._callFUT(3, 512, 65536))
        self.failUnless(self._callFUT(4, 512, 65536))
        self.failIf(self._callFUT(5, 512, 65536))
        self.failUnless(self._callFUT(1, 1023, 65536))
        self.failUnless(self._callFUT(2, 1023, 65536))
        self.failUnless(self._callFUT(3, 1023, 65536))
        self.failUnless(self._callFUT(4, 1023, 65536))
        self.failIf(self._callFUT(5, 1023, 65536))

    def test_w_limit_docratio_ge_1024_lt_2048_over_div(self):
        self.failUnless(self._callFUT(1, 1024, 65536))
        self.failUnless(self._callFUT(2, 1024, 65536))
        self.failUnless(self._callFUT(31, 1024, 65536))
        self.failUnless(self._callFUT(32, 1024, 65536))
        self.failIf(self._callFUT(33, 1024, 65536))
        self.failUnless(self._callFUT(1, 2047, 65536))
        self.failUnless(self._callFUT(2, 2047, 65536))
        self.failUnless(self._callFUT(31, 2047, 65536))
        self.failUnless(self._callFUT(32, 2047, 65536))
        self.failIf(self._callFUT(33, 2047, 65536))

    def test_w_limit_docratio_ge_2048_lt_4096_over_div(self):
        self.failUnless(self._callFUT(1, 2048, 65536))
        self.failUnless(self._callFUT(2, 2048, 65536))
        self.failUnless(self._callFUT(127, 2048, 65536))
        self.failUnless(self._callFUT(128, 2048, 65536))
        self.failIf(self._callFUT(129, 2048, 65536))
        self.failUnless(self._callFUT(1, 4095, 65536))
        self.failUnless(self._callFUT(2, 4095, 65536))
        self.failUnless(self._callFUT(127, 4095, 65536))
        self.failUnless(self._callFUT(128, 4095, 65536))
        self.failIf(self._callFUT(129, 4095, 65536))

    def test_w_limit_docratio_ge_4096_lt_8092_over_div(self):
        self.failUnless(self._callFUT(1, 4096, 65536))
        self.failUnless(self._callFUT(2, 4096, 65536))
        self.failUnless(self._callFUT(511, 4096, 65536))
        self.failUnless(self._callFUT(512, 4096, 65536))
        self.failIf(self._callFUT(513, 4096, 65536))
        self.failUnless(self._callFUT(1, 8091, 65536))
        self.failUnless(self._callFUT(2, 8091, 65536))
        self.failUnless(self._callFUT(511, 8091, 65536))
        self.failUnless(self._callFUT(512, 8091, 65536))
        self.failIf(self._callFUT(513, 8091, 65536))

    def test_w_limit_docratio_ge_8192_lt_16384_over_div(self):
        self.failUnless(self._callFUT(1, 8192, 65536))
        self.failUnless(self._callFUT(2, 8192, 65536))
        self.failUnless(self._callFUT(4095, 8192, 65536))
        self.failUnless(self._callFUT(4096, 8192, 65536))
        self.failIf(self._callFUT(4097, 8192, 65536))
        self.failUnless(self._callFUT(1, 16383, 65536))
        self.failUnless(self._callFUT(2, 16383, 65536))
        self.failUnless(self._callFUT(4095, 16383, 65536))
        self.failUnless(self._callFUT(4096, 16383, 65536))
        self.failIf(self._callFUT(4097, 16383, 65536))


class Test_nbest_ascending_wins(unittest.TestCase):

    def _callFUT(self, limit, rlen, numdocs):
        from repoze.catalog.indexes.field import nbest_ascending_wins
        return nbest_ascending_wins(limit, rlen, numdocs)

    def test_wo_limit(self):
        self.failIf(self._callFUT(None, 1, 1000))
        self.failIf(self._callFUT(None, 10, 1000))
        self.failIf(self._callFUT(None, 100, 1000))
        self.failIf(self._callFUT(None, 999, 1000))
        self.failIf(self._callFUT(0, 1, 1000))
        self.failIf(self._callFUT(0, 10, 1000))
        self.failIf(self._callFUT(0, 100, 1000))
        self.failIf(self._callFUT(0, 999, 1000))

    def test_w_limit_numdocs_le_768(self):
        self.failUnless(self._callFUT(1, 100, 100))
        self.failUnless(self._callFUT(10, 100, 100))
        self.failUnless(self._callFUT(99, 100, 100))
        self.failUnless(self._callFUT(1, 100, 767))
        self.failUnless(self._callFUT(10, 100, 767))
        self.failUnless(self._callFUT(99, 100, 767))
        self.failUnless(self._callFUT(1, 100, 768))
        self.failUnless(self._callFUT(10, 100, 768))
        self.failUnless(self._callFUT(99, 100, 768))

    def test_w_limit_docratio_lt_4096_over_div(self):
        self.failUnless(self._callFUT(1, 10, 65536))
        self.failUnless(self._callFUT(2, 10, 65536))
        self.failUnless(self._callFUT(127, 200, 65536))
        self.failUnless(self._callFUT(128, 200, 65536))
        self.failUnless(self._callFUT(3000, 4094, 65536))
        self.failUnless(self._callFUT(3000, 4095, 65536))

    def test_w_limit_docratio_eq_1(self):
        self.failUnless(self._callFUT(1, 65536, 65536))
        self.failUnless(self._callFUT(2, 65536, 65536))
        self.failUnless(self._callFUT(8191, 65536, 65536))
        self.failUnless(self._callFUT(8192, 65536, 65536))
        self.failIf(self._callFUT(8193, 65536, 65536))

    def test_w_limit_docratio_ge_32768_over_div(self):
        self.failUnless(self._callFUT(1, 37268, 65536))
        self.failUnless(self._callFUT(2, 37268, 65536))
        self.failUnless(self._callFUT(4095, 37268, 65536))
        self.failUnless(self._callFUT(4096, 37268, 65536))
        self.failIf(self._callFUT(4097, 37268, 65536))
        self.failUnless(self._callFUT(1, 65535, 65536))
        self.failUnless(self._callFUT(2, 65535, 65536))
        self.failUnless(self._callFUT(4095, 65535, 65536))
        self.failUnless(self._callFUT(4096, 65535, 65536))
        self.failIf(self._callFUT(4097, 65535, 65536))

    def test_w_limit_docratio_ge_4096_lt_32768_over_div(self):
        self.failUnless(self._callFUT(1, 4096, 65536))
        self.failUnless(self._callFUT(2, 4096, 65536))
        self.failUnless(self._callFUT(2047, 4096, 65536))
        self.failUnless(self._callFUT(2048, 4096, 65536))
        self.failIf(self._callFUT(2049, 4096, 65536))
        self.failUnless(self._callFUT(1, 32767, 65536))
        self.failUnless(self._callFUT(2, 32767, 65536))
        self.failUnless(self._callFUT(2047, 32767, 65536))
        self.failUnless(self._callFUT(2048, 32767, 65536))
        self.failIf(self._callFUT(2049, 32767, 65536))
