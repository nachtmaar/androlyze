
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

#categories
CAT_ACTIVITIES = "activities" 
CAT_ACTIVITIES_MAIN = "main activity"
CAT_ACTIVITIES_LISTING = "all" 

class Activities(AndroScript):
    ''' List activities '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        res = self.res
        
        # register basic structure
        res.register_keys([CAT_ACTIVITIES_LISTING, CAT_ACTIVITIES_MAIN], CAT_ACTIVITIES)
        
        # activities        
        res.log(CAT_ACTIVITIES_LISTING, sorted(apk.get_activities()), CAT_ACTIVITIES)
        res.log(CAT_ACTIVITIES_MAIN, apk.get_main_activity(), CAT_ACTIVITIES)
