class BadResults(Exception):
    """ Superclass of :exc:`hypatia.exc.MultipleResults` and
    :exc:`hypatia.exc.NoResults`.  Has an attribute named ``resultset`` which
    is the resultset related to the error."""
    def __init__(self, resultset):
        self.resultset = resultset

class MultipleResults(BadResults):
    """ Raised when a method that was expected to return a single result
    returns multiple results."""

class NoResults(BadResults):
    """ Raised when a method that was expected to return at least one result
    returns zero results."""

class Unsortable(Exception):
    """ Raised when a method which was expected to sort a set of provided
    document identifiers cannot sort one or more of those identifiers.  An
    attribute named ``docids`` is a sequence containing the identifiers. """
    def __init__(self, docids):
        self.docids = docids

    def __repr__(self):
        return '%r' % (list(self.docids),)
    __str__ = __repr__
        
