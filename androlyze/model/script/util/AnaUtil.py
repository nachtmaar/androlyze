
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androguard.decompiler.dad import decompile
import re

from androlyze.log.Log import log


############################################################
#---Checks
############################################################

def check_own_method_implementation(apk, encoded_method):
    ''' Check if the `encoded_method` is implemented in an own package (no third party) '''
    # package name separated with "."
    apk_pn = apk.package_name.lower()
    method_pn = convert_dalvik_pn_to_java_pn(encoded_method.get_class_name().lower())
    
    # package names equal ??
    if method_pn.find(apk_pn) != -1:
        return True
        



def check_method_contains_string(enoded_method, regexp, lowercase = True, all_findings = False):
    '''
    Check if the `encoded_method` contains the `string` in the instruction output.
    
    Parameters
    ----------
    enoded_method: androguard.core.bytecodes.dvm.EncodedMethod
    regexp: str
    lowercase: boolean, optional (default is True)
        Convert the string on which shall be matched beforehand to lowercase
    all_findings : bool, optional (default is False)
        If true, return a list of all match objects
    
    Returns
    -------
    re match object
        If not `all_findings`.
    list<re match object>
        Else
    '''
    res = []
    for instr in enoded_method.get_instructions():
        match_on = instr.get_output()
        if lowercase:
            match_on = match_on.lower()
        match_object = re.search(regexp, match_on)
        if match_object:
            if not all_findings:
                return match_object
            else:
                res.append(match_object)
    return res
        
def check_instructions_one(instructions, func):
    '''
    Check if at least one instruction matches with `func`.
    
    Parameters
    ----------
    instructions: iterable<androguard.core.bytecodes.dvm.Instruction>
    func: Instruction -> Bool
    
    Returns
    -------
    bool
    '''
    for instruction in instructions:
        if func(instruction):
            return True

############################################################
#---Decompilation
############################################################
        
def decompile_pathp(pathp, dalvik_vm_format, vm_analysis, caller = True, show_class = True):
    '''
    Decompile either the caller or callee
    
    Parameters
    ----------
    pathp: androguard.androguard.core.analysis.analysis.PathP
        Edge in method call graph.
    dalvik_vm_format: DalvikVMFormat
        Parsed .dex file.
    vm_analysis: uVMAnalysis
        Dex analyzer.
    caller: bool, optional (default is True)
        Use the src of the `pathp`, hence decompile the caller.
        Otherwise the dst is used.
    show_class : bool, optional (default is True)
        Include the package name in the decompilation.
        
    Returns
    -------
    str
        The decompiled method
    None
        N/A
        
    Example
    -------
    >>> decompile_pathp(...)
    protected varargs String doInBackground(Void[] p14)
    {
        org.apache.http.client.methods.HttpGet v6_1 = new org.apache.http.client.methods.HttpGet("http://10.10.0.134:8080/index.html");
        v6_1.addHeader("Authorization", new StringBuilder().append("Basic ").append(android.util.Base64.encodeToString(this.CREDENTIALS.getBytes(), 2)).toString());
        try {
            java.io.InputStream v9 = new org.apache.http.impl.client.DefaultHttpClient().execute(v6_1).getEntity().getContent();
            int v7 = de.uni_marburg.ipcinetcallee.InetActivity.inputStream2String(v9);
            v9.close();
        } catch (org.apache.http.client.ClientProtocolException v2) {
            android.util.Log.e("HTTPGetTask", "msg", v2);
            v7 = 0;
        } catch (java.io.IOException v5) {
            android.util.Log.e("HTTPGetTask", "msg", v5);
        }
        return v7;
    }
    '''
    idx = pathp.src_idx if caller else pathp.dst_idx
    encoded_method = dalvik_vm_format.get_method_by_idx(idx)
    
    if encoded_method is not None:
        method_analysis = vm_analysis.get_method(encoded_method)
        
        res = ""
        if show_class:
            res += "class %s\n" % encoded_method.get_class_name()
            
        res += decompile_method_analysis(method_analysis)
            
        return res
    
