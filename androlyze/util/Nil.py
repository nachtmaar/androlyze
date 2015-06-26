
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

class Nil(object):
    ''' Imitates the nil object from objective-c. Comparable to None, but ignores all method calls and attribute lookups. '''

    def do_nothing(self, *args, **kwargs):
        ''' Function that accepts all arguments and does nothing '''
        pass
    
    def __getattr__(self, name):
        ''' Return function that does nothing. Therefore every function call on the object does nothing '''
        return self.do_nothing

# static Nil object
nil = Nil()

if __name__ == '__main__':
    nil = nil
    nil.bar()
    nil.get_analyze_task_name