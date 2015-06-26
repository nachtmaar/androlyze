
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

#categories
CAT_CLASS_DETAILS = "class details"
CAT_METHODS = "methods"
CAT_FIELDS = "fields"

class ShowLoggingFuncs(AndroScript):
    ''' Example for demonstrating available logging options and to do some query checks '''

    VERSION = "0.1"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        res = self.res

        CAT_UNLOGGED = "category1", "category2", "unlogged"
        CAT_LOGGED = "category1", "category2", "logged"

        res.register_keys(["normal"], *CAT_LOGGED)
        res.register_keys(["normal"], *CAT_UNLOGGED)
        res.register_bool_keys(["bool"], *CAT_LOGGED)
        res.register_bool_keys(["bool"], *CAT_UNLOGGED)
        res.register_enum_keys(["enum"], *CAT_LOGGED)
        res.register_enum_keys(["enum"], *CAT_UNLOGGED)

        res.log("normal", "some value", *CAT_LOGGED)
        res.log_true("bool", *CAT_LOGGED)
        res.log_append_to_enum("enum", "list element", *CAT_LOGGED)
