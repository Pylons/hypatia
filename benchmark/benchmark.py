# 4933 sec to catalog 511421 documents with 3 field indexes, a facet index
# and a text index.

import os
import datetime

BENCHMARK_DATA_DIR='benchmark_data'
MAILLIST_INDEX='http://mail.python.org/pipermail/python-list/'

from hypatia.catalog import FileStorageCatalogFactory
from hypatia.catalog import ConnectionManager
from hypatia.indexes.field import CatalogFieldIndex
from hypatia.indexes.facet import CatalogFacetIndex
from hypatia.indexes.text import CatalogTextIndex
        
from email.Parser import Parser
from rfc822 import parsedate_tz
import gzip,time
from urllib2 import urlopen
from HTMLParser import HTMLParser
from urlparse import urljoin

class Profiler(object):
    """This is a 'profiler' of sorts intended to let us find out how
       long particular actions, of programmer interest, take to run,
       total.  Actions can be arbitrarily nested.  This doesn't do
       anything like the actual python profiler, which tells how much
       time you end up spending in particular function calls
       aggregated across all calls to particular functions.  Both
       kinds of data are useful and recommended for getting a handle
       on where performance bottlenecks might be.
    """
    def __init__(self):
        self.action_root = TimedAction('Total')
        self.action_stack = [ self.action_root, ]
        
    def start(self, name):
        action = TimedAction(name)
        self.action_stack[-1].children.append(action)
        self.action_stack.append(action)
        print name
        
    def stop(self, name=None):
        if name is None:
            self.action_root.stop()
            return
        
        action = self.action_stack.pop()
        if action.name != name:
            raise Exception( "Profiler action stopped out of sequence.  "
                             "Expecting: %s" % action.name )
        action.stop()
        
    def print_stack(self):
        self.action_root.print_action()
        
class TimedAction(object):
    def __init__(self, name):
        self.name = name
        self.start_time = time.time()
        self.end_time = None
        self.children = []
        
    def stop(self):
        self.end_time = time.time()
        
    def print_action(self,level=0):
        indent = "  ".join( [ "" for i in xrange(level+1) ] ) # Hacky, sorry
        if self.end_time:
            print "%s%s: %0.3f" % ( indent, self.name,
                                    self.end_time - self.start_time )
        else:
            print "%s%s:" % ( indent, self.name )

        for child in self.children:
            child.print_action( level + 1 )
            
# Start profiling
profiler = Profiler()

def prep_catalog():
    """Download python mailing list, create new catalog and catalog 
       messages, if not done already.
    """
    if not os.path.exists(BENCHMARK_DATA_DIR):
        os.makedirs(BENCHMARK_DATA_DIR)
        
    # Check to see if mailing list data already present
    if len(get_mailbox_filenames()) == 0:
        MailListSucker(MAILLIST_INDEX,BENCHMARK_DATA_DIR).suck()
        
    # Create ZODB and index maillist messages, if not yet done
    zodb_file = os.path.join(BENCHMARK_DATA_DIR, 'test.zodb')
    if not os.path.exists(zodb_file):
        # Create a catalog
        manager = ConnectionManager()
        factory = FileStorageCatalogFactory(
            os.path.join(BENCHMARK_DATA_DIR,
                         'test.zodb'), 'benchmark' )
        c = factory(manager)
        
        # Create some indices
        c['subject'] = CatalogFieldIndex(get_subject)
        c['date'] = CatalogFieldIndex(get_date)
        c['sender_email'] = CatalogFieldIndex(get_sender_email)
        c['topics'] = CatalogFacetIndex(get_topics, topic_taxonomy)
        c['text'] = CatalogTextIndex(get_text)
        manager.commit()
                
        # Loop over messages to get base line
        profiler.start( "Loop over messages without indexing" )
        for _ in MessageIterator():
            pass
        profiler.stop( "Loop over messages without indexing" )
        
        profiler.start( "Index messages" )
        id = 1
        for msg in MessageIterator():
            c.index_doc(id,msg)
            id += 1
            if id / 100 == 0:
                manager.commit()
        manager.commit()
        manager.close()
        
        profiler.stop( "Index messages" )
        print "Indexed %d messages" % id
    
def get_mailbox_filenames():
    return [ dir for dir in
             os.listdir(BENCHMARK_DATA_DIR) if dir[-7:] == '.txt.gz' ]

# Adapter methods for indexing messages
def get_subject(msg,default):
    subject = msg.get('Subject',default)
    return subject

def get_date(msg,default):
    date = msg.get('Date',default)
    return date

