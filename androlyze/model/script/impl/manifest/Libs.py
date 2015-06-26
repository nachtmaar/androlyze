
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript


class Libs(AndroScript):
    ''' List the libraries '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        #categories
        CAT_LIBS = "libraries" 
        
        res = self.res
        
        # libs
        res.register_keys([CAT_LIBS])
        res.log(CAT_LIBS, apk.get_libraries())
