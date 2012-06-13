import cPickle
import math
import os
import random
import sys
import time

from pychart import theme
from pychart import canvas
from pychart import axis
from pychart import area
from pychart import line_plot
from pychart import legend
from pychart import text_box

from BTrees.IFBTree import IFSet
from hypatia.indexes.field import fwscan_wins
from hypatia.indexes.field import nbest_ascending_wins

theme.get_options()
theme.use_color = True
theme.scale_factor = 2

# db keys:
# 64
# 512
# 1024
# 2048
# 4096
# 8192
# 16384
# 32768
# 65536

class FieldIndexForwardSort:
    """ Benchmark and compare the field index forward sort algorithms """

    def __init__(self, limitbase=2, rlenbase=2, dbfn='sort.db', dbkey='65536'):
        self.limitbase = limitbase
        self.rlenbase = rlenbase
        self.dbfn = dbfn
        self.dbkey = dbkey
        self.index = self.get_index()
        self.numdocs = self.index._num_docs.value
        self.dbkey = dbkey
        # the set of rlens and limits are series generated via
        # exponents to the power of the base base, e.g.  [4, 16, 64,
        # 256, 1024, 4096, 16384, 65535 ] if numdocs = 65708 and the
        # base is 4
        self.rlens = series(self.numdocs+1, self.rlenbase)
        self.limits = series(self.numdocs+1, self.limitbase)

        self.sorts = (
            ('nbest', self.index.nbest_ascending),
            ('fwscan', self.index.scan_forward),
            ('timsort', self.index.timsort_ascending)
            )
 
    def get_index(self):
        if not os.path.exists(self.dbfn):
            raise NotImplementedError # XXX create index-creation code
        from ZODB.FileStorage.FileStorage import FileStorage
        from ZODB.DB import DB
        s = FileStorage(self.dbfn)
        db = DB(s, cache_size=300000)
        c = db.open()
        root = c.root()
        return root[self.dbkey]

    def __call__(self):
        if not os.path.exists('%s.pck' % self.dbkey):
            self.bench()
        self.chart()

    def bench(self):
        tf = open('%s.txt' % self.dbkey, 'w')

        def output(msg):
            tf.write(msg + '\n')
            tf.flush()
            print msg

        all_docids = list(self.index._rev_index.keys())
        random.shuffle(all_docids)

        main = []

        for rlen in self.rlens:
            docids = IFSet(random.sample(all_docids,
                                         min(rlen, len(all_docids))))
            output('for %s' % rlen)
            output('-----------------------------------')

            control = []
            for k, s in self.index._fwd_index.items():
                for docid in s:
                    if docid in docids:
                        control.append(docid)

            capture = {}
            result = None
            for name, fn in self.sorts:
                data = capture.setdefault(name, [])
                for limit in self.limits:
                    t, result = timer(fn, docids, limit)
                    result = list(result)
                    if control[:limit] != result:
                        raise AssertionError((control[:limit], result))
                    data.append(t)
                    output('%0.6f %s at limit %s' % (t, name, limit))

            main.append({'rlen':rlen, 'capture':capture})

        cPickle.dump(main, open('%s.pck' % self.dbkey, 'w'))

    def chart(self):

        self.main = cPickle.load(open('%s.pck' % self.dbkey))

        for chartable in self.main:
            self.detailchart(chartable)

        sortnames = [ x[0] for x in self.sorts ]

        for sortname1, sortname2 in product(sortnames, sortnames):
            if sortname1 == sortname2:
                continue
            self.comparisonchart(sortname1, sortname2)

    def detailchart(self, chartable):
        theme.reinitialize()

        min_y = 0
        max_y = 0
        capture = chartable.get('capture')
        for sortname, sortfn in self.sorts:
            data = capture[sortname]
            m = median(data)
            if m > max_y:
                max_y = m

        max_x = max(self.limits)
        min_x = min(self.limits)

        ipoints = 10.0

        x_interval = (max_x - min_x) / ipoints
        y_interval = (max_y - min_y) / ipoints

        xaxis = axis.X(label='Limit',
                       tic_interval = x_interval,
                       format='/4{}%d')
        yaxis = axis.Y(label='Seconds',
                       tic_interval = y_interval,
                       format='/4{}%0.3f')

        ar = area.T(
            x_range = (min_x, max_x),
            y_range = (min_y, max_y),
            x_axis  = xaxis,
            y_axis  = yaxis,
            legend =  legend.T(),
            )
        tb = text_box.T(loc=(140,90), text='Rlen\n%s' % chartable['rlen'])

        for sortname, sortfn in self.sorts:
            data = capture[sortname]
            linedata = [ (self.limits[x], data[x]) for x in range(len(data)) ]
            ar.add_plot(
                line_plot.T(label="%s" % sortname, data=linedata)
                )
        fd = open('detail-%s-%s.pdf' % (self.dbkey, chartable['rlen']), 'w')
        can = canvas.init(fd, 'pdf')
        ar.draw(can)
        tb.draw(can)
        can.close()

    def comparisonchart(self, sortname1, sortname2):
        linedata = []
        test_total = 0
        test_wrong = 0

        for rlendata in self.main:
            rlen = rlendata['rlen']
            capture = rlendata['capture']
            values1 = capture[sortname1]
            values2 = capture[sortname2]
            doc_ratio = rlen / float(self.numdocs)
            cutoff = None
            wins = []

            #test = sortname1 == 'fwscan' and sortname2 in ('nbest', 'timsort')
            #test_fn = fwscan_wins
            test = sortname1 == 'nbest' and sortname2 == 'timsort'
            test_fn = nbest_ascending_wins

            for x in xrange(0, min(len(values1), len(values2))):
                t1 = values1[x]
                t2 = values2[x]
                limit = self.limits[x]
                limitratio = limit / float(self.numdocs)
                won = t1 < t2
                if won:
                    wins.append(limit)

                wrongmsg = "wrong %s? rlen %s, limit %s (%0.5f > %0.5f)%s"

                if test:
                    test_total += 1
                    curvewin = test_fn(limit, rlen, self.numdocs)
                    if won and (not curvewin):
                        extra = ''
                        if (t1 /  t2) < .90: # more than 10% difference
                            extra = " * (%0.2f)" % (t1/t2)
                        print wrongmsg % ('curvelose', rlen, limit, t2, t1,
                                          extra)
                        test_wrong +=1
                    elif (not won) and curvewin:
                        extra = ''
                        if (t2 /  t1) < .90: # more than 10% difference
                            extra = " * (%0.2f)" % (t2/t1)
                        print wrongmsg % ('curvewin', rlen, limit, t1, t2,
                                          extra)
                        test_wrong +=1

            for limit in wins:
                limitratio = limit / float(self.numdocs)
                linedata.append((doc_ratio, limitratio))

        if test:
            if test_total:
                test_right = test_total - test_wrong
                test_percent = test_right / float(test_total)
                print "test percentage %0.2f: (%s wrong out of %s)" % (
                    test_percent, test_wrong, test_total)

        comparename = 'compare-%s-%s-beats-%s' % (self.dbkey,
                                                  sortname1, sortname2)

        xaxis=axis.X(label='Doc Ratio (rlen//numdocs)',
                     tic_interval=.1,
                     format='/4{}%0.2f')
        yaxis=axis.Y(label='Limit Ratio (limit//numdocs)',
                     tic_interval=.1,
                     format='/4{}%0.2f')

        ar = area.T(
            x_range = (0, 1),
            y_range = (0, 1),
            x_axis  = xaxis,
            y_axis  = yaxis,
            legend =  legend.T(),
            )

        ar.add_plot(
            line_plot.T(label="%s \nbeats \n%s" % (sortname1, sortname2),
                        data=linedata),
            )

        tb = text_box.T(loc=(140,90), text='Numdocs\n%s' % self.numdocs)

        fd = open('%s.pdf' % comparename, 'w')
        can = canvas.init(fd, 'pdf')
        ar.draw(can)
        tb.draw(can)
        can.close()

def timer(fn, *args, **kw):
    times = []
    for x in xrange(7):
        start = time.time()
        result = fn(*args, **kw)
        if not hasattr(result, '__len__'):
            result = list(result)
        end = time.time()
        times.append(end-start)
    return median(times), result

def isect(seq1, seq2):
    res = []                     # start empty
    for x in seq1:               # scan seq1
        if x in seq2:            # common item?
            res.append(x)        # add to end
    return res

def product(*args):
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = map(tuple, args)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

def avg(numbers):
    return sum(numbers) / len(numbers)

def median(numbers):
    "Return the median of the list of numbers."
    # Sort the list and take the middle element.
    n = len(numbers)
    copy = numbers[:] # So that "numbers" keeps its original order
    copy.sort()
    if n & 1:         # There is an odd number of elements
        return copy[n // 2]
    else:
        return (copy[n // 2 - 1] + copy[n // 2]) / 2
  
def series(numdocs, base):
    exp = int(math.ceil(math.log(numdocs) / math.log(base)))
    return [ pow(base, x) for x in range(1, exp) ]

def main(argv=sys.argv):
    bench = FieldIndexForwardSort()
    bench()

