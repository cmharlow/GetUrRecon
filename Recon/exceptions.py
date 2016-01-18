"Exceptions for recon work."


class ReconException(Exception):
    """Base exception class for this work"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value)
