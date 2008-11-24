import random

from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree

import BTrees

_marker = ()

class DocumentMap(Persistent):
    """ A document map maps addresses (e.g. location paths) to
    document ids.  It is a persistent object meant to live in a ZODB
    storage."""
    _v_nextid = None
    family = BTrees.family32
    _randrange = random.randrange

    def __init__(self):
        self.docid_to_address = IOBTree()
        self.address_to_docid = OIBTree()

    def add(self, address, docid=_marker):
        """ Add a new document to the docment map.  ``address`` is a
        string or other hashable object which represents a token known
        by the application.  This method returns an integer document
        id.  An optional ``docid`` argument allows you to add a a
        document with an already-known document id.  If it is not
        passed, a docid is generated and used."""
        if docid is _marker:
            docid = self.new_docid()
        self.docid_to_address[docid] = address
        self.address_to_docid[address] = docid
        return docid

    def remove_docid(self, docid):
        """ Remove a document from the document map using an integer
        document id.  If the document id doesn't actually exist in the
        document map, return False.  Otherwise, return True."""
        address = self.docid_to_address.get(docid)
        if address is None:
            return False
        del self.docid_to_address[docid]
        del self.address_to_docid[address]
        return True

    def remove_address(self, address):
        """ Remove a document from the document map using an address.
        If the address doesn't actually exist in the document map,
        return False.  Otherwise, return True."""
        docid = self.address_to_docid.get(address)
        if docid is None:
            return False
        del self.docid_to_address[docid]
        del self.address_to_docid[address]
        return True

    def docid_for_address(self, address):
        """ Retrieve an integer document id given an address.  If the
        address doesn't actually exist in the document map, return
        None."""
        return self.address_to_docid.get(address)

    def address_for_docid(self, docid):
        """ Retrieve an address given an integer document id.  If the
        document id doesn't actually exist in the document map, return
        None."""
        return self.docid_to_address.get(docid)

    def new_docid(self):
        """Return a document id which is not yet taken in this
        document map.
        """
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(self.family.minint,
                                                 self.family.maxint)
            uid = self._v_nextid
            self._v_nextid += 1
            if uid not in self.docid_to_address:
                return uid
            self._v_nextid = None


