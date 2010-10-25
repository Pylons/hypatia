"""
Thinking about apply_intersection()

oob = 250  (OOBTree DEFAULT_MAX_BTREE_SIZE)
iob = 500  (IOBTree DEFAULT_MAX_BTREE_SIZE)
Given two indices: i1, i2
Number of docs in each index: nd1, nd2
Number of unique keys in each index: nk1, nk2
Average size of result set: nd1/nk1, nd2/nk2

Lookup on i1 has been performed, yielding result set r1 with actual size n1.
r2 is not yet computed, average n2 is nd2/nk2.

Two algorithms:

1) Perform lookup on i2, yielding r2, then take intersection of r1 and r2.

Lookup is O(log(nk2, oob))
Intersection is O(max(n1, n2))
Total cost: O(log(nk2, oob) + max(n1, n2))
or taking the average for n2, since not yet known,
Total cost: O(log(nk2, oob) + max(n1, nd2/nk2))

2) Iterate over items in r1, use rev_index of i2 to check for each value in i2.

Rev lookup in i2 is O(log(nd2, iob))
Performed n1 times
Total cost: O(n1 * log(nd2, iob))

2) beats 1) when:

  n1 * log(nd2, iob) < log(nk2, oob) + max(n1, nd2/nk2)

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
import math
import os
import random
import time

from repoze.catalog.catalog import ConnectionManager
from repoze.catalog.catalog import FileStorageCatalogFactory
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.query import Eq
from repoze.catalog.query import SetOp

_marker = object()
random.seed()

class Intersection1(SetOp):
    """
    Total cost: O(log(nk2, oob) + max(n1, nd2/nk2))
    """
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

    Total cost: O(n1 * log(nd2, iob))
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

    oob = 250 # OOBTree DEFAULT_MAX_BTREE_SIZE
    iob = 500 # IOBTree DEFAULT_MAX_BTREE_SIZE
    L_FWD_LOOKUP_COST = math.log(nk1, oob)
    R_FWD_LOOKUP_COST = math.log(nk2, oob)
    L_REV_LOOKUP_COST = math.log(nd, iob)
    AVG_L_RESULT_SIZE = float(nd)/nk1
    AVG_R_RESULT_SIZE = float(nd)/nk2
    LR_INTERSECT_COST = max(AVG_L_RESULT_SIZE, AVG_R_RESULT_SIZE)
    MAX_INTERSECT_COST = LR_INTERSECT_COST #max(nk1/2, nk2/2)

    # Total cost: O(log(nk2, oob) + max(n1, nd2/nk2))
    cost1 = L_FWD_LOOKUP_COST + R_FWD_LOOKUP_COST + MAX_INTERSECT_COST
    # Total cost: O(n1 * log(nd2, iob))
    cost2 = L_FWD_LOOKUP_COST + (AVG_L_RESULT_SIZE * L_REV_LOOKUP_COST)

    print 'Cost1: %0.2f' % cost1
    print 'Cost2: %0.2f' % cost2
    print
    print "Prediction:"
    if cost1 > cost2:
        print "Algorithm 2 %0.2f times faster than Algorithm 1" % (cost1/cost2)
    else:
        print "Algorithm 1 %0.2f times faster than Algorithm 2" % (cost2/cost1)

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
        def __init__(self):
            self.one = str(random.randrange(nk1))
            self.two = str(random.randrange(nk2))

    for docid in xrange(nd):
        catalog.index_doc(docid, Document())
    manager.commit()
    manager.close()

    print "Running %d queries for each algorithm..." % (nk1 * nk2)
    catalog = factory(manager)
    for key1 in xrange(nk1):
        for key2 in xrange(nk2):
            query1 = Intersection1(Eq('one', str(key1)), Eq('two', str(key2)))
            query2 = Intersection2(Eq('one', str(key1)), Eq('two', str(key2)))

            start = time.time()
            result1 = query1.apply(catalog)
            cumulative1 += time.time() - start

            start = time.time()
            result2 = query2.apply(catalog)
            cumulative2 += time.time() - start

            s1 = sorted(list(result1))
            s2 = sorted(list(result2))

            assert s1==s2, (s1, s2)

    manager.close()
    for fn in glob.glob(fname + "*"):
        os.remove(fn)

    print ""
    print "Result:"
    print "Time for algorithm1: %0.3f s" % cumulative1
    print "Time for algorithm2: %0.3f s" % cumulative2
    if cumulative1 > cumulative2:
        print "Algorithm 2 %0.2f times faster than Algorithm 1" % (
            cumulative1/cumulative2)
    else:
        print "Algorithm 1 %0.2f times faster than Algorithm 2" % (
            cumulative2/cumulative1)

# profile (unused right now)
def profile(cmd, globals, locals, sort_order, callers):
    import profile
    import pstats
    import tempfile
    fd, fn = tempfile.mkstemp()
    try:
        if hasattr(profile, 'runctx'):
            profile.runctx(cmd, globals, locals, fn)
        else:
            raise NotImplementedError('No profiling support under Python 2.3')
        stats = pstats.Stats(fn)
        stats.strip_dirs()
        # calls,time,cumulative and cumulative,calls,time are useful
        stats.sort_stats(*sort_order or ('cumulative', 'calls', 'time'))
        if callers:
            stats.print_callers(.3)
        else:
            stats.print_stats(.3)
    finally:
        os.remove(fn)

if __name__ == '__main__':
    do_benchmark('benchmark.db', 10000, 1000, 1000)
