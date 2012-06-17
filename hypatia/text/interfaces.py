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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Text-indexing interfaces
"""
from zope.interface import Attribute
from zope.interface import Interface

class ILexicon(Interface):
    """Object responsible for converting text to word identifiers."""

    def termToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parse the text as if they are search terms, and skips words
        that aren't in the lexicon.
        """

    def sourceToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parse the text as if they come from a source document, and
        creates new word ids for words that aren't (yet) in the
        lexicon.
        """

    def globToWordIds(pattern):
        """Return a sequence of ids of words matching the pattern.

        The argument should be a single word using globbing syntax,
        e.g. 'foo*' meaning anything starting with 'foo'.

        Return the wids for all words in the lexicon that match the
        pattern.
        """

    def wordCount():
        """Return the number of unique terms in the lexicon."""

    def get_word(wid):
        """Return the word for the given word id.

        Raise KeyError if the word id is not in the lexicon.
        """

    def get_wid(word):
        """Return the wird id for the given word.

        Return 0 of the word is not in the lexicon.
        """

    def parseTerms(text):
        """Pass the text through the pipeline.

        Return a list of words, normalized by the pipeline
        (e.g. stopwords removed, case normalized etc.).
        """

    def isGlob(word):
        """Return true if the word is a globbing pattern.

        The word should be one of the words returned by parseTerms().
        """

class ILexiconBasedIndex(Interface):
    """ Interface for indexes which hold a lexicon."""
    lexicon = Attribute(u'Lexicon used by the index.')

class IQueryParser(Interface):
    """Interface for Query Parsers."""

    def parseQuery(query):
        """Parse a query string.

        Return a parse tree (which implements IQueryParseTree).

        Some of the query terms may be ignored because they are
        stopwords; use getIgnored() to find out which terms were
        ignored.  But if the entire query consists only of stop words,
        or of stopwords and one or more negated terms, an exception is
        raised.

        May raise ParseTree.ParseError.
        """

    def getIgnored():
        """Return the list of ignored terms.

        Return the list of terms that were ignored by the most recent
        call to parseQuery() because they were stopwords.

        If parseQuery() was never called this returns None.
        """

    def parseQueryEx(query):
        """Parse a query string.

        Return a tuple (tree, ignored) where 'tree' is the parse tree
        as returned by parseQuery(), and 'ignored' is a list of
        ignored terms as returned by getIgnored().

        May raise ParseTree.ParseError.
        """

class IQueryParseTree(Interface):
    """Interface for parse trees returned by parseQuery()."""

    def nodeType():
        """Return the node type.

        This is one of 'AND', 'OR', 'NOT', 'ATOM', 'PHRASE' or 'GLOB'.
        """

    def getValue():
        """Return a node-type specific value.

        For node type:    Return:
        'AND'             a list of parse trees
        'OR'              a list of parse trees
        'NOT'             a parse tree
        'ATOM'            a string (representing a single search term)
        'PHRASE'          a string (representing a search phrase)
        'GLOB'            a string (representing a pattern, e.g. "foo*")
        """

    def terms():
        """Return a list of all terms in this node, excluding NOT subtrees."""

    def executeQuery(index):
        """Execute the query represented by this node against the index.

        The index argument must implement the IIndex interface.

        Return an IFBucket or IFBTree mapping document ids to scores
        (higher scores mean better results).

        May raise ParseTree.QueryError.
        """

class ISearchableText(Interface):
    """Interface that text-indexable objects should implement."""

    def getSearchableText():
        """Return a sequence of unicode strings to be indexed.

        Each unicode string in the returned sequence will be run
        through the splitter pipeline; the combined stream of words
        coming out of the pipeline will be indexed.

        returning None indicates the object should not be indexed
        """

class IPipelineElement(Interface):
    """ An element in a lexicon's processing pipeline.
    """
    def process(terms):
        """ Transform each term in terms.

        Return the sequence of transformed terms.
        """

class ISplitter(IPipelineElement):
    """ Split text into a sequence of words.
    """
    def processGlob(terms):
        """ Transform terms, leaving globbing markers in place.
        """


class IExtendedQuerying(Interface):
    """An index that supports advanced search setups."""

    def search(term):
        """Execute a search on a single term given as a string.

        Return an IFBTree mapping docid to score, or None if all docs
        match due to the lexicon returning no wids for the term (e.g.,
        if the term is entirely composed of stopwords).
        """

    def search_phrase(phrase):
        """Execute a search on a phrase given as a string.

        Return an IFBtree mapping docid to score.
        """

    def search_glob(pattern):
        """Execute a pattern search.

        The pattern represents a set of words by using * and ?.  For
        example, "foo*" represents the set of all words in the lexicon
        starting with "foo".

        Return an IFBTree mapping docid to score.
        """

    def query_weight(terms):
        """Return the weight for a set of query terms.

        'terms' is a sequence of all terms included in the query,
        although not terms with a not.  If a term appears more than
        once in a query, it should appear more than once in terms.

        Nothing is defined about what "weight" means, beyond that the
        result is an upper bound on document scores returned for the
        query.
        """
