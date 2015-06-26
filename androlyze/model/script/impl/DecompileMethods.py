
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androguard.decompiler.dad import decompile
from androlyze.model.script.AndroScript import AndroScript

CAT_DECOMPILE = "decompiled_methods"

class DecompileMethods(AndroScript):
    ''' Get the source code from the apk for each method. '''

    VERSION = "0.1"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        ''' This sample code is taken from `androguard` and has been modified!

        See Also
        --------
        http://code.google.com/p/androguard/wiki/RE#Source_Code
        '''

        res = self.res

        res.register_keys([CAT_DECOMPILE])

        # CFG
        for method in dalvik_vm_format.get_methods():
            mx = vm_analysis.get_method(method)

            if method.get_code() == None:
                continue
            try:
                classname, methodname, method_descriptor = method.get_class_name(), method.get_name(), method.get_descriptor()
                
                # skip android classes
                if classname.find("Landroid") != -1:
                    continue
                CAT = (CAT_DECOMPILE, classname, methodname)
                res.register_keys([method_descriptor], *CAT)
    
                ms = decompile.DvMethod(mx)
                # process to the decompilation
                ms.process()
    
                # get the source !
                res.log(method_descriptor, ms.get_source().split("\n"), *CAT)
            except:
                pass
            
    ############################################################
    #---Options
    ############################################################

    def needs_dalvik_vm_format(self):
        return True

    def needs_vmanalysis(self):
        return True
