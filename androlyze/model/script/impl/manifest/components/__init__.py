
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.android.Constants import MANIFEST_ACTIVITY, \
    MANIFEST_SERVICE, MANIFEST_RECEIVER
from androlyze.util.Util import transform_key

CAT_ACTIVITIES = "activities" 
CAT_SERVICES = "services" 
CAT_RECEIVERS = "broadcast receivers" 
CAT_PROVIDERS = "content providers" 

def get_components_cache(apk):
    ''' Use components cache, so we don't need to go twice through the xml file (manifest) '''
    return {
             CAT_ACTIVITIES : apk.get_activities(),
             CAT_SERVICES : apk.get_services(),
             CAT_RECEIVERS : apk.get_receivers(),
             CAT_PROVIDERS : apk.get_providers()
            }

def component_key_2_intent_key(key):
    ''' Get the key needed to lookup intents in the manifest '''
    from_mapping = (CAT_ACTIVITIES, CAT_SERVICES, CAT_RECEIVERS, CAT_PROVIDERS)
    to_mapping = (MANIFEST_ACTIVITY, MANIFEST_SERVICE, MANIFEST_RECEIVER, None)
    return transform_key(key, from_mapping, to_mapping)