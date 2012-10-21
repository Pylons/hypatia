class BadResults(Exception):
    def __init__(self, resultset):
        self.resultset = resultset

class MultipleResults(BadResults):
    pass

class NoResults(BadResults):
    pass

