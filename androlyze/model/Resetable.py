
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

class Resetable:
    ''' Interface for classes that can reset themselves '''
    
    def reset(self):
        ''' Reset the class '''
        raise NotImplementedError 