# TODO: ADD MORE DECOMPILERS!
def decompile_method_analysis(method_analysis):
    '''
    Decompile the `method_analysis` object
    
    Parameters
    ----------
    method_analysis: androguard.androguard.core.analysis.analysis.MethodAnalysis
        
    Returns
    -------
    str
        The decompiled method
        
    Example
    -------
    >>> decompile_method_analysis(...)
    protected varargs String doInBackground(Void[] p14)
    {
        org.apache.http.client.methods.HttpGet v6_1 = new org.apache.http.client.methods.HttpGet("http://10.10.0.134:8080/index.html");
        v6_1.addHeader("Authorization", new StringBuilder().append("Basic ").append(android.util.Base64.encodeToString(this.CREDENTIALS.getBytes(), 2)).toString());
        try {
            java.io.InputStream v9 = new org.apache.http.impl.client.DefaultHttpClient().execute(v6_1).getEntity().getContent();
            int v7 = de.uni_marburg.ipcinetcallee.InetActivity.inputStream2String(v9);
            v9.close();
        } catch (org.apache.http.client.ClientProtocolException v2) {
            android.util.Log.e("HTTPGetTask", "msg", v2);
            v7 = 0;
        } catch (java.io.IOException v5) {
            android.util.Log.e("HTTPGetTask", "msg", v5);
        }
        return v7;
    }
    '''
    dv_method = decompile.DvMethod(method_analysis)
    dv_method.process()
    return dv_method.get_source()

############################################################
#---Disassembly
############################################################
        
def disassemble_encoded_method(encoded_method):
    '''
    Create the disassemble of the `encoded_method`
    
    Parameters
    ----------
    encoded_method : androguard.androguard.core.bytecodes.dvm.EncodedMethod
    
    Returns
    -------
    str
        The disassembled method
        
    Example
    -------
    >>> disassemble_encoded_method(...)
    Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask; doInBackground ([Ljava/lang/Void;)Ljava/lang/String;
    0 new-instance v6, Lorg/apache/http/client/methods/HttpGet;
    4 const-string v10, 'http://10.10.0.134:8080/index.html'
    8 invoke-direct v6, v10, Lorg/apache/http/client/methods/HttpGet;-><init>(Ljava/lang/String;)V
    e iget-object v10, v13, Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask;->CREDENTIALS Ljava/lang/String;
    12 invoke-virtual v10, Ljava/lang/String;->getBytes()[B
    18 move-result-object v10
    1a const/4 v11, 2
    1c invoke-static v10, v11, Landroid/util/Base64;->encodeToString([B I)Ljava/lang/String;
    22 move-result-object v0
    24 const-string v10, 'Authorization'
    28 new-instance v11, Ljava/lang/StringBuilder;
    2c invoke-direct v11, Ljava/lang/StringBuilder;-><init>()V
    32 const-string v12, 'Basic '
    36 invoke-virtual v11, v12, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    3c move-result-object v11
    3e invoke-virtual v11, v0, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    44 move-result-object v11
    46 invoke-virtual v11, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    4c move-result-object v11
    4e invoke-interface v6, v10, v11, Lorg/apache/http/client/methods/HttpUriRequest;->addHeader(Ljava/lang/String; Ljava/lang/String;)V
    54 new-instance v4, Lorg/apache/http/impl/client/DefaultHttpClient;
    58 invoke-direct v4, Lorg/apache/http/impl/client/DefaultHttpClient;-><init>()V
    5e const-string v3, ''
    62 const/16 v10, 8192
    66 new-array v1, v10, [B
    6a invoke-interface v4, v6, Lorg/apache/http/client/HttpClient;->execute(Lorg/apache/http/client/methods/HttpUriRequest;)Lorg/apache/http/HttpResponse;
    70 move-result-object v8
    72 invoke-interface v8, Lorg/apache/http/HttpResponse;->getEntity()Lorg/apache/http/HttpEntity;
    78 move-result-object v10
    7a invoke-interface v10, Lorg/apache/http/HttpEntity;->getContent()Ljava/io/InputStream;
    80 move-result-object v9
    82 invoke-static v9, Lde/uni_marburg/ipcinetcallee/InetActivity;->inputStream2String(Ljava/io/InputStream;)Ljava/lang/String;
    88 move-result-object v7
    8a invoke-virtual v9, Ljava/io/InputStream;->close()V
    90 return-object v7
    92 move-exception v2
    94 const-string v10, 'HTTPGetTask'
    98 const-string v11, 'msg'
    9c invoke-static v10, v11, v2, Landroid/util/Log;->e(Ljava/lang/String; Ljava/lang/String; Ljava/lang/Throwable;)I
    a2 const/4 v7, 0
    a4 goto -a
    a6 move-exception v5
    a8 const-string v10, 'HTTPGetTask'
    ac const-string v11, 'msg'
    b0 invoke-static v10, v11, v5, Landroid/util/Log;->e(Ljava/lang/String; Ljava/lang/String; Ljava/lang/Throwable;)I
    b6 goto -a
    '''
    # add method signature
    disassembly = fmt_encoded_method(encoded_method) + "\n"
    
    idx = 0
    for i in encoded_method.get_instructions():
        disassembly += "%x %s %s\n" % (idx, i.get_name(), i.get_output())
        idx += i.get_length()
        
    return disassembly

