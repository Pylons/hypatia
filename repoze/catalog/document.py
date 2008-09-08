import random

from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree

import BTrees

class DocumentMap(Persistent):
    _v_nextid = None
    family = BTrees.family32
    _randrange = random.randrange

    def __init__(self):
        self.docid_to_path = IOBTree()
        self.path_to_docid = OIBTree()

    def add(self, docid, path):
        self.docid_to_path[docid] = path
        self.path_to_docid[path] = docid

    def remove_docid(self, docid):
        path = self.docid_to_path.get(docid)
        if path is None:
            return
        del self.docid_to_path[docid]
        del self.path_to_docid[path]

    def remove_path(self, path):
        docid = self.path_to_docid.get(path)
        if docid is None:
            return
        del self.docid_to_path[docid]
        del self.path_to_docid[path]

    def docid_for_path(self, path):
        return self.path_to_docid.get(path)

    def path_for_docid(self, docid):
        return self.docid_to_path.get(docid)

    def new_docid(self):
        """Generate an id which is not yet taken.

        This tries to allocate sequential ids so they fall into the
        same BTree bucket, and randomizes if it stumbles upon a
        used one.
        """
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(0, self.family.maxint)
            uid = self._v_nextid
            self._v_nextid += 1
            if uid not in self.docid_to_path:
                return uid
            self._v_nextid = None


