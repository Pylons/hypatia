import random

from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.OOBTree import OOBTree

import BTrees

_marker = ()

class DocumentMap(Persistent):
    """ A two-way map between addresses (e.g. location paths) and document ids.

    The map is a persistent object meant to live in a ZODB storage.

    Additionally, the map is capable of mapping 'metadata' to docids.
    """
    _v_nextid = None
    family = BTrees.family32
    _randrange = random.randrange
    docid_to_metadata = None # latch for b/c

    def __init__(self):
        self.docid_to_address = IOBTree()
        self.address_to_docid = OIBTree()
        self.docid_to_metadata = IOBTree()

    def docid_for_address(self, address):
        """ Retrieve a document id for a given address.

        ``address`` is a string or other hashable object which represents
        a token known by the application.

        Return the integer document id corresponding to ``address``.

        If ``address`` doesn't exist in the document map, return None.
        """
        return self.address_to_docid.get(address)

    def address_for_docid(self, docid):
        """ Retrieve an address for a given document id.

        ``docid`` is an integer document id.

        Return the address corresponding to ``docid``.

        If ``docid`` doesn't exist in the document map, return None.
        """
        return self.docid_to_address.get(docid)

    def add(self, address, docid=_marker):
        """ Add a new document to the document map.

        ``address`` is a string or other hashable object which represents
        a token known by the application.

        ``docid``, if passed, must be an int.  In this case, remove any
        previous address stored for it before mapping it to the new address.
        Preserve any metadata for ``docid`` in this case.
        
        If ``docid`` is not passed, generate a new docid.

        Return the integer document id mapped to ``address``.
        """
        if docid is _marker:
            docid = self.new_docid()
        else:
            old_address = self.docid_to_address.get(docid)
            if old_address is not None:
                del self.address_to_docid[old_address]
        self.docid_to_address[docid] = address
        self.address_to_docid[address] = docid
        return docid

    def remove_docid(self, docid):
        """ Remove a document from the document map for the given document ID.

        ``docid`` is an integer document id.

        Remove any corresponding metadata for ``docid`` as well.

        Return a True if ``docid`` existed in the map, else return False.
        """
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

        ``address`` is a string or other hashable object which represents
        a token known by the application.

        Remove any corresponding metadata for ``address`` as well.

        Return a True if ``address`` existed in the map, else return False.
        """
        self._check_metadata()
        docid = self.address_to_docid.get(address)
        if docid is None:
            return False
        del self.docid_to_address[docid]
        del self.address_to_docid[address]
        if docid in self.docid_to_metadata:
            del self.docid_to_metadata[docid]
        return True

    def _check_metadata(self):
        # backwards compatibility
        if self.docid_to_metadata is None:
            self.docid_to_metadata = IOBTree()

    def add_metadata(self, docid, data):
        """ Add metadata related to a given document id.

        ``data`` must be a mapping, such as a dictionary.
        
        For each key/value pair in ``data`` insert a metadata key/value pair
        into the metadata stored for ``docid``.

        Overwrite any existing values for the keys in ``data``, leaving values
        unchanged for other existing keys.

        Raise a KeyError If ``docid`` doesn't relate to an address in the
        document map,
        """
        if not docid in self.docid_to_address:
            raise KeyError(docid)
        if len(data.keys()) == 0:
            return
        self._check_metadata()
        meta = self.docid_to_metadata.setdefault(docid, OOBTree())
        for k in data:
            meta[k] = data[k]

    def remove_metadata(self, docid, *keys):
        """ Remove metadata related to a given document id.

        If ``docid`` doesn't exist in the metadata map, raise a KeyError.

        For each key in ``keys``, remove the metadata value for the
        docid related to that key.
        
        Do not raise any error if no value exists for a given key.

        If no keys are specified, remove all metadata related to the docid.
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
        """ Return the metadata for ``docid``.

        Return a mapping of the keys and values set using ``add_metadata``.

        Raise a KeyError If metadata does not exist for ``docid``.
        """
        if self.docid_to_metadata is None:
            raise KeyError(docid)
        meta = self.docid_to_metadata[docid]
        return meta

    def new_docid(self):
        """ Return a new document id.

        The returned value is guaranteed not to be used already in this
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
