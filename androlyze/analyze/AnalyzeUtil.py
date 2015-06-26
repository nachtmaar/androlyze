
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from datetime import timedelta
from itertools import repeat, chain
import struct
import sys
from time import time
from zipfile import BadZipfile

from androguard.core.analysis.analysis import uVMAnalysis
from androguard.core.analysis.ganalysis import GVMAnalysis
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.misc import *
from androlyze.analyze.exception import DexError
from androlyze.loader.exception import CouldNotOpenApk
from androlyze.log.Log import log
from androlyze.model.analysis.result.ResultObject import ResultObject
from androlyze.model.android.apk.Apk import Apk
from androlyze.model.android.apk.EAndroApk import EAndroApk
from androlyze.model.android.apk.FastApk import FastApk
from androlyze.util import Util

'''
Holds function that are used to analyze the apks etc.
'''

def open_apk(apk_or_path = None, apk = None, raw = False, path = None):
    '''
    Open apk and set meta information from `apk`

    Parameters
    ----------
    apk_or_path : str, optional (default is None).
        Path to apk.
    apk : Apk, optional (default is None)
        If given, take the meta infos from `apk`.
        So we don't need to recompute the hash.
        At least if `apk_or_path`.

    raw : bool, optional (default is False)
        If specified, use `apk` as raw .apk data.
    path : str, optional (default is None)
        Can be used for `raw` to set the path of the `EAndroApk`.
        If not given, won't be set.

    Returns
    -------
    EAndroApk
    None
        If apk could not be opened.
    '''

    apk_descr = str(apk_or_path)
    if raw:
        apk_descr = "raw data"

    try:
        eandro_apk = None
        if not raw:
            eandro_apk = EAndroApk(apk_or_path)

        else:
            eandro_apk = EAndroApk(apk_or_path, raw = True)
            eandro_apk.path = path

        if apk is not None:
            # we don't want to lose meta infos
            # use the hash from db so we don't need to recompute
            eandro_apk.set_meta(apk)

        return eandro_apk
    except BadZipfile as e:
        log.warn("Apk %s is not a valid zip file!" % apk_descr)
    except (struct.error, IOError) as e:
        log.warn(CouldNotOpenApk(apk_descr, e))
    except Exception as e:
        log.exception(e)

def analyze_dex(filepath_or_raw, needs_dalvik_vm_format=True, needs_vm_analysis=True, needs_gvm_analysis=True,
                 needs_xref=True, needs_dref=True, raw=False, decompiler="dad"):
    '''
    Open the classes.dex file `needs_dalvik_vm_format`
    and set up an analyzer for it `needs_vm_analysis`.

    Parameters
    ----------
    filepath_or_raw : path to file or raw data
         Set raw to True if `filepath_or_raw` is raw data.
    needs_dalvik_vm_format : bool, optional (default is True)
    needs_vm_analysis : bool, optional (default is True)
    needs_gvm_analysis : bool, optional (default is True)
    needs_xref : bool, optional (default is True)
    needs_dref : bool, optional (default is True)
    raw : bool, optional (default is False)
    decompiler : str, optional (default is "dad")

    Returns
    -------
    tuple<DalvikVMFormat, VMAnalysis, GVMAnalysis>

    Raises
    ------
    DexError
        If an error occurred while creating the analysis objects.
    '''

    dalvik_vm_format, vm_analysis, gvm_analysis = None, None, None
    # every requirement implies the need for the `dalvik_vm_format`
    needs_dalvik_vm_format = any((needs_dalvik_vm_format, needs_vm_analysis, needs_gvm_analysis, needs_xref, needs_dref))
    cross_ref = any((needs_xref, needs_dref))

    try:
        if needs_dalvik_vm_format:
            if raw == False:
                with open(filepath_or_raw, "rb") as f:
                    dalvik_vm_format = DalvikVMFormat(f.read())
            else:
                dalvik_vm_format = DalvikVMFormat(filepath_or_raw)

            if needs_vm_analysis or cross_ref or needs_gvm_analysis:
                vm_analysis = uVMAnalysis(dalvik_vm_format)
                dalvik_vm_format.set_vmanalysis(vm_analysis)

            if needs_gvm_analysis or cross_ref:
                gvm_analysis = GVMAnalysis(vm_analysis, None)
                dalvik_vm_format.set_gvmanalysis(gvm_analysis)

            if dalvik_vm_format:
                RunDecompiler(dalvik_vm_format, vm_analysis, decompiler)

            # create references, gvm_analysis needed!
            # we optimize through not exporting the references into the python objects
            if needs_xref:
                dalvik_vm_format.create_xref(python_export = False)
            if needs_dref:
                dalvik_vm_format.create_dref(python_export = False)

    except Exception as e:
        # androguard caused error -> propagate as DexError
        raise DexError(caused_by = e), None, sys.exc_info()[2]

    return dalvik_vm_format, vm_analysis, gvm_analysis

