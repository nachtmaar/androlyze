
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.error.WrapperException import WrapperException

class KeyNotRegisteredError(WrapperException):
    ''' Exception for the case that a key has not been registered '''

    def __init__(self, key, *categories):
        self._key = key
        category_str = None
        if categories:
            category_str = '/'.join(str(y) for y in categories)
        self._category = category_str

    def __str__(self):
        category_msg = "for the category %s" % self._category if self._category is not None else ""
        return 'The key %s needs to be registered %s first!' % (self._key, category_msg)