
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.log.Log import log
from androlyze.util.Util import sha256


class Hashable:
    ''' Interface for lazyly computing the hash by reading and hashing the file from `path`.
    
    You need to implement the `_get_hash` method 
    '''
    
    KEY_HASH = "sha256"
    
    def __init__(self):
        self._hash, self._path = 2 * [None]

    def _get_hash(self):
        ''' The `get_hash` method relies on this method
        to return the local variable where the hash will be stored. '''
        return self._hash
    
    def get_path(self):
        return self._path
    
    def set_hash(self, value):
        self._hash = value

    def del_path(self):
        del self._path

    def del_hash(self):
        del self._hash
        
    def set_path(self, value):
        self._path = value
    
    def get_hash(self):
        '''
        Get the sha256 message digest of the file
        and store it.
        
        Returns
        -------
        str
            sha256 message digest as hexstring
        None
            If path is None
            
        Raises
        ------
        OSError
            If the file could no be opened
        '''
        if self._get_hash() is None:
            if self.path is None:
                # cannot calculate message digest from file
                return None
            else:
                with open(self.path, "rb") as apkf:
                    self.hash = sha256(apkf.read())
                    log.debug("Calculated hash for %s by reading file %s", self, self.path)
        return self._get_hash()
    
    path = property(get_path, set_path, del_path, "str - path to file")
    hash = property(get_hash, set_hash, del_hash, "str - sha256 of raw file (hexstring)")
        