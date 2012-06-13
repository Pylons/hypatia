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

Fudge factor is introduced to account for fact that forward lookup is done with
string keys whereas reverse lookup and intersection are performed with integer
keys which have less expensive comparisons.

Lookup is O(fudge * log(nk2, oob))
Intersection is O(max(n1, n2))
Total cost: O(log(nk2, oob) + max(n1, n2))
or taking the average for n2, since not yet known,
Total cost: O(log(nk2, oob) + max(n1, nd2/nk2))

2) Iterate over items in r1, use rev_index of i2 to check for each value in i2.

Rev lookup in i2 is O(log(nd2, iob))
Performed n1 times
Total cost: O(n1 * log(nd2, iob))

2) beats 1) when:

  n1 * log(nd2, iob) < fudge * log(nk2, oob) + max(n1, nd2/nk2)

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
import sys
import time

from hypatia.catalog import ConnectionManager
from hypatia.catalog import FileStorageCatalogFactory
from hypatia.indexes.field import CatalogFieldIndex
from hypatia.query import Eq
from hypatia.query import BoolOp

_marker = object()
random.seed()

class Intersection1(BoolOp):
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

class Intersection2(BoolOp):
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


def predictions(nd, nk1, nk2):
    FUDGE = 17.0
##    oob = 250 # OOBTree DEFAULT_MAX_BTREE_SIZE
##    iob = 500 # IOBTree DEFAULT_MAX_BTREE_SIZE
    oob = 125 # OOBTree wag avg bucket size
    iob = 250 # IOBTree wag avg bucket size
    L_FWD_LOOKUP_COST = FUDGE * math.log(nk1, oob)
    R_FWD_LOOKUP_COST = FUDGE * math.log(nk2, oob)
    L_REV_LOOKUP_COST = math.log(nd, iob)
    AVG_L_RESULT_SIZE = float(nd)/nk1
    AVG_R_RESULT_SIZE = float(nd)/nk2
    MAX_INTERSECT_COST = max(AVG_L_RESULT_SIZE, AVG_R_RESULT_SIZE)
    AVG_INTERSECT_COST = MAX_INTERSECT_COST / 2.0 #max(nk1/2, nk2/2) / 2

    # Total cost: O(log(nk2, oob) + max(n1, nd2/nk2))
    cost1 = L_FWD_LOOKUP_COST + R_FWD_LOOKUP_COST + AVG_INTERSECT_COST
    # Total cost: O(n1 * log(nd2, iob))
    cost2 = L_FWD_LOOKUP_COST + (AVG_L_RESULT_SIZE * L_REV_LOOKUP_COST)

    return cost1, cost2

##def predictions(nd, nk1, nk2):
##    s1 = nd / nk1
##    s2 = nd / nk2
##    if s1 <= s2 / 2:
##        return 2.0, 1.0
##    return 1.0, 2.0

