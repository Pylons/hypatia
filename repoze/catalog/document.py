from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree

class DocumentMap(Persistent):
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

