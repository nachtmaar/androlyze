
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androguard.decompiler.dad import decompile
from androlyze.log.Log import log
from androlyze.model.script.AndroScript import AndroScript

CAT_DECOMPILE = "decompiled_classes"


class DecompileClasses(AndroScript):
    ''' Get the source code from the apk for each class. '''
    
    VERSION = "0.2"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        ''' This sample code is taken from `androguard` and has been modified!

        See Also
        --------
        http://code.google.com/p/androguard/wiki/RE#Source_Code
        '''

        res = self.res

        # androguard.core.bytecodes.dvm.ClassDefItem
        for clazz in dalvik_vm_format.get_classes():
            try:
                key = clazz.get_name() 
                # skip android classes due to mongo db document limit
                if key.find("Landroid") != -1:
                    continue
                # allows querying for package name
                res.register_keys([key], CAT_DECOMPILE)
                res.log(key, clazz.get_source().split("\n"), CAT_DECOMPILE)
            except Exception as e:
                log.exception(e)

    ############################################################
    #---Options
    ############################################################    

    def needs_dalvik_vm_format(self):
        return True
    
    def needs_vmanalysis(self):
        return True