def do_benchmark(fname, nd, nk1, nk2, out=sys.stdout):
    cumulative1 = 0.0
    cumulative2 = 0.0

    print >>out, "Index 1:"
    print >>out, "\t# docs: %d" % nd
    print >>out, "\t# distinct keys: %d" % nk1
    print >>out, "Index 2:"
    print >>out, "\t# docs: %d" % nd
    print >>out, "\t# distinct keys: %d" % nk2
    print >>out, ""

    cost1, cost2 = predictions(nd, nk1, nk2)

    print >>out, 'Cost1: %0.2f' % cost1
    print >>out, 'Cost2: %0.2f' % cost2
    print >>out
    print >>out, "Prediction:"
    if cost1 > cost2:
        print >>out, "Algorithm 2 %0.2f times faster than Algorithm 1" % (
            cost1/cost2)
    else:
        print >>out, "Algorithm 1 %0.2f times faster than Algorithm 2" % (
            cost2/cost1)

    print >>out, ""
    print >>out, "Setting up indexes..."
    for fn in glob.glob(fname + "*"):
        os.remove(fn)

    manager = ConnectionManager()
    factory = FileStorageCatalogFactory(fname, 'intersection')
    catalog = factory(manager)

    catalog['one'] = CatalogFieldIndex('one')
    catalog['two'] = CatalogFieldIndex('two')

    class Document(object):
        def __init__(self, docid):
            self.one = str(docid % nk1)
            self.two = str(docid % nk2)

    for docid in xrange(nd):
        catalog.index_doc(docid, Document(docid))
    manager.commit()
    manager.close()

    N_QUERIES = 1000
    print >>out, "Running %d queries for each algorithm..." % N_QUERIES
    catalog = factory(manager)
    for _ in xrange(1000):
        key1 = random.randrange(nk1)
        key2 = random.randrange(nk2)
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

    print >>out, ""
    print >>out, "Result:"
    print >>out, "Time for algorithm1: %0.3f s" % cumulative1
    print >>out, "Time for algorithm2: %0.3f s" % cumulative2
    if cumulative1 > cumulative2:
        print >>out, "Algorithm 2 %0.2f times faster than Algorithm 1" % (
            cumulative1/cumulative2)
    else:
        print >>out, "Algorithm 1 %0.2f times faster than Algorithm 2" % (
            cumulative2/cumulative1)
    return cost1 / cost2, cumulative1 / cumulative2

class Null(object):
    def write(self, s):
        pass

def _range_order_of_magnitude(n):
    # Iterate over (at most) 3 orders of magnitude
    n_magnitude = int(math.ceil(math.log10(n)))
    lowest_magnitude = max(0, n_magnitude - 3)
    for magnitude in xrange(lowest_magnitude, n_magnitude):
        for i in xrange(1,10):
            value = i * 10**magnitude
            if value >= n:
                break
            yield value

def do_benchmarks(fname):
    null = Null()
    print "Cost of algorithm 1 / Cost of algorithm 2"
    print "N Docs | N Keys 1 | N Keys 2 | Predicted | Actual | Correct"
    for nd in  [100, 1000, 10000, 100000, 1000000]:
        for nk1 in _range_order_of_magnitude(nd / 2):
            for nk2 in _range_order_of_magnitude(nd):
                predicted, actual = do_benchmark(fname, nd, nk1, nk2, out=null)
                correct = ((predicted >= 1 and actual >= 1) or
                           (predicted < 1 and actual < 1))
                print "%6d | %8d | %8d | %9.2f | %6.2f | %s" % (
                    nd, nk1, nk2,  predicted, actual, correct)
                sys.stdout.flush()

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

def rerun_predictions(fname):
    benchmarks = open(fname).xreadlines()
    benchmarks.next(); benchmarks.next()  # skip header lines

    print "Cost of algorithm 1 / Cost of algorithm 2"
    print "nd     | nd/nk1   | nd/nk2   | Predicted | Actual | Correct"

    gain = count = n_correct = 0
    for line in benchmarks:
        line = line.split('|')
        nd = int(line[0].strip())
        nk1 = int(line[1].strip())
        nk2 = int(line[2].strip())
        actual = float(line[4].strip())
        cost1, cost2 = predictions(nd, nk1, nk2)
        predicted = cost1 / cost2
        correct = ((predicted >= 1 and actual >= 1) or
                   (predicted < 1 and actual < 1))
        print "%6d | %8d | %8d | %9.2f | %6.2f | %s" % (
            nd, nd/nk1, nd/nk2,  predicted, actual, correct)
        count += 1
        if correct:
            n_correct += 1

        if cost1 < cost2:
            # I picked algorithm1, so no net loss or gain
            gain += 1.0
        else:
            # I picked algorith2, so note difference in performance
            gain += actual

    print "-" * 79
    print "%% correct: %0.1f" % (n_correct * 100.0 / count)
    print "%% performance gain: %0.1f" % ((gain / count - 1.0) * 100.0)

if __name__ == '__main__':
    #do_benchmark('benchmark.db', 10000, 1000, 1000)
    #do_benchmarks('/dev/shm/benchmark.db')
    rerun_predictions('benchmarks.txt')