def disassemble_pathp(pathp, dalvik_vm_format, caller = True):
    '''
    Disassemble either the caller or callee.
    
    Parameters
    ----------
    pathp: androguard.androguard.core.analysis.analysis.PathP
        Edge in method call graph.
    dalvik_vm_format: DalvikVMFormat
        Parsed .dex file.
    caller: bool, optional (default is True)
        Use the src of the `pathp`, hence disassemble the caller.
        Otherwise the dst is used.
        
    Returns
    -------
    str
        The disassembled method.
    None
        N/A
        
        
    See :py:method:`.disassemble_encoded_method`
    '''
    idx = pathp.src_idx if caller else pathp.dst_idx
    encoded_method = dalvik_vm_format.get_method_by_idx(idx)
    
    if encoded_method is not None:
        return disassemble_encoded_method(encoded_method)

############################################################
#---Filtering
############################################################

def filter_own_implementations(apk, dalvik_vm_format, pathp_list):        
    '''
    Filter the `PathP` objects which are inside the apk package
    
    Parameters
    ----------
    apk: Apk
        The apk representation
    dalvik_vm_format: DalvikVMFormat
        Parsed .dex file.
    pathp_list: list<androguard.androguard.core.analysis.analysis.PathP>
    
    Returns
    -------
    list<androguard.androguard.core.analysis.analysis.PathP>
    '''
    pathp_list_check = []
    
    for pathp in pathp_list:
                 
        encoded_method = dalvik_vm_format.get_method_by_idx(pathp.src_idx)
        
        # package name separated with "."
        apk_pn = apk.package_name.lower()
        method_pn = convert_dalvik_pn_to_java_pn(encoded_method.get_class_name().lower())
        
        # package names equal ??
        if method_pn.find(apk_pn) != -1:
            pathp_list_check.append(pathp)
    
    return pathp_list_check

############################################################
#---Abstract Syntax Tree (AST)
############################################################

def ast_for_pathp(pathp, dalvik_vm_format, vm_analysis, caller = True):
    '''
    Disassemble either the caller or callee.
    
    Parameters
    ----------
    pathp: androguard.androguard.core.analysis.analysis.PathP
        Edge in method call graph.
    dalvik_vm_format: DalvikVMFormat
        Parsed .dex file.
    vm_analysis: VMAnalysis
        Dex analyzer.
    caller: bool, optional (default is True)
        Use the src of the `pathp`, hence disassemble the caller.
        Otherwise the dst is used.
        
    Returns
    -------
    str
        The disassembled method.
    None
        N/A
    '''
    idx = pathp.src_idx if caller else pathp.dst_idx
    encoded_method = dalvik_vm_format.get_method_by_idx(idx)
    
    if encoded_method is not None:
        return ast_for_method_analysis(vm_analysis.get_method(encoded_method))
    
