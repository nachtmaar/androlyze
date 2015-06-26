
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.storage.exception import DatabaseException

class ImportQueryError(DatabaseException):
    ''' Base exception for the `ImportQueryInterface` '''
    pass
