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
"""Query Parser.

This particular parser recognizes the following syntax:

Start = OrExpr
OrExpr = AndExpr ('OR' AndExpr)*
AndExpr = Term ('AND' NotExpr | 'NOT' AndExpr)*
NotExpr = ['NOT'] Term
Term = '(' OrExpr ')' | ATOM+

The key words (AND, OR, NOT) are recognized in any mixture of case.

An ATOM is either:

+ A sequence of characters not containing whitespace or parentheses or
  double quotes, and not equal (ignoring case) to one of the key words
  'AND', 'OR', 'NOT'; or

+ A non-empty string enclosed in double quotes.  The interior of the
  string can contain whitespace, parentheses and key words, but not
  quotes.

+ A hyphen followed by one of the two forms above, meaning that it
  must not be present.

An unquoted ATOM may also contain globbing characters.  Globbing
syntax is defined by the lexicon; for example "foo*" could mean any
word starting with "foo".

When multiple consecutive ATOMs are found at the leaf level, they are
connected by an implied AND operator, and an unquoted leading hyphen
is interpreted as a NOT operator.

Summarizing the default operator rules:

- a sequence of words without operators implies AND, e.g. ``foo bar''
- double-quoted text implies phrase search, e.g. ``"foo bar"''
- words connected by punctuation implies phrase search, e.g. ``foo-bar''
- a leading hyphen implies NOT, e.g. ``foo -bar''
- these can be combined, e.g. ``foo -"foo bar"'' or ``foo -foo-bar''
- * and ? are used for globbing (i.e. prefix search), e.g. ``foo*''
"""

import re
import sys

from zope.interface import implementer

from .interfaces import IQueryParser
from . import parsetree

# Create unique symbols for token types.
_AND    = sys.intern("AND")
_OR     = sys.intern("OR")
_NOT    = sys.intern("NOT")
_LPAREN = sys.intern("(")
_RPAREN = sys.intern(")")
_ATOM   = sys.intern("ATOM")
_EOF    = sys.intern("EOF")

# Map keyword string to token type.
_keywords = {
    _AND:       _AND,
    _OR:        _OR,
    _NOT:       _NOT,
    _LPAREN:    _LPAREN,
    _RPAREN:    _RPAREN,
}

# Regular expression to tokenize.
_tokenizer_regex = re.compile(r"""
    # a paren
    [()]
    # or an optional hyphen
|   -?
    # followed by
    (?:
        # a string inside double quotes (and not containing these)
        " [^"]* "
        # or a non-empty stretch w/o whitespace, parens or double quotes
    |    [^()\s"]+
    )
""", re.VERBOSE)

@implementer(IQueryParser)
class QueryParser(object):

    # This class is not thread-safe;
    # each thread should have its own instance

    def __init__(self, lexicon):
        self._lexicon = lexicon
        self._ignored = None

    # Public API methods

    def parseQuery(self, query):
        # Lexical analysis.
        tokens = _tokenizer_regex.findall(query)
        self._tokens = tokens
        # classify tokens
        self._tokentypes = [_keywords.get(token.upper(), _ATOM)
                            for token in tokens]
        # add _EOF
        self._tokens.append(_EOF)
        self._tokentypes.append(_EOF)
        self._index = 0

        # Syntactical analysis.
        self._ignored = [] # Ignored words in the query, for parseQueryEx
        tree = self._parseOrExpr()
        self._require(_EOF)
        if tree is None:
            raise parsetree.ParseError(
                "Query contains only common words: %s" % repr(query))
        return tree

    def getIgnored(self):
        return self._ignored

    def parseQueryEx(self, query):
        tree = self.parseQuery(query)
        ignored = self.getIgnored()
        return tree, ignored

    # Recursive descent parser

    def _require(self, tokentype):
        if not self._check(tokentype):
            t = self._tokens[self._index]
            msg = "Token %r required, %r found" % (tokentype, t)
            raise parsetree.ParseError(msg)

    def _check(self, tokentype):
        if self._tokentypes[self._index] is tokentype:
            self._index += 1
            return 1
        else:
            return 0

    def _peek(self, tokentype):
        return self._tokentypes[self._index] is tokentype

    def _get(self, tokentype):
        t = self._tokens[self._index]
        self._require(tokentype)
        return t

    def _parseOrExpr(self):
        L = []
        L.append(self._parseAndExpr())
        while self._check(_OR):
            L.append(self._parseAndExpr())
        L = [x for x in L if x]
        if not L:
            return None # Only stopwords
        elif len(L) == 1:
            return L[0]
        else:
            return parsetree.OrNode(L)

    def _parseAndExpr(self):
        L = []
        t = self._parseTerm()
        if t is not None:
            L.append(t)
        Nots = []
        while 1:
            if self._check(_AND):
                t = self._parseNotExpr()
                if t is None:
                    continue
                if isinstance(t, parsetree.NotNode):
                    Nots.append(t)
                else:
                    L.append(t)
            elif self._check(_NOT):
                t = self._parseTerm()
                if t is None:
                    continue # Only stopwords
                Nots.append(parsetree.NotNode(t))
            else:
                break
        if not L:
            return None # Only stopwords
        L.extend(Nots)
        if len(L) == 1:
            return L[0]
        else:
            return parsetree.AndNode(L)

    def _parseNotExpr(self):
        if self._check(_NOT):
            t = self._parseTerm()
            if t is None:
                return None # Only stopwords
            return parsetree.NotNode(t)
        else:
            return self._parseTerm()

    def _parseTerm(self):
        if self._check(_LPAREN):
            tree = self._parseOrExpr()
            self._require(_RPAREN)
        else:
            nodes = []
            nodes = [self._parseAtom()]
            while self._peek(_ATOM):
                nodes.append(self._parseAtom())
            nodes = [x for x in  nodes if x]
            if not nodes:
                return None # Only stopwords
            structure = sorted(
                [(isinstance(nodes[i], parsetree.NotNode), i, nodes[i])
                         for i in range(len(nodes))])
            nodes = [node for (bit, index, node) in structure]
            if isinstance(nodes[0], parsetree.NotNode):
                raise parsetree.ParseError(
                    "a term must have at least one positive word")
            if len(nodes) == 1:
                return nodes[0]
            tree = parsetree.AndNode(nodes)
        return tree

    def _parseAtom(self):
        term = self._get(_ATOM)
        words = self._lexicon.parseTerms(term)
        if not words:
            self._ignored.append(term)
            return None
        if len(words) > 1:
            tree = parsetree.PhraseNode(words)
        elif self._lexicon.isGlob(words[0]):
            tree = parsetree.GlobNode(words[0])
        else:
            tree = parsetree.AtomNode(words[0])
        if term[0] == "-":
            tree = parsetree.NotNode(tree)
        return tree
