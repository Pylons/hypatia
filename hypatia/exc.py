class ResultsException(Exception):
    def __init__(self, resultset):
        self.resultset = resultset

class MultipleResultsFound(ResultsException):
    pass

class NoResultsFound(ResultsException):
    pass

