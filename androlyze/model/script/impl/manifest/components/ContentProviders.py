
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

CAT_PROVIDERS = "content providers" 

class ContentProviders(AndroScript):
    ''' List content providers '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        res = self.res
        
        res.register_keys([CAT_PROVIDERS])
        res.log(CAT_PROVIDERS, apk.get_providers())
