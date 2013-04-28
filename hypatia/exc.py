class BadResults(Exception):
    def __init__(self, resultset):
        self.resultset = resultset

class MultipleResults(BadResults):
    pass

class NoResults(BadResults):
    pass

class Unsortable(Exception):
    def __init__(self, docids):
        self.docids = docids

    def __repr__(self):
        return '%r' % (list(self.docids),)
    __str__ = __repr__
        
