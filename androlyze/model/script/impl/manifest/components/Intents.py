
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript
from androlyze.model.script.impl.manifest.components import get_components_cache, \
    component_key_2_intent_key


CAT_INTENTS = "intents"

class Intents(AndroScript):
    ''' Get intents '''
    VERSION = "0.1"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):

        res = self.res

        components_cache = get_components_cache(apk)

        # intents
        for k, package_names in components_cache.items():
            intents = {}
            for package_name in package_names:
                # get intent filter for activity, service or receiver
                intent_key = component_key_2_intent_key(k)
                package_intents = apk.get_intent_filters(intent_key, package_name)
                if package_intents:
                    intents[package_name] = package_intents

            res.register_keys([k], CAT_INTENTS)

            res.log(k, intents, CAT_INTENTS)

