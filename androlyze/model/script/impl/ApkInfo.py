
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript
from androlyze.model.script.impl.manifest.components import get_components_cache,\
    component_key_2_intent_key

#categories
CAT_APK_INFO = "apkinfo"
CAT_FILES = "files"
CAT_PERMISSIONS = "permissions"
CAT_LIBS = "libraries" 

CAT_ACTIVITIES = "activities" 
CAT_ACTIVITIES_MAIN = "main activity"
CAT_ACTIVITIES_LISTING = "all" 

CAT_COMPONENTS = "components"
CAT_SERVICES = "services" 
CAT_RECEIVERS = "broadcast receivers" 
CAT_PROVIDERS = "content providers" 
CAT_INTENTS = "intents"

class ApkInfo(AndroScript):
    ''' Shows basic information about the .apk like e.g. permissions, files, libraries,
    components (activities, broadcast receivers, content providers, services) as wall as their intents. 
    '''
    
    VERSION = "0.1"
    
    def _register_static_structure(self):
        ''' Register the static structure '''
        res = self.res

        # register basic structure
        res.register_keys([CAT_ACTIVITIES_LISTING, CAT_ACTIVITIES_MAIN], CAT_APK_INFO, CAT_COMPONENTS, CAT_ACTIVITIES)
        
        # register components
        for k in (CAT_SERVICES, CAT_RECEIVERS, CAT_PROVIDERS, CAT_INTENTS):
            res.register_keys([k], CAT_APK_INFO, CAT_COMPONENTS)
            
        # register other
        for k in (CAT_PERMISSIONS, CAT_LIBS, CAT_FILES):
            res.register_keys([k], CAT_APK_INFO)
        
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        res = self.res
        
        # register static structure
        self._register_static_structure()
        
        # libs
        res.log(CAT_LIBS, apk.get_libraries(), CAT_APK_INFO)
        
        # files
        res.log(CAT_FILES, apk.get_files(), CAT_APK_INFO)

        # permissions
        res.log(CAT_PERMISSIONS, sorted(apk.get_permissions()), CAT_APK_INFO)
            
        components_cache = get_components_cache(apk)
        
        # activities        
        res.log(CAT_ACTIVITIES_LISTING, sorted(components_cache[CAT_ACTIVITIES]), CAT_APK_INFO, CAT_COMPONENTS, CAT_ACTIVITIES)
        res.log(CAT_ACTIVITIES_MAIN, apk.get_main_activity(), CAT_APK_INFO, CAT_COMPONENTS, CAT_ACTIVITIES)
        
        # services
        res.log(CAT_SERVICES, components_cache[CAT_SERVICES], CAT_APK_INFO, CAT_COMPONENTS)
        
        # receivers
        res.log(CAT_RECEIVERS, components_cache[CAT_RECEIVERS], CAT_APK_INFO, CAT_COMPONENTS)

        # content providers
        res.log(CAT_PROVIDERS, components_cache[CAT_PROVIDERS], CAT_APK_INFO, CAT_COMPONENTS)
        
        # intents
        for k, package_names in components_cache.items():
            intents = {}
            for package_name in package_names:
                # get intent filter for activity, service or receiver
                intent_key = component_key_2_intent_key(k)
                package_intents = apk.get_intent_filters(intent_key, package_name) 
                if package_intents:
                    intents[package_name] = package_intents
                
            # we can also register the keys later for dynamic structures
            CAT = (CAT_APK_INFO, CAT_COMPONENTS, CAT_INTENTS)
            res.register_keys([k], *CAT)
            
            res.log(k, intents, *CAT)


