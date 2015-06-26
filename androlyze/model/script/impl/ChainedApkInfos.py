
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script import ScriptUtil
from androlyze.model.script.ChainedScript import ChainedScript
from androlyze.model.script.impl.manifest.Files import Files
from androlyze.model.script.impl.manifest.Libs import Libs
from androlyze.model.script.impl.manifest.Permissions import Permissions
from androlyze.model.script.impl.manifest.components.Activities import Activities
from androlyze.model.script.impl.manifest.components.BroadcastReceivers import BroadcastReceivers
from androlyze.model.script.impl.manifest.components.ContentProviders import ContentProviders
from androlyze.model.script.impl.manifest.components.Intents import Intents
from androlyze.model.script.impl.manifest.components.Services import Services
from androlyze.model.script.impl.manifest.Manifest import Manifest
from androlyze.model.script.impl.manifest.components.PublicContentProviders import PublicContentProviders

class ChainedApkInfos(ChainedScript):
    ''' The same as the `ApkInfo` script, but build using modular scripts chained together '''

    VERSION = "0.1"

    def chain_scripts(self):
        # use the chained_script function to do further grouping
        components = ScriptUtil.chained_script([Activities(), Services(), BroadcastReceivers(),
                                                ContentProviders(), PublicContentProviders(),
                                                 Intents()], ("components", ), name = "components")

        return [components, Permissions(), Libs(), Files(), Manifest()]

    def root_categories(self):
        return ('apkinfo', )

    def log_chained_script_meta_infos(self):
        ''' By default some information will be logged.
        Like e.g. the scripts used, which ran successful and which failed.
        '''
        return False