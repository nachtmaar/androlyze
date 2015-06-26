
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

class GVMAnalysisExample(AndroScript):
    ''' Example that uses the `GVMAnalysis` object from `androguard` to create a graph '''
    
    VERSION = "0.1"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        self.cres = gvm_analysis.export_to_gexf()

    def custom_result_object(self):
        '''
        Overwrite this method, if you want to use your own result logging framework/object,
        You can supply it here and access it via `self.cres`.
        
        E.g. you could return ("", "txt") for simply logging with a string to a .txt file.
        
        Returns
        -------
        tuple<object, str>
            First argument is the result object you want to use,
            the second is the file name extension used for storage (without a leading point)
        '''
        # Simply use str for logging
        # The first parameter isn't needed at all,
        # because we only set the result at the end of the _analyze method
        return ("", "gexf")
    
    def needs_gvmanalysis(self):
        return True
    