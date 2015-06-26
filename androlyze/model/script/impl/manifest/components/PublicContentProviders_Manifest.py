
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript
from androlyze.model.script.ChainedScript import ChainedScript
from androlyze.model.script.impl.manifest.Manifest import Manifest
from androlyze.model.script.impl.manifest.components.ContentProviders import ContentProviders
from androlyze.model.script.impl.manifest.components.PublicContentProviders import PublicContentProviders


class PublicContentProviders_Manifest(ChainedScript):
    ''' Additionally to `PublicContentProviders` also show all content providers and the manifest ''' 
    
    VERSION = "0.1"

    def chain_scripts(self):
        # use the chained_script function to do further grouping
        return [PublicContentProviders(), ContentProviders(), Manifest()]

    def root_categories(self):
        return ('ContentProviderStuff', )

    def log_chained_script_meta_infos(self):
        return False
    
# testing code
if __name__ == '__main__':
    for res in AndroScript.test(PublicContentProviders_Manifest, ["../../../../../../../androguard_playground/apks/public_content_provider.apk"]):
        print res.write_to_json()