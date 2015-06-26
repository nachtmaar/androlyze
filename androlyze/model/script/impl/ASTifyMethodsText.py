
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from pprint import pformat

from androlyze.log.Log import log
from androlyze.model.script.AndroScript import AndroScript
from androlyze.model.script.util import AnaUtil


class ASTifyMethodsText(AndroScript):
    ''' Get the AST (abstract syntax tree) for each method. '''
    
    VERSION = "0.3"
    
    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):    
        
        # CFG
        for encoded_method in dalvik_vm_format.get_methods():
            try:
                method_analysis = vm_analysis.get_method(encoded_method)
            
                if encoded_method.get_code() == None:
                    continue
                
                classname = encoded_method.get_class_name()
                
                # skip android classes due to mongo db document limit
                if classname.find("Landroid") != -1:
                    continue
                
                ast = None
                if method_analysis is not None:
                    ast = AnaUtil.ast_for_method_analysis(method_analysis)
                
                if ast is not None:    
                    self.cres += '%s\n\n' % pformat(ast)
            except Exception as e:
                log.exception(e)

    def custom_result_object(self):
        return ("", "json")

    ############################################################
    #---Options
    ############################################################    

    def needs_dalvik_vm_format(self):
        return True
    
    def needs_vmanalysis(self):
        return True