def store_script_res(storage, script, apk):
    ''' Store script results to disk and result database.

    Apk's which haven't been imported, won't get imported into the database!
    But of course the results will be stored.

    Parameters
    ----------
    storage : RedundantStorage
    script : AndroScript
    apk : Apk

    Raises
    ------
    StorageException

    Returns
    -------
    See :py:method:`.RedundantStorage.store_result_for_apk`
    '''
    storage.create_entry_for_apk(apk, tag=apk.tag,
                                # we don't want to import the apk into the import db
                                # also wouln't work with sqlite (access from different thread)
                                no_db_import = True)
    return storage.store_result_for_apk(apk, script)

def analyze_apk(eandro_apk, scripts, min_script_needs, propagate_error = False, reset_scripts = True):
    ''' Analyze the `eandro_apk` with the given `scripts` assuming each `AndroScript`
    neads at least `min_script_needs`.

    Be sure that you reseted the `scripts`!

    Parameters
    ----------
    eandro_apk : EAndroApk
        The apk.
    scripts : iterable<AndroScript>
        The scripts to use for the analysis.
    min_script_needs : tuple<bool>
        See :py:meth:ScriptUtil.get_maximal_script_options`
    propagate_error : bool, optional (default is False)
        If true propagate errors.
    reset_scripts : bool, optional (default is True)
        If given, reset the `AndroScript` before analyzing.

    Returns
    -------
    list<FastApk, list<AndroScript>>
        Uses `FastApk` to only store the meta information, not the apk data!
    None
        If error happened.
    '''
    from androlyze.analyze.exception import AndroScriptError

    try:
        # reset scripts
        if reset_scripts:
            for s in scripts:
                s.reset()

        if eandro_apk is not None:
            fastapk = None
            # analyze classes.dex with script requirements and get time
            args = [eandro_apk.get_dex()] + list(min_script_needs)

            time_s, analysis_objs = Util.timeit(analyze_dex, *args, raw = True)

            script_results = []
            for s in scripts:
                try:
                    result_obj = s.analyze(eandro_apk, *analysis_objs)

                    # we only need the meta infos of the apk
                    if eandro_apk is not None:
                        fastapk = FastApk.load_from_eandroapk(eandro_apk)

                    # set androguard analysis time if script wants stats
                    s.add_apk_androguard_analyze_time(time_s)

                    # link to apk
                    if isinstance(result_obj, ResultObject):
                        result_obj.set_apk(fastapk)

                    script_results.append(s)
                except Exception as e:
                    if propagate_error:
                        raise
                    else:
                        log.exception(AndroScriptError(s, e))

            if fastapk is not None:
                # use fastapk to only store the meta information, not the apk data!
                return [fastapk, script_results]

    # interrupt analysis if analysis objects could not be created!
    except DexError as e:
        log.exception(e)

def analyze_apk_ana_objs(ana_objs, time_s, eandro_apk, scripts, propagate_error = False, reset_scripts = True):
    ''' Analyze the `eandro_apk` with the given `scripts` assuming each `AndroScript`
    neads at least `min_script_needs`.

    Be sure that you reseted the `scripts`!

    Parameters
    ----------
    eandro_apk : EAndroApk
        The apk.
    scripts : iterable<AndroScript>
        The scripts to use for the analysis.
    propagate_error : bool, optional (default is False)
        If true propagate errors.
    reset_scripts : bool, optional (default is True)
        If given, reset the `AndroScript` before analyzing.

    Returns
    -------
    list<FastApk, list<AndroScript>>
        Uses `FastApk` to only store the meta information, not the apk data!
    None
        If error happened.
    '''
    from androlyze.analyze.exception import AndroScriptError

    try:
        # reset scripts
        if reset_scripts:
            for s in scripts:
                s.reset()

        if eandro_apk is not None:
            fastapk = None

            script_results = []
            for s in scripts:
                try:
                    result_obj = s.analyze(eandro_apk, *ana_objs)

                    # we only need the meta infos of the apk
                    if eandro_apk is not None:
                        fastapk = FastApk.load_from_eandroapk(eandro_apk)

                    # set androguard analysis time if script wants stats
                    s.add_apk_androguard_analyze_time(time_s)

                    # link to apk
                    if isinstance(result_obj, ResultObject):
                        result_obj.set_apk(fastapk)

                    script_results.append(s)
                except Exception as e:
                    if propagate_error:
                        raise
                    else:
                        log.exception(AndroScriptError(s, e))

            if fastapk is not None:
                # use fastapk to only store the meta information, not the apk data!
                return [fastapk, script_results]

    # interrupt analysis if analysis objects could not be created!
    except DexError as e:
        log.exception(e)

