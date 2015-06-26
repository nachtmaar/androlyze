
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

CAT_CLASSES = "classes"        

class ClassListing(AndroScript):
    ''' List all classes from the dex file '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        
        res = self.res
        
        # dvm stuff
        res.register_keys([CAT_CLASSES])
        
        # dvm stuff
        # list<ClassDefItem>
        classes = dalvik_vm_format.get_classes()
        
        # class listing
        res.log(CAT_CLASSES, [c.name for c in classes])
        
    ############################################################
    #---Options
    ############################################################    
    
    def needs_dalvik_vm_format(self):
        return True
