
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

#categories
CAT_SERVICES = "services"

class Services(AndroScript):
    ''' Read services from manifest '''

    VERSION = "0.1"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):

        res = self.res

        res.register_keys([CAT_SERVICES])

        # services
        res.log(CAT_SERVICES, apk.get_services())