def ast_for_method_analysis(method_analysis):
    '''
    Create the abstract syntax tree.
    
    Parameters
    ----------
    method_analysis: androguard.androguard.core.analysis.analysis.MethodAnalysis
        
    Returns
    -------
    dict
        The abstract syntax tree of the `method_analysis`.
    '''
    dv_method = decompile.DvMethod(method_analysis)
    dv_method.process(doAST = True)
    return dv_method.ast

def ast_get_containing_collection(iterable, pattern):
    '''
    Check the structure recursive for matches with the regex `pattern` and return the collection that contains the match. 
    
    Parameters
    ----------
    iterable: iterable
    pattern: str
        Regex
        
    Returns
    -------
    iterable
    '''
    def ast_get_containing_collection_inner(iterable, pattern, containing_collection, findings):

        def do_check(on, containing_collection):
            if isinstance(on, (str, unicode)):

                mo = re.search(pattern, on)
                if mo:
                    findings.append(containing_collection)

                return mo

        # dict
        if isinstance(iterable, dict):

            # recursively check all keys and values
            for k, v in iterable.items():
                # do check (method has side-effect!) 
                do_check(k, iterable)
                # recursively check value too
                ast_get_containing_collection_inner(v, pattern, iterable, findings)

        # lists, sets
        elif isinstance(iterable, (tuple, list, set)):
            for it in iterable:
                ast_get_containing_collection_inner(it, pattern, iterable, findings)

        # do_check on value
        else:
            do_check(iterable, containing_collection)

        return findings

    return ast_get_containing_collection_inner(iterable, pattern, iterable, [])

############################################################
#---Formatting
############################################################

def fmt_encoded_method(encoded_method):
    '''
    Return a string represenation of `encoded_method`.
    
    Parameters
    ----------
        encoded_method : androguard.androguard.core.bytecodes.dvm.EncodedMethod

    Returns
    -------
    str
    
    Example
    -------
    >>> fmt_encoded_method(...)
    Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask; doInBackground ([Ljava/lang/Void;)Ljava/lang/String;
    '''
    return "%s %s %s" % (encoded_method.get_class_name(), encoded_method.get_name(), encoded_method.get_descriptor())

############################################################
#---Converting
############################################################

def convert_dalvik_pn_to_java_pn(dalvik_pn, ignore_inner_class = True):
    ''' Convert e.g. "Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask;" to "de.uni_marburg.ipcinetcall.InetActivity"
    
    Parameters
    ----------
    ignore_inner_class : bool, optional (default is True)
        Strip inner class names like $HTTPGetTask
    
    Returns
    -------
    str
    
    Example
    -------
    >>> print convert_dalvik_pn_to_java_pn('Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask;', True)
    "de.uni_marburg.ipcinetcallee.InetActivity"
    
    >>> print convert_dalvik_pn_to_java_pn('Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask;', False)
    "de.uni_marburg.ipcinetcallee.InetActivity.HTTPGetTask"
    '''
    package_name = dalvik_pn[1:]
    package_name = package_name.replace("/", ".")
    package_name = package_name[:-1]
    if not ignore_inner_class:
        package_name = re.sub("\$d*", ".", package_name)
    else:
        dollar_idx = package_name.find("$")
        if dollar_idx != -1:
            package_name = package_name[:dollar_idx]
    
    return package_name

def convert_java_pn_to_dalvik(java_pn):
    ''' Convert e.g. "de.uni_marburg.ipcinetcall.InetActivity" to "Lde/uni_marburg/ipcinetcallee/InetActivity;"
    
    Parameters
    ----------
    java_pn: str
        Package name separated with "."
    
    Returns
    -------
    str
    '''
    java_pn = java_pn.replace(".", "/")
    return 'L%s;' % java_pn

if __name__ == '__main__':
    print convert_dalvik_pn_to_java_pn('Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask;', True)
    print convert_dalvik_pn_to_java_pn('Lde/uni_marburg/ipcinetcallee/InetActivity$HTTPGetTask;', False)
    print convert_java_pn_to_dalvik('de.uni_marburg.ipcinetcallee.InetActivity')