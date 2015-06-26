
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript
from androlyze.log.Log import log

CAT_DECOMPILE = "decompiled_classes"

class DecompileClassesText(AndroScript):
    ''' Get the source code from the apk for each class. '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        ''' This sample code is taken from `androguard` and has been modified!

        See Also
        --------
        http://code.google.com/p/androguard/wiki/RE#Source_Code
        '''

        res = self.res

        res.register_keys([CAT_DECOMPILE])

        # androguard.core.bytecodes.dvm.ClassDefItem
        for clazz in dalvik_vm_format.get_classes():
            try:
                key = clazz.get_name() 
                # skip android classes
                if key.find("Landroid") != -1:
                    continue
                self.cres += clazz.get_source()
            except Exception as e:
                log.exception(e)

    def custom_result_object(self):
        return ("", "java")

    ############################################################
    #---Options
    ############################################################    

    def needs_dalvik_vm_format(self):
        return True
    
    def needs_vmanalysis(self):
        return True
