
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androguard.decompiler.dad import decompile
from androlyze.model.script.AndroScript import AndroScript

class DecompileMethodsText(AndroScript):
    ''' Get the source code from the apk for each method. '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        # CFG
        for method in dalvik_vm_format.get_methods():
            try:
                mx = vm_analysis.get_method(method)
            
                if method.get_code() == None:
                    continue
                
                classname, methodname, method_descriptor = method.get_class_name(), method.get_name(), method.get_descriptor()
                
                    # skip android classes due to mongo db document limit
                if classname.find("Landroid") != -1:
                    continue
                
                ms = decompile.DvMethod(mx)
                # process to the decompilation
                ms.process()
                
                self.cres += '''%s.%s%s {
    %s
    }
''' % (classname, methodname, method_descriptor, ms.get_source())
            except:
                pass

        
    def custom_result_object(self):
        return ("", "java")

    ############################################################
    #---Options
    ############################################################    

    def needs_dalvik_vm_format(self):
        return True
    
    def needs_vmanalysis(self):
        return True
