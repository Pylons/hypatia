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
"""Keyword-index search interface
"""
from zope.interface import Interface

class IKeywordQuerying(Interface):
    """Query over a set of keywords, seperated by white space."""

    def search(query, operator='and'):
        """Execute a search given by 'query'.
        
        'query' can be a (unicode) string or an iterable of (unicode) strings.
        'operator' can be either 'and' or 'or' to search for documents
        containing all keywords or any keyword. 

        Return an IFSet of docids
        """
