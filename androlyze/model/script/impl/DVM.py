
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.ChainedScript import ChainedScript
from androlyze.model.script.impl.ClassDetails import ClassDetails
from androlyze.model.script.impl.ClassListing import ClassListing
from androlyze.model.script.impl.DecompileClassesText import DecompileClassesText

class DVM(ChainedScript):
    ''' List classes as well as their details (methods and fields) and create Disassembly '''

    VERSION = "0.1"

    ############################################################
    #---ChainedScript options
    ############################################################

    def chain_scripts(self):
        return [ClassListing(), ClassDetails(), DecompileClassesText()]

    def continue_on_script_failure(self):
        ''' Specify if the analysis shall continue if a script encounters an error '''
        return True

    def log_script_failure_exception(self):
        ''' If true, write the exception into the result file'''
        return True

    def create_script_stats(self):
        ''' If true, create some script statistics and
        write them into the `ResultObject` (at least if used)'''
        return True


if __name__ == '__main__':
    from androlyze.model.script.AndroScript import AndroScript

    for res in AndroScript.test(DVM, ["../../../../testenv/apks/a2dp.Vol.apk"]):
        # get result object
        print res
        print
        # get json
        print res.write_to_json()