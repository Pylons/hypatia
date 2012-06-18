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
"""Query Parser
"""
import unittest


class TestQueryParserBase(unittest.TestCase):

    def _getTargetClass(self):
        from ..queryparser import QueryParser
        return QueryParser

    def _makeOne(self, lexicon=None):
        if lexicon is None:
            lexicon = self._makeLexicon()
        return self._getTargetClass()(lexicon)

    def _makePipeline(self):
        from ..lexicon import Splitter
        return (Splitter(),)

    def _makeLexicon(self):
        from ..lexicon import Lexicon
        return Lexicon(*self._makePipeline())

    def _expect(self, parser, input, output, expected_ignored=[]):
        tree = parser.parseQuery(input)
        ignored = parser.getIgnored()
        self._compareParseTrees(tree, output)
        self.assertEqual(ignored, expected_ignored)
        # Check that parseQueryEx() == (parseQuery(), getIgnored())
        ex_tree, ex_ignored = parser.parseQueryEx(input)
        self._compareParseTrees(ex_tree, tree)
        self.assertEqual(ex_ignored, expected_ignored)

    def _failure(self, parser, input):
        from ..parsetree import ParseError
        self.assertRaises(ParseError, parser.parseQuery, input)
        self.assertRaises(ParseError, parser.parseQueryEx, input)

    def _compareParseTrees(self, got, expected, msg=None):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import GlobNode
        from ..parsetree import NotNode
        from ..parsetree import OrNode
        from ..parsetree import ParseTreeNode
        from ..parsetree import PhraseNode
        if msg is None:
            msg = repr(got)
        self.assertEqual(isinstance(got, ParseTreeNode), 1)
        self.assertEqual(got.__class__, expected.__class__, msg)
        if isinstance(got, PhraseNode):
            self.assertEqual(got.nodeType(), "PHRASE", msg)
            self.assertEqual(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, GlobNode):
            self.assertEqual(got.nodeType(), "GLOB", msg)
            self.assertEqual(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, AtomNode):
            self.assertEqual(got.nodeType(), "ATOM", msg)
            self.assertEqual(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, NotNode):
            self.assertEqual(got.nodeType(), "NOT")
            self._compareParseTrees(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, AndNode) or isinstance(got, OrNode):
            self.assertEqual(got.nodeType(),
                             isinstance(got, AndNode) and "AND" or "OR", msg)
            list1 = got.getValue()
            list2 = expected.getValue()
            self.assertEqual(len(list1), len(list2), msg)
            for i in range(len(list1)):
                self._compareParseTrees(list1[i], list2[i], msg)


