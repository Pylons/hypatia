import unittest

class ConformsToIQueryParseTree:

    def test_class_conforms_to_IQueryParseTree(self):
        from zope.interface.verify import verifyClass
        from ..interfaces import IQueryParseTree
        verifyClass(IQueryParseTree, self._getTargetClass())

    def test_instance_conforms_to_IQueryParseTree(self):
        from zope.interface.verify import verifyObject
        from ..interfaces import IQueryParseTree
        verifyObject(IQueryParseTree, self._makeOne())

class ParseTreeNodeTests(unittest.TestCase, ConformsToIQueryParseTree):

    def _getTargetClass(self):
        from ..parsetree import ParseTreeNode
        return ParseTreeNode

    def _makeOne(self, value=None):
        if value is None:
            value = [FauxValue('XXX')]
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), None)

    def test_getValue(self):
        value = [FauxValue('XXX')]
        node = self._makeOne(value)
        self.assertEqual(node.getValue(), value)

    def test___repr__(self):
        node = self._makeOne()
        self.assertEqual(repr(node), "ParseTreeNode([FV:XXX])")

    def test___repr___subclass(self):
        class Derived(self._getTargetClass()):
            pass
        node = Derived('XXX')
        self.assertEqual(repr(node), "Derived('XXX')")

    def test_terms(self):
        node = self._makeOne()
        self.assertEqual(list(node.terms()), ['XXX'])

    def test_executeQuery_raises(self):
        node = self._makeOne()
        self.assertRaises(NotImplementedError, node.executeQuery, FauxIndex())

class NotNodeTests(unittest.TestCase, ConformsToIQueryParseTree):

    def _getTargetClass(self):
        from ..parsetree import NotNode
        return NotNode

    def _makeOne(self, value=None):
        if value is None:
            value = [FauxValue('XXX')]
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), 'NOT')

    def test_terms(self):
        node = self._makeOne(object())
        self.assertEqual(list(node.terms()), [])

    def test_executeQuery_raises(self):
        from ..parsetree import QueryError
        node = self._makeOne()
        self.assertRaises(QueryError, node.executeQuery, FauxIndex())

class BucketMaker:

    def _makeBucket(self, index, count, start=0):
        bucket = index.family.IF.Bucket()
        for i in range(start, count):
            bucket[i] = count * 3.1415926
        return bucket

class AndNodeTests(unittest.TestCase, ConformsToIQueryParseTree, BucketMaker):

    def _getTargetClass(self):
        from ..parsetree import AndNode
        return AndNode

    def _makeOne(self, value=None):
        if value is None:
            value = [FauxValue('XXX')]
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), 'AND')

    def test_executeQuery_no_results(self):
        node = self._makeOne([FauxSubnode('FOO', None)])
        result = node.executeQuery(FauxIndex())
        self.assertEqual(dict(result), {})

    def test_executeQuery_w_positive_results(self):
        index = FauxIndex()
        node = self._makeOne(
                    [FauxSubnode('FOO', self._makeBucket(index, 5)),
                     FauxSubnode('FOO', self._makeBucket(index, 6)),
                    ])
        result = node.executeQuery(index)
        self.assertEqual(sorted(result.keys()), [0, 1, 2, 3, 4])

    def test_executeQuery_w_negative_results(self): # TODO
        index = FauxIndex()
        node = self._makeOne(
                    [FauxSubnode('NOT', self._makeBucket(index, 5)),
                     FauxSubnode('FOO', self._makeBucket(index, 6)),
                    ])
        result = node.executeQuery(index)
        self.assertEqual(sorted(result.keys()), [5])

class OrNodeTests(unittest.TestCase, ConformsToIQueryParseTree, BucketMaker):

    def _getTargetClass(self):
        from ..parsetree import OrNode
        return OrNode

    def _makeOne(self, value=None):
        if value is None:
            value = [FauxValue('XXX')]
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), 'OR')

    def test_executeQuery_no_results(self):
        node = self._makeOne([FauxSubnode('FOO', None)])
        result = node.executeQuery(FauxIndex())
        self.assertEqual(dict(result), {})

    def test_executeQuery_w_results(self):
        index = FauxIndex()
        node = self._makeOne(
                    [FauxSubnode('FOO', self._makeBucket(index, 5)),
                     FauxSubnode('FOO', self._makeBucket(index, 6)),
                    ])
        result = node.executeQuery(index)
        self.assertEqual(sorted(result.keys()), [0, 1, 2, 3, 4, 5])

class AtomNodeTests(unittest.TestCase, ConformsToIQueryParseTree, BucketMaker):

    def _getTargetClass(self):
        from ..parsetree import AtomNode
        return AtomNode

    def _makeOne(self, value=None):
        if value is None:
            value = 'XXX'
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), 'ATOM')

    def test_terms(self):
        node = self._makeOne()
        self.assertEqual(node.terms(), ['XXX'])

    def test_executeQuery(self):
        node = self._makeOne()
        index = FauxIndex()
        index.search = lambda term:  self._makeBucket(index, 5)
        result = node.executeQuery(index)
        self.assertEqual(sorted(result.keys()), [0, 1, 2, 3, 4])

class PhraseNodeTests(unittest.TestCase, ConformsToIQueryParseTree):

    def _getTargetClass(self):
        from ..parsetree import PhraseNode
        return PhraseNode

    def _makeOne(self, value=None):
        if value is None:
            value = 'XXX YYY'
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), 'PHRASE')

    def test_executeQuery(self):
        _called_with = []
        def _search(*args, **kw):
            _called_with.append((args, kw))
            return []
        index = FauxIndex()
        index.search_phrase = _search
        node = self._makeOne()
        self.assertEqual(node.executeQuery(index), [])
        self.assertEqual(_called_with[0], (('XXX YYY',), {}))

class GlobNodeTests(unittest.TestCase, ConformsToIQueryParseTree):

    def _getTargetClass(self):
        from ..parsetree import GlobNode
        return GlobNode

    def _makeOne(self, value=None):
        if value is None:
            value = 'XXX*'
        return self._getTargetClass()(value)

    def test_nodeType(self):
        node = self._makeOne()
        self.assertEqual(node.nodeType(), 'GLOB')

    def test_executeQuery(self):
        _called_with = []
        def _search(*args, **kw):
            _called_with.append((args, kw))
            return []
        index = FauxIndex()
        index.search_glob = _search
        node = self._makeOne()
        self.assertEqual(node.executeQuery(index), [])
        self.assertEqual(_called_with[0], (('XXX*',), {}))

class FauxIndex(object):

    def _get_family(self):
        import BTrees
        return BTrees.family32

    family = property(_get_family,)

class FauxValue:
    def __init__(self, *terms):
        self._terms = terms[:]
    def terms(self):
        return self._terms
    def __repr__(self):
        return 'FV:%s' % ' '.join(self._terms)


class FauxSubnode:
    def __init__(self, node_type, query_results):
        self._nodeType = node_type
        self._query_results = query_results
    def nodeType(self):
        return self._nodeType
    def executeQuery(self, index):
        return self._query_results
    def getValue(self):
        return self

