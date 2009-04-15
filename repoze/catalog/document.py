import random

from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.OOBTree import OOBTree

import BTrees

_marker = ()

class DocumentMap(Persistent):
    """ A document map maps addresses (e.g. location paths) to
    document ids.  It is a persistent object meant to live in a ZODB
    storage."""
    _v_nextid = None
    family = BTrees.family32
    _randrange = random.randrange
    docid_to_metadata = None # latch for b/c

    def __init__(self):
        self.docid_to_address = IOBTree()
        self.address_to_docid = OIBTree()
        self.docid_to_metadata = IOBTree()

    def add(self, address, docid=_marker):
        """ Add a new document to the document map.  ``address`` is a
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

    def _check_metadata(self):
        # backwards compatibility
        if self.docid_to_metadata is None:
            self.docid_to_metadata = IOBTree()

    def add_metadata(self, docid, data):
        """
        Add metadata related to docid.  If ``docid`` doesn't
        relate to an address in in the document map, a KeyError will
        be raised.

        For each key/value pair in ``data`` (which should be a
        mapping, such as a dictionary), insert a metadata key/value
        pair into the metadata BTree.

        When metadata values are added, any existing values related to
        the keys are overwritten, but existing values that don't
        relate to the keys are left unchanged.
        """
        if not docid in self.docid_to_address:
            raise KeyError(docid)
        self._check_metadata()
        meta = self.docid_to_metadata.setdefault(docid, OOBTree())
        for k in data:
            meta[k] = data[k]
        if not meta:
            del self.docid_to_metadata[docid]

    def remove_metadata(self, docid, *keys):
        """ Remove metadata related to docid.  If the docid doesn't
        exist in the metadata map, a KeyError will be raised.

        For each key in ``keys``, remove the metadata value for the
        docid related to that key.  If any entry related to a key does
        not exist, no error will be raised.

        If no keys are specified, all metadata related to the docid is
        removed.
        """
        self._check_metadata()
        if keys:
            meta = self.docid_to_metadata.get(docid, None)
            if meta is None:
                raise KeyError(docid)
            for k in keys:
                if k in meta:
                    del meta[k]
            if not meta:
                del self.docid_to_metadata[docid]
        else:
            if not (docid in self.docid_to_metadata):
                raise KeyError(docid)
            del self.docid_to_metadata[docid]

    def get_metadata(self, docid):
        """
        Return the metadata BTree related to ``docid``.

        If metadata does not exist for ``docid``, a KeyError is raised.
        """
        if self.docid_to_metadata is None:
            raise KeyError(docid)
        meta = self.docid_to_metadata[docid]
        return meta

    def remove_docid(self, docid):
        """ Remove a document from the document map using an integer
        document id.  If the document id doesn't actually exist in the
        document map, return False.  Otherwise, return True."""
        self._check_metadata()
        address = self.docid_to_address.get(docid)
        if address is None:
            return False
        del self.docid_to_address[docid]
        del self.address_to_docid[address]
        if docid in self.docid_to_metadata:
            del self.docid_to_metadata[docid]
        return True

    def remove_address(self, address):
        """ Remove a document from the document map using an address.
        If the address doesn't actually exist in the document map,
        return False.  Otherwise, return True."""
        self._check_metadata()
        docid = self.address_to_docid.get(address)
        if docid is None:
            return False
        del self.docid_to_address[docid]
        del self.address_to_docid[address]
        if docid in self.docid_to_metadata:
            del self.docid_to_metadata[docid]
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


