
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

# categories
CAT_CLASS_DETAILS = "class details"
CAT_METHODS = "methods"
CAT_FIELDS = "fields"

class ClassDetails(AndroScript):
    ''' Retrieve all classes and their methods and fields '''

    VERSION = "0.1"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        res = self.res

        # dvm stuff
        # list<ClassDefItem>
        classes = dalvik_vm_format.get_classes()

        # run over classes
        for c in classes:
            ROOT_CAT = (CAT_CLASS_DETAILS, c.name)
            res.register_keys([CAT_METHODS, CAT_FIELDS], *ROOT_CAT)

            # list<EncodedMethod>
            methods = c.get_methods()
            res.log(CAT_METHODS, [mn.name for mn in methods], *ROOT_CAT)

            # list<EncodedField>
            fields = c.get_fields()
            res.log(CAT_FIELDS, [fn.name for fn in fields], *ROOT_CAT)

    ############################################################
    #---Options
    ############################################################

    def needs_dalvik_vm_format(self):
        return True

if __name__ == '__main__':
    for res in AndroScript.test(ClassDetails, ["../../../../testenv/apks/a2dp.Vol.apk"]):
        print res
        print res.write_to_json()