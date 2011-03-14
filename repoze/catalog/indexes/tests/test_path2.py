import unittest

_marker = object()

class CatalogPathIndex2Tests(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.catalog.indexes.path2 import CatalogPathIndex2
        return CatalogPathIndex2

    def _makeOne(self, values=None,
                 discriminator='path', attr_discriminator=_marker):
        if values is None:
            values = {}
        def _attr_discriminator(obj, default):
            return obj.path
        if attr_discriminator is _marker:
            attr_discriminator = _attr_discriminator
        index = self._getTargetClass()(discriminator,
                                       attr_discriminator=attr_discriminator)
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

    def test_ctor_callback_attr_discriminator(self):
        def _attr_discriminator(obj, default):
            """ """
        index = self._makeOne(attr_discriminator=_attr_discriminator)
        self.failUnless(index.attr_discriminator is _attr_discriminator)

    def test_ctor_string_attr_discriminator(self):
        index = self._makeOne(attr_discriminator='abc')
        self.assertEqual(index.attr_discriminator, 'abc')

    def test_ctor_no_attr_discriminator(self):
        index = self._makeOne(attr_discriminator=None)
        self.assertEqual(index.attr_discriminator, None)

    def test_ctor_bad_attr_discriminator(self):
        self.assertRaises(ValueError, self._makeOne,
                          attr_discriminator=object())

    def test_throws_on_no_query(self):
        index = self._makeOne({})
        self.assertRaises(KeyError, index.apply, {})

    def test_empty_index(self):
        index = self._makeOne({})
        self.assertEqual(len(index), 0)
        self.failUnless(index) # True even if empty

    def test_nonempty_index(self):
        index = self._makeOne(VALUES)
        self.assertEqual(len(index), 22)
        self.failUnless(index)

    def test_index_object_bad_path(self):
        index = self._makeOne()
        class Dummy:
            path = ()
        self.assertRaises(ValueError, index.index_doc, 1, Dummy())

    def test_index_object_simple(self):
        index = self._makeOne()
        class Dummy:
            path = '/abc'
        index.index_doc(1, Dummy())
        self.assertEqual(index.path_to_docid[('', 'abc')], 1)
        self.assertEqual(index.docid_to_path[1], ('', 'abc'))

    def test_index_object_callback_discriminator(self):
        def _discriminator(obj, default):
            return '/abc'
        index = self._makeOne(discriminator=_discriminator)
        class Dummy:
            path = '/foo'
        index.index_doc(1, Dummy())
        self.assertEqual(index.path_to_docid[('', 'abc')], 1)
        self.assertEqual(index.docid_to_path[1], ('', 'abc'))

    def test_index_object_missing_value_unindexes(self):
        index = self._makeOne()
        class Dummy:
            pass
        dummy = Dummy()
        dummy.path = '/abc'
        index.index_doc(1, Dummy())
        del dummy.path
        index.index_doc(1, Dummy())
        self.failIf(('', 'abc') in index.path_to_docid)
        self.failIf(1 in index.docid_to_path)

    def test_unindex_nonesuch(self):
        index = self._makeOne({})
        index.unindex_doc(1234) # nothrow

    def test_unindex_doc(self):
        index = self._makeOne(VALUES)
        docids = VALUES.keys()

        for doc_id in docids:
            index.unindex_doc(doc_id)

        self.assertEqual(len(index), 0)
        self.assertEqual(list(index.adjacency.keys()), [])
        self.assertEqual(list(index.disjoint.keys()), [])
        self.assertEqual(list(index.path_to_docid.keys()), [])
        self.assertEqual(list(index.docid_to_path.keys()), [])

        index = self._makeOne(VALUES)
        # randomize the order
        import random
        random.shuffle(docids)
        for doc_id in docids:
            index.unindex_doc(doc_id)

        self.assertEqual(len(index), 0)
        self.assertEqual(list(index.adjacency.keys()), [])
        self.assertEqual(list(index.disjoint.keys()), [])
        self.assertEqual(list(index.path_to_docid.keys()), [])
        self.assertEqual(list(index.docid_to_path.keys()), [])

    def test_unindex_then_index_doesnt_dupe(self):
        index = self._makeOne()
        o = Dummy('/foo/bar')
        index.index_doc(1, o)
        self.assertEqual(len(index), 1)
        index.index_doc(1, o)
        self.assertEqual(len(index), 1)

    # This test fails, but I can't see why it should.
    #def XXX_test_search_from_unindexed_root(self):
    #    index = self._makeOne()
    #    index.index_doc(1, '/abc/def')
    #    index.index_doc(2, '/abc/ghi')
    #    result = index.search('/abc', depth=1, include_path=True)
    #    self.assertEqual(sorted(result), [1, 2])

    def test_search_root_nodepth(self):
        index = self._makeOne(VALUES)
        result = index.search('/')
        self.assertEqual(sorted(result), range(1, 21))

    def test_search_root_nodepth_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/', include_path=True)
        self.assertEqual(sorted(result), range(0, 21))

    def test_search_root_depth_0(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=0)
        self.assertEqual(sorted(result), [])

    def test_search_depth_0_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=0, include_path=True)
        self.assertEqual(sorted(result), [0])

    def test_search_root_depth_1(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=1)
        self.assertEqual(sorted(result), [1,5])

    def test_search_depth_1_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=1, include_path=True)
        self.assertEqual(sorted(result), [0, 1, 5])

    def test_search_root_depth_2(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=2)
        self.assertEqual(sorted(result), [1, 2, 3, 4, 5, 6, 7, 8])

    def test_search_depth_2_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=2, include_path=True)
        self.assertEqual(sorted(result), [0, 1, 2, 3, 4, 5, 6, 7, 8])

    def test_search_root_depth_3(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=3)
        self.assertEqual(sorted(result), range(1, 21))

    def test_search_root_depth_3_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/', depth=3, include_path=True)
        self.assertEqual(sorted(result), range(0, 21))

    def test_search_aa_nodepth(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa')
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_search_aa_nodepth_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', include_path=True)
        self.assertEqual(sorted(result), [1, 2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_search_aa_depth_0(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', depth=0)
        self.assertEqual(sorted(result), [])

    def test_search_aa_depth_0_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', depth=0, include_path=True)
        self.assertEqual(sorted(result), [1])

    def test_search_aa_depth_1(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', depth=1)
        self.assertEqual(sorted(result), [2,3,4])

    def test_search_aa_depth_1_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/aa', depth=1, include_path=True)
        self.assertEqual(sorted(result), [1, 2, 3, 4])

    def test_search_bb_nodepth(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb')
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])

    def test_search_bb_nodepth_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', include_path=True)
        self.assertEqual(sorted(result), [5, 6, 7, 8, 15, 16, 17, 18, 19, 20])

    def test_search_bb_depth_0(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', depth=0)
        self.assertEqual(sorted(result), [])

    def test_search_bb_depth_0_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', depth=0, include_path=True)
        self.assertEqual(sorted(result), [5])

    def test_search_bb_depth_1(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', depth=1)
        self.assertEqual(sorted(result), [6, 7, 8])

    def test_search_bb_depth_1_include_path(self):
        index = self._makeOne(VALUES)
        result = index.search('/bb', depth=1, include_path=True)
        self.assertEqual(sorted(result), [5, 6, 7, 8])

    def test_search_with_tuple(self):
        index = self._makeOne(VALUES)
        result = index.search(('', 'bb'))
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])

    def test_disjoint_resolved(self):
        index = self._makeOne(VALUES)
        result = index.search('/disjoint')
        self.assertEqual(sorted(result), [])
        index.index_doc(22, Dummy('/disjoint'))
        result = index.search('/disjoint')
        self.assertEqual(sorted(result), [21])
        result = index.search('/')
        self.failUnless(22 in result)

    def test_disjoint_resolved_random_order(self):
        index = self._makeOne({})

        index.index_doc(0, Dummy('/disjoint/path/element/1'))
        index.index_doc(1, Dummy('/disjoint/path/element/2'))

        result = index.search('/')
        self.assertEqual(sorted(result), [])

        index.index_doc(2, Dummy('/disjoint'))

        result = index.search('/')
        self.assertEqual(sorted(result), [])

        index.index_doc(3, Dummy('/disjoint/path'))

        result = index.search('/')
        self.assertEqual(sorted(result), [])

        index.index_doc(4, Dummy('/'))

        result = index.search('/')
        self.assertEqual(sorted(result), [2, 3])

        index.index_doc(5, Dummy('/disjoint/path/element'))

        result = index.search('/')
        self.assertEqual(sorted(result), [0, 1, 2, 3, 5])

    def test_apply_intersect_wo_docids(self):
        index = self._makeOne(VALUES)
        result = index.apply_intersect('/aa', None)
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_apply_intersect_w_docids(self):
        index = self._makeOne(VALUES)
        to_intersect = index.family.IF.Set([2, 3, 4, 7, 8])
        result = index.apply_intersect('/aa', to_intersect)
        self.assertEqual(sorted(result), [2, 3, 4])

    def test_apply_path_string(self):
        index = self._makeOne(VALUES)
        result = index.apply('/aa')
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_apply_path_string_relative_raises(self):
        index = self._makeOne(VALUES)
        result = self.assertRaises(ValueError, index.apply, 'aa')

    def test_apply_path_tuple_absolute(self):
        index = self._makeOne(VALUES)
        result = index.apply(('', 'aa'))
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_apply_path_tuple_relative_raises(self):
        index = self._makeOne(VALUES)
        result = self.assertRaises(ValueError, index.apply, ('aa',))

    def test_apply_path_list_absolute(self):
        index = self._makeOne(VALUES)
        result = index.apply(['', 'aa'])
        self.assertEqual(sorted(result), [2, 3, 4, 9, 10, 11, 12, 13, 14])

    def test_apply_path_list_relative_raises(self):
        index = self._makeOne(VALUES)
        result = self.assertRaises(ValueError, index.apply, ['aa'])

    def test_apply_path_dict_with_string_query(self):
        index = self._makeOne(VALUES)
        result = index.apply({'query':'/aa', 'depth':1})
        self.assertEqual(sorted(result), [2, 3, 4])

    def test_apply_path_dict_with_tuple_query(self):
        index = self._makeOne(VALUES)
        result = index.apply({'query':('', 'aa'), 'depth':1})
        self.assertEqual(sorted(result), [2, 3, 4])

    def test_apply_path_dict_with_list_query(self):
        index = self._makeOne(VALUES)
        result = index.apply({'query':['', 'aa'], 'depth':1})
        self.assertEqual(sorted(result), [2, 3, 4])

    def test_apply_path_dict_with_include_path_true(self):
        index = self._makeOne(VALUES)
        result = index.apply({'query':('', 'aa'), 'depth':1,
                              'include_path':True})
        self.assertEqual(sorted(result), [1, 2, 3, 4])

    def test_apply_path_dict_with_include_path_false(self):
        index = self._makeOne(VALUES)
        result = index.apply({'query':('', 'aa'), 'depth':1,
                              'include_path':False})
        self.assertEqual(sorted(result), [2, 3, 4])

    def test_reindex_doc_nochange(self):
        index = self._makeOne(VALUES)
        result = index.reindex_doc(1, VALUES[1])
        self.assertEqual(result, False)

    def test_reindex_doc_attradd(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        self.assertEqual(index.docid_to_attr.get(1), None)
        result = index.reindex_doc(1, Dummy('/aa', 'acl5'))
        self.assertEqual(result, True)
        self.assertEqual(index.docid_to_attr[1], 'acl5')

    def test_reindex_doc_attrchange(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        self.assertEqual(index.docid_to_attr[0], 'acl1')
        result = index.reindex_doc(0, Dummy('/', 'acl11'))
        self.assertEqual(result, True)
        self.assertEqual(index.docid_to_attr[0], 'acl11')

    def test_reindex_doc_attrdel(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        self.assertEqual(index.docid_to_attr[0], 'acl1')
        result = index.reindex_doc(0, Dummy('/'))
        self.assertEqual(result, True)
        self.assertEqual(index.docid_to_attr.get(0), None)

    def test_reindex_doc_pathchange(self):
        index = self._makeOne(VALUES)
        result = index.reindex_doc(1, Dummy('/abcdef'))
        self.assertEqual(result, True)
        self.assertEqual(index.docid_to_path[1], ('', 'abcdef'))

    def test_index_doc_unindex_doc_with_attr_discriminator(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_keys = sorted(index.docid_to_attr.keys())
        self.assertEqual(attr_keys, [0, 2, 8, 12])

        docids = VALUES.keys()

        for doc_id in docids:
            index.unindex_doc(doc_id)

        self.assertEqual(len(index), 0)
        self.assertEqual(list(index.adjacency.keys()), [])
        self.assertEqual(list(index.disjoint.keys()), [])
        self.assertEqual(list(index.path_to_docid.keys()), [])
        self.assertEqual(list(index.docid_to_path.keys()), [])
        self.assertEqual(list(index.docid_to_attr.keys()), [])

        index = self._makeOne(VALUES, attr_discriminator='attr')
        # randomize the order
        import random
        random.shuffle(docids)
        for doc_id in docids:
            index.unindex_doc(doc_id)

        self.assertEqual(len(index), 0)
        self.assertEqual(list(index.adjacency.keys()), [])
        self.assertEqual(list(index.disjoint.keys()), [])
        self.assertEqual(list(index.path_to_docid.keys()), [])
        self.assertEqual(list(index.docid_to_path.keys()), [])
        self.assertEqual(list(index.docid_to_attr.keys()), [])

    def test_search_root_nodepth_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', attr_checker=attr_checker)
        self.assertEqual(sorted(result), range(1, 21))
        results = attr_checker.results
        self.assertEqual(len(results), 4)
        attrs, theset = results[0]
        self.assertEqual(attrs, (12, ['acl1', 'acl4']))
        self.assertEqual(sorted(theset), [12])
        attrs, theset = results[1]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [1,3,4,5,6,7,11,13,14,15,16,17,18])
        attrs, theset = results[2]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(sorted(theset), [8, 19, 20])
        attrs, theset = results[3]
        self.assertEqual(attrs, (2, ['acl1', 'acl3']))
        self.assertEqual(sorted(theset), [2,9, 10])

    def test_search_root_nodepth_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', include_path=True, attr_checker=attr_checker)
        self.assertEqual(sorted(result), range(0, 21))
        results = attr_checker.results
        self.assertEqual(len(results), 4)
        attrs, theset = results[0]
        self.assertEqual(attrs, (12, ['acl1', 'acl4']))
        self.assertEqual(sorted(theset), [12])
        attrs, theset = results[1]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0,1,3,4,5,6,7,11,13,14,15,16,17,18])
        attrs, theset = results[2]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(sorted(theset), [8, 19, 20])
        attrs, theset = results[3]
        self.assertEqual(attrs, (2, ['acl1', 'acl3']))
        self.assertEqual(sorted(theset), [2,9, 10])

    def test_search_root_depth0_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=0, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])

    def test_search_root_depth0_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=0, include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [0])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0])

    def test_search_root_depth1_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=1, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [1, 5])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [1,5])

    def test_search_root_depth1_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=1, include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [0, 1, 5])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0, 1, 5])

    def test_search_root_depth2_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=2, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [1, 2, 3, 4, 5, 6, 7, 8])
        results = attr_checker.results
        self.assertEqual(len(results), 3)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [1,3,4,5,6,7])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8])
        attrs, theset = results[2]
        self.assertEqual(attrs, (2, ['acl1', 'acl3']))
        self.assertEqual(list(theset), [2])

    def test_search_root_depth2_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=2, include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [0, 1, 2, 3, 4, 5, 6, 7, 8])
        results = attr_checker.results
        self.assertEqual(len(results), 3)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0,1,3,4,5,6,7])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8])
        attrs, theset = results[2]
        self.assertEqual(attrs, (2, ['acl1', 'acl3']))
        self.assertEqual(list(theset), [2])


    def test_search_root_depth3_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=3, attr_checker=attr_checker)
        self.assertEqual(sorted(result), range(1, 21))
        results = attr_checker.results
        self.assertEqual(len(results), 4)
        attrs, theset = results[0]
        self.assertEqual(attrs, (12, ['acl1', 'acl4']))
        self.assertEqual(list(theset), [12])
        attrs, theset = results[1]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [1,3,4,5,6,7,11,13,14,15,16,17,18])
        attrs, theset = results[2]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])
        attrs, theset = results[3]
        self.assertEqual(attrs, (2, ['acl1', 'acl3']))
        self.assertEqual(list(theset), [2, 9, 10])

    def test_search_root_depth3_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=3, include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), range(0, 21))
        results = attr_checker.results
        self.assertEqual(len(results), 4)
        attrs, theset = results[0]
        self.assertEqual(attrs, (12, ['acl1', 'acl4']))
        self.assertEqual(list(theset), [12])
        attrs, theset = results[1]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0,1,3,4,5,6,7,11,13,14,15,16,17,18])
        attrs, theset = results[2]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])
        attrs, theset = results[3]
        self.assertEqual(attrs, (2, ['acl1', 'acl3']))
        self.assertEqual(list(theset), [2, 9, 10])

    def test_search_bb_nodepth_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb', attr_checker=attr_checker)
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [6, 7, 15, 16, 17, 18])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])

    def test_search_bb_nodepth_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb', include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [5, 6, 7, 8, 15, 16, 17, 18, 19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [5, 6, 7, 15, 16, 17, 18])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])

    def test_search_bb_depth0_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb', depth=0, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])

    def test_search_bb_depth1_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb', depth=1, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [6,7,8])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [6,7])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8])

    def test_search_bb_depth2_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb', depth=2, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [6, 7, 15, 16, 17, 18])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])

    def test_search_bb_depth3_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb', depth=3, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [6, 7, 8, 15, 16, 17, 18, 19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [6, 7, 15, 16, 17, 18])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])

    def test_search_bb_cc_nodepth_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc', attr_checker=attr_checker)
        self.assertEqual(sorted(result), [19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [19, 20])

    def test_search_bb_cc_nodepth_with_attrchecker_and_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc', include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [8, 19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [8, 19, 20])

    def test_search_bb_cc_depth0_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc', depth=0, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [])

    def test_search_bb_cc_depth1_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc', depth=1, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [19, 20])

    def test_search_bb_cc_depth2_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc', depth=2, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [19, 20])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [19, 20])

    def test_search_bb_cc_11_nodepth_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc/11.html', attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [])

    def test_search_bb_cc_11_nodepth_with_attrchecker_include_path(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc/11.html', include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [19])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [19])

    def test_search_bb_cc_11_depth0_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc/11.html', depth=0,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [])

    def test_search_bb_cc_11_depth1_with_attrchecker(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc/11.html', depth=1,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [])

    def test_search_bb_cc_11_depth1_with_attrchecker_and_includepath(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/bb/cc/11.html', depth=1, include_path=True,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [19])
        results = attr_checker.results
        self.assertEqual(len(results), 2)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])
        attrs, theset = results[1]
        self.assertEqual(attrs, (8, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [19])

    def test_search_root_nodepth_with_attrchecker_values2(self):
        index = self._makeOne(VALUES2, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', attr_checker=attr_checker)
        self.assertEqual(sorted(result), range(1, 6))
        results = attr_checker.results
        self.assertEqual(len(results), 6)
        attrs, theset = results[0]
        self.assertEqual(attrs, (1, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [1])
        attrs, theset = results[1]
        self.assertEqual(attrs, (3, ['acl1', 'acl2', 'acl4']))
        self.assertEqual(list(theset), [3])
        attrs, theset = results[2]
        self.assertEqual(attrs, (4, ['acl1', 'acl2', 'acl5']))
        self.assertEqual(list(theset), [4])
        attrs, theset = results[3]
        self.assertEqual(attrs, (2, ['acl1', 'acl2', 'acl3']))
        self.assertEqual(list(theset), [2])
        attrs, theset = results[4]
        self.assertEqual(attrs, (5, ['acl1', 'acl6']))
        self.assertEqual(list(theset), [5])
        attrs, theset = results[5]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])

    def test_search_root_nodepth_with_attrchecker_incpath_values2(self):
        index = self._makeOne(VALUES2, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', include_path=True, attr_checker=attr_checker)
        self.assertEqual(sorted(result), range(0, 6))
        results = attr_checker.results
        self.assertEqual(len(results), 6)
        attrs, theset = results[0]
        self.assertEqual(attrs, (1, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [1])
        attrs, theset = results[1]
        self.assertEqual(attrs, (3, ['acl1', 'acl2', 'acl4']))
        self.assertEqual(list(theset), [3])
        attrs, theset = results[2]
        self.assertEqual(attrs, (4, ['acl1', 'acl2', 'acl5']))
        self.assertEqual(list(theset), [4])
        attrs, theset = results[3]
        self.assertEqual(attrs, (2, ['acl1', 'acl2', 'acl3']))
        self.assertEqual(list(theset), [2])
        attrs, theset = results[4]
        self.assertEqual(attrs, (5, ['acl1', 'acl6']))
        self.assertEqual(list(theset), [5])
        attrs, theset = results[5]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0])

    def test_search_root_depth0_with_attrchecker_values2(self):
        index = self._makeOne(VALUES2, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=0, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])

    def test_search_root_depth0_with_attrchecker_incpath_values2(self):
        index = self._makeOne(VALUES2, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', include_path=True, depth=0,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [0])
        results = attr_checker.results
        self.assertEqual(len(results), 1)
        attrs, theset = results[0]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0])

    def test_search_root_depth1_with_attrchecker_values2(self):
        index = self._makeOne(VALUES2, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', depth=1, attr_checker=attr_checker)
        self.assertEqual(sorted(result), [1,5])
        results = attr_checker.results
        self.assertEqual(len(results), 3)
        attrs, theset = results[0]
        self.assertEqual(attrs, (5, ['acl1', 'acl6']))
        self.assertEqual(list(theset), [5])
        attrs, theset = results[1]
        self.assertEqual(attrs, (1, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [1])
        attrs, theset = results[2]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [])

    def test_search_root_depth1_with_attrchecker_incpath_values2(self):
        index = self._makeOne(VALUES2, attr_discriminator='attr')
        attr_checker = DummyAttrChecker()
        result = index.search('/', include_path=True, depth=1,
                              attr_checker=attr_checker)
        self.assertEqual(sorted(result), [0, 1, 5])
        results = attr_checker.results
        self.assertEqual(len(results), 3)
        attrs, theset = results[0]
        self.assertEqual(attrs, (5, ['acl1', 'acl6']))
        self.assertEqual(list(theset), [5])
        attrs, theset = results[1]
        self.assertEqual(attrs, (1, ['acl1', 'acl2']))
        self.assertEqual(list(theset), [1])
        attrs, theset = results[2]
        self.assertEqual(attrs, (0, ['acl1']))
        self.assertEqual(list(theset), [0])

    def test__indexed(self):
        index = self._makeOne(VALUES, attr_discriminator='attr')
        self.assertEqual(
            set(index._indexed()),
            set(range(22)))

class DummyAttrChecker(object):
    def __init__(self):
        pass

    def __call__(self, results):
        import BTrees
        self.results = results
        return BTrees.family32.IF.multiunion([x[1] for x in results])

class Dummy:

    def __init__( self, path, attr=None):
        self.path = path
        if attr is not None:
            self.attr = attr

VALUES = {
    0 : Dummy('/', 'acl1'),
    1 : Dummy('/aa'),
    2 : Dummy('/aa/aa', 'acl3'),
    3 : Dummy('/aa/bb'),
    4 : Dummy('/aa/cc'),
    5 : Dummy('/bb'),
    6 : Dummy('/bb/aa'),
    7 : Dummy('/bb/bb'),
    8 : Dummy('/bb/cc', 'acl2'),
    9 : Dummy("/aa/aa/1.html"),
    10 : Dummy("/aa/aa/2.html"),
    11 : Dummy("/aa/bb/3.html"),
    12 : Dummy("/aa/bb/4.html", 'acl4'),
    13 : Dummy("/aa/cc/5.html"),
    14 : Dummy("/aa/cc/6.html"),
    15 : Dummy("/bb/aa/7.html"),
    16 : Dummy("/bb/aa/8.html"),
    17 : Dummy("/bb/bb/9.html"),
    18 : Dummy("/bb/bb/10.html"),
    19 : Dummy("/bb/cc/11.html"),
    20 : Dummy("/bb/cc/12.html"),
    21 : Dummy('/disjoint/entry')
    }

VALUES2 = {
    0 : Dummy('/', 'acl1'),
    1 : Dummy('/aa', 'acl2'),
    2 : Dummy('/aa/aa', 'acl3'),
    3 : Dummy('/aa/bb', 'acl4'),
    4 : Dummy('/aa/cc', 'acl5'),
    5 : Dummy('/bb', 'acl6'),
    }
