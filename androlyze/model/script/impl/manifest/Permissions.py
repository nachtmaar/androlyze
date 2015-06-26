
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript


class Permissions(AndroScript):
    ''' List the permissions '''    
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        #categories
        CAT_PERMISSIONS = "permissions"
        
        res = self.res
        
        res.register_keys([CAT_PERMISSIONS])
        
        # permissions
        res.log(CAT_PERMISSIONS, sorted(apk.get_permissions()))
            