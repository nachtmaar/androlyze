
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.error.WrapperException import WrapperException

class NetworkError(WrapperException):

    def _msg(self):
        return 'Some network error occurred!'


class ScriptHashValidationError(WrapperException):

    def __init__(self, submitted_hashes, actual_hashes):
        super(ScriptHashValidationError, self).__init__()
        self.msg = """The hashes of the imported scripts don't match! Submitted hashes are: %s, actual hashes from imported scripts are: %s!
This may be a severe security problem!""" % (', '.join(submitted_hashes), ', '.join(actual_hashes))


    def _msg(self):
        return self.msg
