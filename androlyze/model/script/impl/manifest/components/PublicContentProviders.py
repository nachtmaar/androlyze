
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

CAT = "public_content_providers"

class PublicContentProviders(AndroScript):
    ''' Lists all public content providers '''
    
    VERSION = "0.1"
        
    def register_structure(self, res):
        # register keys
        res.register_enum_keys([CAT])
        
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        '''
        Parameters
        ----------
        apk: EAndroApk
        dalvik_vm_format: DalvikVMFormat
            Parsed .dex file.
            Only available if `needs_dalvik_vm_format` returns True.
        vm_analysis: VMAnalysis
            Dex analyzer.
            Only available if `needs_vmanalysis` returns True.
        gvm_analysis : GVMAnalysis
        '''

        res = self.res
        self.register_structure(res)
        
        public_components = apk.get_manifest_public_components()
        for cp in apk.get_providers():
            if cp in public_components:
                res.log_append_to_enum(CAT, cp)
            
# testing code
if __name__ == '__main__':
    for res in AndroScript.test(PublicContentProviders, ["../../../../../../../androguard_playground/apks/sql_injection.apk", "../../../../../../../androguard_playground/apks/public_content_provider.apk"]):
        print res.write_to_json()
