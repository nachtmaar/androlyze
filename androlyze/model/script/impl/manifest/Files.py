
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript


class Files(AndroScript):
    ''' List the files of the .apk '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        #categories
        CAT_FILES = "files"
        
        res = self.res
        
        res.register_keys([CAT_FILES])
        
        # files
        res.log(CAT_FILES, apk.get_files())
