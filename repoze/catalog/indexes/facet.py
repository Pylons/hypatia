try:
    from hashlib import md5
except: # pragma no cover
    from md5 import new as md5

from persistent import Persistent
from zope.interface import implements

from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from repoze.catalog.interfaces import ICatalogIndex

_marker = ()

class CatalogFacetIndex(CatalogKeywordIndex):
    """Facet index.

    Query types supported:

    - Eq

    - NotEq

    - In

    - NotIn

    - Any

    - NotAny

    - All

    - NotAll
    """
    implements(ICatalogIndex)

    def __init__(self, discriminator, facets, family=None):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        if family is not None:
            self.family = family
        self.facets = self.family.OO.Set(facets)
        self._not_indexed = self.family.IF.Set()
        self.clear()

    def index_doc(self, docid, object):
        """ Pass in an integer document id and an object supporting a
        sequence of facet specifiers ala ['style:gucci:handbag'] via
        the discriminator"""

        if callable(self.discriminator):
            value = self.discriminator(object, _marker)
        else:
            value = getattr(object, self.discriminator, _marker)

        if value is _marker:
            # unindex the previous value
            self.unindex_doc(docid)
            self._not_indexed.add(docid)
            return None

        if isinstance(value, Persistent):
            raise ValueError('Catalog cannot index persistent object %s' %
                             value)

        if docid in self._not_indexed:
            self._not_indexed.remove(docid)

        old = self._rev_index.get(docid)
        if old is not None:
            self.unindex_doc(docid)

        changed = False

        for facet in value:
            L = []
            categories = facet.split(':')
            for category in categories:
                L.append(category)
                facet_candidate = ':'.join(L)
                for fac in self.facets:
                    if fac == facet_candidate:
                        changed = True
                        fwset = self._fwd_index.get(fac)
                        if fwset is None:
                            fwset = self.family.IF.Set()
                            self._fwd_index[fac] = fwset
                        fwset.insert(docid)
                        revset = self._rev_index.get(docid)
                        if revset is None:
                            revset = self.family.OO.Set()
                            self._rev_index[docid] = revset
                        revset.insert(fac)

        if changed:
            self._num_docs.change(1)

        return value

    def counts(self, docids, omit_facets=()):
        """ Given a set of docids (usually returned from query),
        provide count information for further facet narrowing.
        Optionally omit count information for facets and their
        ancestors that are in 'omit_facets' (a sequence of facets)"""

        effective_omits = self.family.OO.Set()

        for omit_facet in omit_facets:
            L = []
            categories = omit_facet.split(':')
            for category in categories:
                L.append(category)
                effective_omits.insert(':'.join(L))

        include_facets = self.family.OO.difference(self.facets,
                                                   effective_omits)

        counts = {}
        isect_cache = {}

        for docid in docids:
            available_facets = self._rev_index.get(docid)
            ck = cachekey(available_facets)
            appropriate_facets = isect_cache.get(ck)
            if appropriate_facets is None:
                appropriate_facets = self.family.OO.intersection(
                    include_facets, available_facets)
                isect_cache[ck] = appropriate_facets
            for facet in appropriate_facets:
                count = counts.get(facet, 0)
                count += 1
                counts[facet] = count

        return counts


def cachekey(set):
    h = md5()
    for item in sorted(list(set)):
        h.update(item)
    return h.hexdigest()

