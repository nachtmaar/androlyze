
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import re

from androlyze.model.script.AndroScript import AndroScript

class Manifest(AndroScript):
    ''' Extract the android manifest file (XML) '''

    VERSION = "0.2"

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        res = self.res

        # register key
        KEY = "Manifest"
        res.register_keys([KEY])
        
        # faster way
#         # get manifest
#         manifest_xml = ""
#         for i in apk.zip.namelist():
#             if i == "AndroidManifest.xml":
#                 apk.axml[i] = AXMLPrinter(apk.zip.read(i))
#                 try:
#                     manifest_xml = apk.axml[i].get_buff()
#                 except:
#                     pass
                
        # more convenient way with pretty priting, but also slower
        manifest_str = apk.xml.items()[0][1].toprettyxml(indent=" " * 2)
        # replace multiple \n and split into list for better representation in json
        manifest_str = re.sub("\n+", "\n", manifest_str)
        manifest_list = manifest_str.split("\n")
        res.log(KEY, manifest_list)
        
#         if manifest_xml:
#             res.log(KEY, manifest_xml.split("\n"))

if __name__ == '__main__':
    
    for res in AndroScript.test(Manifest, ["../../../../../../androguard_playground/apks/ipcinetcall.apk"]):
        print res.write_to_json()