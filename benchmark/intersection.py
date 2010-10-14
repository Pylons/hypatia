"""
Thinking about apply_intersection()

Given two indices: i1, i2
Number of docs in each index: nd1, nd2
Number of unique keys in each index: nk1, nk2
Average size of result set: nd1/nk1, nd2/nk2

Lookup on i1 has been performed, yielding result set r1 with actual size n1.
r2 is not yet computed, average n2 is nd2/nk2.

Two algorithms:

1) Perform lookup on i2, yielding r2, then take intersection of r1 and r2.

Lookup is O(log(nk2))
Intersection is O(max(n1, n2))
Total cost: O(log(nk2) + max(n1, n2))
or taking the average for n2, since not yet known,
Total cost: O(log(nk2) + max(n1, nd2/nk2))

2) Iterate over items in r1, use rev_index of i2 to check for each value in i2.

Rev lookup in i2 is O(log(nd2))
Performed n1 times
Total cost: O(n1 * log(nd2))

2) beats 1) when:

  n1 * log(nd2) < log(nk2) + max(n1, nd2/nk2)

n1   | nd2   | nk2   | n1 log(nd2) | log(nk2) + max(n1, nd2/nk2) | Who wins?
----------------------------------------------------------------------------
10   | 2^20  | 2^18  | 200         | 22                          | 1
10   | 2^20  | 2^10  | 200         | 1034                        | 2

So given a relationship between number of keys and number of docs in i2 and
size of r1, we can decide which algorithm is better.

We can also look at order of evaluation of r1 vs r2. Given there is some
advantage to algorithm 2 if n1 is small, we can compute nd/nk for each index
and choose to evaluate the index with the smaller value first, since on
average it will have a smaller result set.

That's the theory anyway.  Let's see who wins.
"""
import glob
import os
import time

from repoze.catalog.catalog import ConnectionManager
from repoze.catalog.catalog import FileStorageCatalogFactory
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.query import Eq
from repoze.catalog.query import SetOp

_marker = object()

class Intersection1(SetOp):
    def apply(self, catalog):
        left = self.left.apply(catalog)
        if len(left) == 0:
            results = self.family.IF.Set()
        else:
            right = self.right.apply(catalog)
            if len(right) == 0:
                results = self.family.IF.Set()
            else:
                _, results = self.family.IF.weightedIntersection(left, right)
        return results

class Intersection2(SetOp):
    """
    Implements algorithm2 above.  In real life we wouldn't do this in the
    Intersection operator--we'd do it in the apply_intersection() of the index
    and wire the Intersection operator to use that.
    """
    def apply(self, catalog):
        left = self.left.apply(catalog)
        rev_index = catalog[self.right.index_name]._rev_index
        value = self.right.value
        results = self.family.IF.Set()
        for docid in left:
            if rev_index.get(docid, _marker) == value:
                results.add(docid)
        return results

def do_benchmark(fname, nd, nk1, nk2):
    cumulative1 = 0.0
    cumulative2 = 0.0

    print "Index 1:"
    print "\t# docs: %d" % nd
    print "\t# distinct keys: %d" % nk1
    print "Index 2:"
    print "\t# docs: %d" % nd
    print "\t# distinct keys: %d" % nk2
    print ""
    print "Setting up indexes..."

    for fn in glob.glob(fname + "*"):
        os.remove(fn)

    manager = ConnectionManager()
    factory = FileStorageCatalogFactory(fname, 'intersection')
    catalog = factory(manager)

    catalog['one'] = CatalogFieldIndex('one')
    catalog['two'] = CatalogFieldIndex('two')

    class Document(object):
        def __init__(self, i):
            self.one = str(i % nk1)
            self.two = str(i % nk2)

    for docid in xrange(nd):
        catalog.index_doc(docid, Document(docid))
    manager.commit()
    manager.close()

    print "Running %d queries for each algorithm..." % (nk1 * nk2)
    catalog = factory(manager)
    for key1 in xrange(nk1):
        for key2 in xrange(nk2):
            query1 = Intersection1(Eq('one', str(key1)), Eq('two', str(key2)))
            query2 = Intersection2(Eq('one', str(key1)), Eq('two', str(key2)))

            start = time.time()
            query1.apply(catalog)
            cumulative1 += time.time() - start

            start = time.time()
            query2.apply(catalog)
            cumulative2 += time.time() - start

    manager.close()

    print "Time for algorithm1: %0.3f s" % cumulative1
    print "Time for algorithm2: %0.3f s" % cumulative2

if __name__ == '__main__':
    do_benchmark('benchmark.db', 10000, 1000, 1000)
