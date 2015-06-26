
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys
from datetime import datetime
import importlib
import json
from os.path import basename

from androlyze.loader.exception import NoAndroScriptSubclass, \
    ModuleNotSameClassNameException
from androlyze.log.Log import log
from androlyze.util import Util


def import_scripts(script_list, via_package = False, _reload = False, clazz_name = None):
    '''
    Import the scripts (via file path or package name - configurable via `via_pacakge`).

    Parameters
    ----------
    script_list: list<str>
        list of script names (absolute path) or package names.
    via_package : bool, optional (default is False)
        If true, assume package names are given instead of file paths.
    _reload : bool, optional (default is False)
        Reload scripts and delete them from internal cache.
        Only possible if `via_package`.
    clazz_name : optional (default is None)
        The name of the class to import. If none, use the name of the module. 

    Returns
    -------
    list<type<AndroScript>>
        list of uninstantiated AndroScript classes

    Raises
    ------
    AnalyzeError
        If an NoAndroScriptSubclass, IOError or ModuleNotSameClassNameException has been raised.
    ImportError
    '''
    # late import -> pervent recursive import
    from androlyze.model.script.AndroScript import AndroScript
    from androlyze.analyze.exception import AnalyzeError
    androscripts = []

    # reload scripts if wanted
    if via_package and _reload:
        for script_package in script_list:
            log.debug("deleting %s from system modules", script_package)
            try:
                del sys.modules[script_package]
                log.debug("deleted")
            except KeyError:
                pass

    for script in script_list:
        class_name = clazz_name
        
        if not class_name:
            if via_package:
                class_name = script.split(".")[-1]
            else:
                class_name = basename(script.split(".py")[0])

        # class name must be equivalent to the module name!
        try:
            module_package = script
            # get package name from path and cut off file extension
            if not via_package:
                module_package = Util.path_2_package_name(script)
            module = importlib.import_module(module_package)
            clazz = getattr(module, class_name)
            # check if class is derived from AndroScript
            if isinstance(clazz, AndroScript.__class__):
                androscripts.append(clazz)
            else:
                raise NoAndroScriptSubclass(clazz), None, sys.exc_info()[2]
        except AttributeError as e:
            raise ModuleNotSameClassNameException(script, class_name), None, sys.exc_info()[2]
        except IOError as e:
            e.filename = script
            raise
        except (NoAndroScriptSubclass, ModuleNotSameClassNameException, IOError) as e:
            raise AnalyzeError(e), None, sys.exc_info()[2]

    return androscripts

def instantiate_scripts(script_list, script_paths = None, script_hashes = None):
    ''' Instantiate the `AndroScript`s and return them.

    Parameters
    ----------
    script_list : list<type<AndroScript>>
    script_paths : list<str>, optional (default is None)
        If given, set the path of the `AndroScript` (needed for hashing)
    script_hashes : list<str>, optional (default is [])
        If given, set the hash of the `AndroScript` directly (without hashing the file from path)

    Returns
    -------
    list<AndroScript>

    Raises
    ------
    AndroScriptError
        If an error happened while initializing some `AndroScript`
    '''
    from androlyze.analyze.exception import AndroScriptError
    instantiated_scripts = None

    try:
        instantiated_scripts = [s() for s in script_list]
        # set paths
        if script_paths is not None or script_hashes is not None:
            for idx, s in enumerate(instantiated_scripts):
                # calculate hash from path
                if script_paths is not None:
                    s.path = script_paths[idx]
                # set hash directly
                if script_hashes is not None:
                    s.hash = script_hashes[idx]

        return instantiated_scripts
    except Exception as e:
        raise AndroScriptError(s, e), None, sys.exc_info()[2]

def get_minimum_script_options(androscripts):
    ''' Get the maximum script options that any of `androscripts` needs.

    These are the minimum options needed to run the `androscripts`.

    Parameters
    ----------
    androscripts : list<AndroScript>

    Returns
    -------
    tuple<bool>
    '''
    needs_xref, needs_dref, dalvik_vm_format, vm_analysis, gvm_analysis = 5 * [False]
    for ascript in androscripts:
        if ascript.needs_xref(): needs_xref = True
        if ascript.needs_dref(): needs_dref = True
        if ascript.needs_dalvik_vm_format(): dalvik_vm_format = True
        if ascript.needs_vmanalysis(): vm_analysis = True
        if ascript.needs_gvmanalysis(): gvm_analysis = True

    if gvm_analysis:
        vm_analysis = True

    if vm_analysis:
        dalvik_vm_format = True

    return dalvik_vm_format, vm_analysis, gvm_analysis, needs_xref, needs_dref

def androscript_options_descr(androscripts):
    '''
    Format the minimum options to run the `androscripts`.

    Parameters
    ----------
    androscripts : list<AndroScript>

    Returns
    -------
    tuple<bool>
    '''
    dalvik_vm_format, vm_analysis, gvm_analysis, needs_xref, needs_dref = get_minimum_script_options(androscripts)
    return '''Minimum script needs:
DalvikVMFormat: %s
VMAnalysis: %s
GVMAnalysis: %s
Create xref: %s
Create dref: %s
    ''' % (dalvik_vm_format, vm_analysis, gvm_analysis, needs_xref, needs_dref)

def chained_script(androscripts, root_categories = (), name = None,
                   log_chained_script_meta_infos = False, continue_on_script_failure = True,
                   log_script_failure_exception = False):

    ''' Factory method for creating a `ChainedScript`. Can be used to do further grouping.
    E.g. group the results of multiple scripts under the given `root_categories`

    Parameters
    ----------
    androscripts : list<AndroScript>, optional (default is [])
        List of scripts to use (instantiated classes!)
    root_categories : tuple<str>, optional (default is ())
        Categories under which you want to store the results of the scripts.
        Empty tuple means no category at all
    name : str, optional (default is class name))
        If given set the name of the created class.
    log_chained_script_meta_infos : bool, optional (default is False)
        Will be passed to the `ChainedScript` subclass.
        Meaning no meta information will be created from it (related to the chained scripts)
    continue_on_script_failure : bool, optional (default is True)
    log_script_failure_exception : bool, optional (default is False)

    Returns
    -------
    ChainedScript
    '''
    from androlyze.model.script.ChainedScript import ChainedScript

    return ChainedScript(androscripts = androscripts,
                         root_categories = root_categories,
                         name = name,
                         log_chained_script_meta_infos = log_chained_script_meta_infos,
                         continue_on_script_failure = continue_on_script_failure,
                         log_script_failure_exception = log_script_failure_exception
                         )

def is_result_object(obj):
    from androlyze.model.analysis.result.ResultObject import ResultObject
    return isinstance(obj, ResultObject)

def dict2json(d):
    ''' Convert the dict `d` to json
    and convert any datetime object to iso8601.
    Can also convert `bson.objectid.ObjectId
    '''
    from bson.objectid import ObjectId

    def converter(obj):
        if isinstance(obj, datetime):
            return Util.datetime_to_iso8601(obj)
        elif isinstance(obj, ObjectId):
            return str(obj)

    return json.dumps(d, indent = 4,
                      # use converter
                       default = converter)

