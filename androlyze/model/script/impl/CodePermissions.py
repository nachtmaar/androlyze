
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androguard.decompiler.dad import decompile
from androlyze.model.script.AndroScript import AndroScript
from androguard.core.analysis.analysis import PathP

# categories
CAT_PERMISSIONS = "code permissions"
PERMISSIONS_LISTING = "listing"
PERMISSIONS_CODE = "code"

def full_method_signature(method):
    return '%s.%s.%s' % (method.get_class_name()[:-1], method.get_name(), method.get_descriptor())

def full_method_name(method):
    return '%s.%s' % (method.get_class_name()[:-1].replace("/", "."), method.get_name())

class CodePermissions(AndroScript):
    ''' List where permissions are used in the code and decompile them '''

    VERSION = "0.1"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        res = self.res

        res.register_keys([CAT_PERMISSIONS])

        class_manager = dalvik_vm_format.get_class_manager()
        perm_dict = vm_analysis.get_permissions([])

        # register list for each used permissions keys
        permissions = set(perm_dict.keys())

        res.register_enum_keys(permissions, CAT_PERMISSIONS, PERMISSIONS_LISTING)
        # register each permission only once!
        res.register_enum_keys(permissions, CAT_PERMISSIONS, PERMISSIONS_CODE)

        # use set to remove duplicates!
        method_names = set()
        method_analysis_objs = set()
        for permission_name, pathp_obj_list in perm_dict.items():

            # list<PathP>
            for pathp in pathp_obj_list:
                if isinstance(pathp, PathP):
                    # type: androguard.core.bytecodes.dvm.MethodIdItem
                    # the method that uses the permission
                    src_method = class_manager.get_method_ref(pathp.src_idx)
                    method_name = full_method_name(src_method)
                    method_names.add((permission_name, method_name))

                    # the api function for the permission
                    #dst_method = class_manager.get_method_ref(pathp.dst_idx)

                    # get androguard.core.bytecodes.dvm.EncodedMethod
                    encoded_method = dalvik_vm_format.get_method(src_method.get_name())[0]

                    # get androguard.core.analysis.analysis.MethodAnalysis
                    method_analysis = vm_analysis.get_method(encoded_method)

                    method_analysis_objs.add((permission_name, method_name, method_analysis))

        for permission_name, method_name in method_names:
            # log which classes use which permissions
            res.log_append_to_enum(permission_name, method_name, CAT_PERMISSIONS, PERMISSIONS_LISTING)

        for permission_name, method_name, method_analysis in method_analysis_objs:

            ms = decompile.DvMethod(method_analysis)
            ms.process()

            source_code = ms.get_source()

            # decompile these methods too!
            log_val = {method_name : source_code.split("\n")[1:-1]}
            res.log_append_to_enum(permission_name, log_val, CAT_PERMISSIONS, PERMISSIONS_CODE)

    def needs_dalvik_vm_format(self):
        return True

    def needs_vmanalysis(self):
        return True

if __name__ == '__main__':
    for res in AndroScript.test(CodePermissions, ["../../../../testenv/apks/a2dp.Vol.apk"]):
        print res
        print res.write_to_json()