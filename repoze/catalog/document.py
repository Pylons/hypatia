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

        ``docid``, if passed, must be an int.  In this case, remove
        any previous address stored for it before mapping it to the
        new address.  Passing an explicit ``docid`` also removes any
        metadata associated with that docid.
        
        If ``docid`` is not passed, generate a new docid.

        Return the integer document id mapped to ``address``.
        """
        if docid is _marker:
            docid = self.new_docid()

        self.remove_docid(docid)
        self.remove_address(address)

        self.docid_to_address[docid] = address
        self.address_to_docid[address] = docid
        return docid

    def remove_docid(self, docid):
        """ Remove a document from the document map for the given document ID.

        ``docid`` is an integer document id.

        Remove any corresponding metadata for ``docid`` as well.

        Return a True if ``docid`` existed in the map, else return False.
        """
        # It should be an invariant that if one entry exists in
        # docid_to_address for a docid/address pair, exactly one
        # corresponding entry exists in address_to_docid for the same
        # docid/address pair.  However, versions of this code before
        # r.catalog 0.7.3 had a bug which, if this method was called
        # multiple times, each time with the same address but a
        # different docid, the ``docid_to_address`` mapping could
        # contain multiple entries for the same address each with a
        # different docid, causing this invariant to be violated.  The
        # symptom: in systems that used r.catalog 0.7.2 and lower,
        # there might be more entries in docid_to_address than there
        # are in address_to_docid.  The conditional fuzziness in the
        # code directly below is a runtime kindness to systems in that
        # state.  Technically, the administrator of a system in such a
        # state should normalize the two data structures by running a
        # script after upgrading to 0.7.3.  If we made the admin do
        # this, some of the code fuzziness below could go away,
        # replaced with something simpler.  But there's no sense in
        # breaking systems at runtime through being a hardass about
        # consistency if an unsuspecting upgrader has not yet run the
        # data fixer script. The "fix the data" mantra rings a
        # little hollow when you weren't the one who broke the data in
        # the first place ;-)

        self._check_metadata()

        address = self.docid_to_address.get(docid, _marker)
        if address is _marker:
            return False
        
        old_docid = self.address_to_docid.get(address, _marker)
        if (old_docid is not _marker) and (old_docid != docid):
            self.remove_docid(old_docid)

        if docid in self.docid_to_address:
            del self.docid_to_address[docid]
        if address in self.address_to_docid:
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
        # See the comment in remove_docid for complexity rationalization
        
        self._check_metadata()

        docid = self.address_to_docid.get(address, _marker)
        if docid is _marker:
            return False
        
        old_address = self.docid_to_address.get(docid, _marker)
        if (old_address is not _marker) and (old_address != address):
            self.remove_address(old_address)

        if docid in self.docid_to_address:
            del self.docid_to_address[docid]
        if address in self.address_to_docid:
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
        document map.
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
            meta = self.docid_to_metadata.get(docid, _marker)
            if meta is _marker:
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