def get_sender_email(msg,default):
    sender_email = msg.get('From', default)
    return sender_email

topic_taxonomy = set(['year'])
for year in (2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009):
    topic_taxonomy.add('year:%s' % year)
    for num in range(1, 13):
        monthname = datetime.date(year, num, 1).strftime('%B')
        topic_taxonomy.add('year:%s:%s' % (year, monthname))

def get_topics(msg, default):
    date = msg.get('Date', default)
    if date is default:
        return default
    try:
        tt = parsedate_tz(date)
    except:
        return default
    if not tt:
        return default
    year, mon, _, _, _, _, _, _, _, _ = tt
    try:
        year = int(year)
    except:
        return default
    if year < 1900:
        year = year + 1900
    monthname = datetime.date(year, mon, 1).strftime('%B')
    return ['year:%s:%s' % (year, monthname)]

def get_text(msg, default):
    return msg.as_string()

class MailListSucker(HTMLParser):
    BUFFER_SIZE = 64 * 1024
    
    def __init__(self,url,out_dir):
        HTMLParser.__init__(self)
        self.url = url
        self.out_dir = out_dir
        
    def suck(self):
        self.feed(urlopen(self.url).read())
        self.close()
        
    def blow(self):
        raise NotImplemented
    
    def handle_starttag(self,name,attrs):
        if name == 'a':
            for name, href in attrs:
                if name == 'href' and href and href[-7:] == '.txt.gz':
                    # Download file
                    href = urljoin( self.url, href )
                    print "Downloading %s..." % href
                    fname = href[href.rindex('/')+1:]
                    down = urlopen(href)
                    out = open( os.path.join( BENCHMARK_DATA_DIR,
                                              fname ), "wb" )
                    buf = down.read(self.BUFFER_SIZE)
                    while len(buf):
                        out.write(buf)
                        buf = down.read(self.BUFFER_SIZE)
                    out.close()
                    down.close()

class MessageIterator(object):
    """Iterates over a messages in a series of gzipped mailboxes in the 
       benchmark data directory.  Conveniently aggregates all messages
       in all mailboxes into a single iterable.
    """
    email_parser = Parser()
    def __init__(self):
        self.file_list = get_mailbox_filenames()
        self._next_file()
        
    def _next_file(self):
        if self.file_list:
            fname = self.file_list.pop(0)
            
            # Read whole thing into memory and manipulate it.
            # Not the most efficient but good enough for testing
            print "load %s" % fname
            self.messages = gzip.open(
                os.path.join(BENCHMARK_DATA_DIR,fname)).read().split('\nFrom ')
        
        else:    
            raise StopIteration
    
    def next(self):
        if not self.messages:
            self._next_file()
        message = self.messages.pop(0)
        return self.email_parser.parsestr( message[message.index('\n')+1:] )
        
    def __iter__(self):
        return self

def run():
    # Download mailbox archive of python mailing list and build
    # catalog if needed
    prep_catalog()

    # Open a catalog
    manager = ConnectionManager()
    factory = FileStorageCatalogFactory(
        os.path.join(BENCHMARK_DATA_DIR,'test.zodb'), 'benchmark' )
    c = factory(manager)

    # Do some searches

    profiler.start( "unsorted retrieval" )
    n, results = c.search(date=('0', 'Z'))
    print '%d results ' % n
    # Force generator to marshall brains
    for result in results:
        pass
    profiler.stop( "unsorted retrieval" )

    profiler.start( "repeat unsorted retrieval" )
    n, results = c.search(date=('0', 'Z'))
    print '%d results ' % n
    # Force generator to marshall brains
    for result in results:
        pass
    profiler.stop( "repeat unsorted retrieval" )

    profiler.start( "sorted retrieval" )
    n, results = c.search( date=('0', 'Z'), sort_index='subject' )
    print '%d results ' % n
    for result in results:
        pass
    profiler.stop( "sorted retrieval" )

    profiler.start( "reverse sorted retrieval" )
    n, results = c.search( date=('0', 'Z'), sort_index='subject', reverse=True )
    print '%d results ' % n
    for result in results:
        pass
    profiler.stop( "reverse sorted retrieval" )

    profiler.start('limit to topic=year:2000')
    n, results = c.search( topics=['year:2000'] )
    print '%d results' % n
    L = []
    for result in results:
        L.append(result)
    profiler.stop( "limit to topic=year:2000" )

    profiler.start('count limited to topic=year:2000')
    print c['topics'].counts(L, ['year:2000'])
    profiler.stop('count limited to topic=year:2000')

    profiler.stop()
    profiler.print_stack()