############################################################
#---Apk generators
############################################################

def apk_gen(apks_or_paths):
    ''' Helper function that checks every element of `apks_or_paths` if its a path
    or already an `Apk`.

    Parameters
    ----------
    apks_or_paths: list<str> or list<Apk>, optional (default is [])
        List of `Apk` or paths to the apks which shall be analyzed with the given scripts
        If you analyze from paths the `import_date` is not set!

    Returns
    -------
    generator<tuple<str, Apk, bool>>
        Path to .apk, instance of `Apk`, bool what determines if current element of apks_or_paths is an `Apk`
    '''

    for apk_or_path in apks_or_paths:
        # is path or `Apk`
        apk_path = None
        _apk = None
        is_apk = isinstance(apk_or_path, Apk)
        if is_apk:
            apk = apk_or_path
            apk_path = apk.path
            _apk = apk_or_path
        else:
            apk_path = apk_or_path

        yield apk_path, _apk, is_apk

def apk_id_or_raw_data_gen(apk_gen, force_raw_data = False):
    ''' Generator over the .apk files if only path given (or `force_raw_data`).
    Otherwise generator over the apk ids.

    Errors will be logged!.

    Parameters
    ----------
    apk_gen : iterable<tuple<str, Apk, bool>>
        See :py:method:`.AnalyzeUtil.apk_gen`
    force_raw_data : bool, optional (default is False)
        If true, force to yield zipfile rather than hash.

    Returns
    -------
    generator<tuple<object, bool>>
        Raw zip file or id.
        Second component of tuples indicates that the generator is other the id's
        rather than over the zip files.
        Last is an `Apk` object.
    '''
    for apk_path, _apk, is_apk in apk_gen:
        if is_apk and not force_raw_data:
            yield _apk.hash, True, _apk
        else:
            try:
                with open(apk_path, mode = "rb") as f:
                    apk_zipfile = f.read()
                    yield apk_zipfile, False, _apk
            except IOError as e:
                log.warn(e)

def apk_zipfile_gen(apk_gen):
    ''' Generator over the .apk files (raw data). Errors will be logged!.

    Parameters
    ----------
    apk_gen : iterable<tuple<str, Apk, bool>>
        See :py:method:`.AnalyzeUtil.apk_gen`
    '''
    for apk_path, _apk, _ in apk_gen:
        if isinstance(apk_path, (str, unicode)):
            try:
                with open(apk_path, mode = "rb") as f:
                    apk_zipfile = f.read()
                    yield apk_zipfile
            except IOError as e:
                log.warn(e)

def eandro_apk_gen(apk_gen):
    ''' Generator over `EAndroApk`.

    Parameters
    ----------
    apk_gen : iterable<tuple<str, Apk, bool>>
        See :py:method:`.AnalyzeUtil.apk_gen`
    '''
    for apk_path, _apk, _ in apk_gen:
        eandro_apk = open_apk(apk_or_path=apk_path, apk = _apk)
        if eandro_apk is not None:
            yield eandro_apk

############################################################
#---Progress
############################################################

def show_n_inc_progress(total_cnt, tasks_per_chunk = 1):
    '''
    Infinite generator over the cnt of analyzed apks.
    Also shows progress and time elapsed on run.
    Call it once before the first result is available (show 0 progress).
    Otherwise count will be wrong!
    If the progress is 1.0, the progress conut will not be increased
    any further and the `total_cnt` will be returned.

    Parameters
    ----------
    total_cnt : int
    tasks_per_chunk : int, optional (default is 1)
        Number of subtasks a task (chunk) contains.

    Returns
    ----------
    int
        Number of analyzed apks
    '''
    start = time()

    def print_progess(cnt_analyzed):
        progress_str = Util.format_progress(cnt_analyzed * tasks_per_chunk, total_cnt)
        time_elapsed = timedelta(seconds=round(time() - start))
        progress_str = '%s, Time elapsed: %s' % (progress_str, time_elapsed)
        Util.print_dyn_progress(progress_str)

    for cnt_analyzed in chain(xrange(0, total_cnt), repeat(total_cnt)):
        print_progess(cnt_analyzed)
        yield min(cnt_analyzed * tasks_per_chunk, total_cnt)
