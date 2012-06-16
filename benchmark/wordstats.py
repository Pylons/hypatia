#! /usr/bin/env python
##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Dump statistics about each word in the index.

usage: wordstats.py data.fs [index key]
"""

from ZODB.Storage.FileStorage import FileStorage

def main(fspath, key):
    fs = FileStorage(fspath, read_only=1)
    db = ZODB.DB(fs)
    rt = db.open().root()
    index = rt[key]

    lex = index.lexicon
    idx = index.index
    print "Words", lex.length()
    print "Documents", idx.length()

    print "Word frequencies: count, word, wid"
    for word, wid in lex.items():
        docs = idx._wordinfo[wid]
        print len(docs), word, wid

    print "Per-doc scores: wid, (doc, score,)+"
    for wid in lex.wids():
        print wid,
        docs = idx._wordinfo[wid]
        for docid, score in docs.items():
            print docid, score,
        print

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    index_key = "index"
    if len(args) == 1:
        fspath = args[0]
    elif len(args) == 2:
        fspath, index_key = args
    else:
        print "Expected 1 or 2 args, got", len(args)
    main(fspath, index_key)