class TestQueryParser(TestQueryParserBase):

    def test_class_conforms_to_IQueryParser(self):
        from zope.interface.verify import verifyClass
        from ..interfaces import IQueryParser
        verifyClass(IQueryParser, self._getTargetClass())

    def test_instance_conforms_to_IQueryParser(self):
        from zope.interface.verify import verifyObject
        from ..interfaces import IQueryParser
        verifyObject(IQueryParser, self._makeOne())

    def test001(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, "foo", AtomNode("foo"))

    def test002(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, "note", AtomNode("note"))

    def test003(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, "aa and bb AND cc",
                    AndNode([AtomNode("aa"), AtomNode("bb"), AtomNode("cc")]))

    def test004(self):
        from ..parsetree import OrNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, "aa OR bb or cc",
                    OrNode([AtomNode("aa"), AtomNode("bb"), AtomNode("cc")]))

    def test005(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import OrNode
        parser = self._makeOne()
        self._expect(parser, "aa AND bb OR cc AnD dd",
                    OrNode([AndNode([AtomNode("aa"), AtomNode("bb")]),
                            AndNode([AtomNode("cc"), AtomNode("dd")])]))

    def test006(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import OrNode
        parser = self._makeOne()
        self._expect(parser, "(aa OR bb) AND (cc OR dd)",
                    AndNode([OrNode([AtomNode("aa"), AtomNode("bb")]),
                             OrNode([AtomNode("cc"), AtomNode("dd")])]))

    def test007(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        parser = self._makeOne()
        self._expect(parser, "aa AND NOT bb",
                    AndNode([AtomNode("aa"), NotNode(AtomNode("bb"))]))

    def test008(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        parser = self._makeOne()
        self._expect(parser, "aa NOT bb",
                    AndNode([AtomNode("aa"), NotNode(AtomNode("bb"))]))

    def test010(self):
        from ..parsetree import PhraseNode
        parser = self._makeOne()
        self._expect(parser, '"foo bar"', PhraseNode(["foo", "bar"]))

    def test011(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, "foo bar",
                     AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test012(self):
        from ..parsetree import PhraseNode
        parser = self._makeOne()
        self._expect(parser, '(("foo bar"))"', PhraseNode(["foo", "bar"]))

    def test013(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, "((foo bar))",
                     AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test014(self):
        from ..parsetree import PhraseNode
        parser = self._makeOne()
        self._expect(parser, "foo-bar", PhraseNode(["foo", "bar"]))

    def test015(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        parser = self._makeOne()
        self._expect(parser, "foo -bar", AndNode([AtomNode("foo"),
                                         NotNode(AtomNode("bar"))]))

    def test016(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        parser = self._makeOne()
        self._expect(parser, "-foo bar", AndNode([AtomNode("bar"),
                                         NotNode(AtomNode("foo"))]))

    def test017(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        from ..parsetree import PhraseNode
        parser = self._makeOne()
        self._expect(parser, "booh -foo-bar",
                    AndNode([AtomNode("booh"),
                             NotNode(PhraseNode(["foo", "bar"]))]))

    def test018(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import NotNode
        from ..parsetree import PhraseNode
        parser = self._makeOne()
        self._expect(parser, 'booh -"foo bar"',
                     AndNode([AtomNode("booh"),
                             NotNode(PhraseNode(["foo", "bar"]))]))

    def test019(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'foo"bar"',
                     AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test020(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, '"foo"bar',
                    AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test021(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'foo"bar"blech',
                    AndNode([AtomNode("foo"), AtomNode("bar"),
                             AtomNode("blech")]))

    def test022(self):
        from ..parsetree import GlobNode
        parser = self._makeOne()
        self._expect(parser, "foo*", GlobNode("foo*"))

    def test023(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        from ..parsetree import GlobNode
        parser = self._makeOne()
        self._expect(parser, "foo* bar",
                     AndNode([GlobNode("foo*"), AtomNode("bar")]))

    def test101(self):
        parser = self._makeOne()
        self._failure(parser, "")

    def test102(self):
        parser = self._makeOne()
        self._failure(parser, "not")

    def test103(self):
        parser = self._makeOne()
        self._failure(parser, "or")

    def test104(self):
        parser = self._makeOne()
        self._failure(parser, "and")

    def test105(self):
        parser = self._makeOne()
        self._failure(parser, "NOT")

    def test106(self):
        parser = self._makeOne()
        self._failure(parser, "OR")

    def test107(self):
        parser = self._makeOne()
        self._failure(parser, "AND")

    def test108(self):
        parser = self._makeOne()
        self._failure(parser, "NOT foo")

    def test109(self):
        parser = self._makeOne()
        self._failure(parser, ")")

    def test110(self):
        parser = self._makeOne()
        self._failure(parser, "(")

    def test111(self):
        parser = self._makeOne()
        self._failure(parser, "foo OR")

    def test112(self):
        parser = self._makeOne()
        self._failure(parser, "foo AND")

    def test113(self):
        parser = self._makeOne()
        self._failure(parser, "OR foo")

    def test114(self):
        parser = self._makeOne()
        self._failure(parser, "AND foo")

    def test115(self):
        parser = self._makeOne()
        self._failure(parser, "(foo) bar")

    def test116(self):
        parser = self._makeOne()
        self._failure(parser, "(foo OR)")

    def test117(self):
        parser = self._makeOne()
        self._failure(parser, "(foo AND)")

    def test118(self):
        parser = self._makeOne()
        self._failure(parser, "(NOT foo)")

    def test119(self):
        parser = self._makeOne()
        self._failure(parser, "-foo")

    def test120(self):
        parser = self._makeOne()
        self._failure(parser, "-foo -bar")

    def test121(self):
        parser = self._makeOne()
        self._failure(parser, "foo OR -bar")

    def test122(self):
        parser = self._makeOne()
        self._failure(parser, "foo AND -bar")


class StopWordTestQueryParser(TestQueryParserBase):

    def _makePipeline(self):
        from ..lexicon import Splitter
        return (Splitter(), FakeStopWordRemover())

    def test201(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'and/', AtomNode("and"))

    def test202(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'foo AND stop', AtomNode("foo"), ["stop"])

    def test203(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'foo AND NOT stop', AtomNode("foo"), ["stop"])

    def test204(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'stop AND foo', AtomNode("foo"), ["stop"])

    def test205(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'foo OR stop', AtomNode("foo"), ["stop"])

    def test206(self):
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'stop OR foo', AtomNode("foo"), ["stop"])

    def test207(self):
        from ..parsetree import AndNode
        from ..parsetree import AtomNode
        parser = self._makeOne()
        self._expect(parser, 'foo AND bar NOT stop',
                     AndNode([AtomNode("foo"), AtomNode("bar")]), ["stop"])

    def test301(self):
        parser = self._makeOne()
        self._failure(parser, 'stop')

    def test302(self):
        parser = self._makeOne()
        self._failure(parser, 'stop stop')

    def test303(self):
        parser = self._makeOne()
        self._failure(parser, 'stop AND stop')

    def test304(self):
        parser = self._makeOne()
        self._failure(parser, 'stop OR stop')

    def test305(self):
        parser = self._makeOne()
        self._failure(parser, 'stop -foo')

    def test306(self):
        parser = self._makeOne()
        self._failure(parser, 'stop AND NOT foo')


class FakeStopWordRemover(object):

    def process(self, list):
        return [word for word in list if word != "stop"]


