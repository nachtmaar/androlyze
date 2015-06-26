
# encoding: utf-8

import imp
from itertools import repeat
from multiprocessing import Value, RLock, cpu_count
from multiprocessing.process import Process
import os
import sys

from androlyze import settings
from androlyze.loader.exception import ApkImportError
from androlyze.log.Log import clilog, log
from androlyze.model.analysis.result import StaticResultKeys
from androlyze.model.script import ScriptUtil
from androlyze.settings import SECTION_ANDROGUARD, KEY_ANDROGUARD_PATH, \
    CONFIG_PATH, DEFAULTS_PATH
from androlyze.settings.Settings import Settings
from androlyze.storage import Util
from androlyze.storage.exception import StorageException
from androlyze.storage.resultdb import MongoUtil
from androlyze.util import Util
from androlyze.Constants import *

__all__ = []
__author__ = u"Nils Tobias Schmidt, Lars Baumgärtner"
__copyright__ = PROJECT_COPYRIGHT
__license__ = PROJECT_LICENSE
__version__ = PROJECT_VERSION
__email__ = "{schmidt89,lbaumgaertner}@informatik.uni-marburg.de"

try:
    # load androguard
    Util.set_androguard_path(settings.singleton)
    # import namespace of androguards androlyze.py module
    imp.load_source("androlyze", "%s/androlyze.py" % settings.singleton[(SECTION_ANDROGUARD, KEY_ANDROGUARD_PATH)])
    from androlyze import *
except Exception as e:
    log.error(e)

############################################################
#---Import
############################################################

def action_import_apks(storage, apk_paths,
                       copy_apk = False, copy_to_mongodb = False,
                       update = False, tag = None,
                       # shared memory
                       cnt_imported_apks = None, total_apk_count = None, import_finished = None,
                       # concurrent settings
                       concurrency = None
                       ):

    ''' Import the apks from the `apk_paths` and create the file system structure
    where the results will be kept, specified by `storage`.

    Parameters
    ----------
    storage : RedundantStorage
        The store to use.
    apk_paths : iterable<str>
        The apk files and/or directories.
    copy_apk : bool
        Import the apk file to the `import_dir` (copy it).
    copy_to_mongodb : bool, optional (default is False)
        Also import into MongoDB. Useful for the distributed analysis.
    update : bool
        Update apks that have already been imported.
    tag : str, optional (default is None)
        Some tag
    cnt_imported_apks : multiprocessing.Value<int>, optional (default is None)
        If given, use for progress updating.
    total_apk_count : multiprocessing.Value<int>, optional (default is None)
        If given, use for total count of apks.
    import_finished : multiprocessing.Value<byte>, optional (default is None)
        If given, use to signal that import has been completed.
    concurrency : int, optional (default is number of cpus)
        Number of processes to use for the import.
    '''
    from androlyze.loader.ApkImporter import ApkImporter

    # get single paths to apks so we get the correct total count of apks
    clilog.info("looking for apks in given paths ... ")
    apk_paths = ApkImporter.get_apks_from_list_or_dir(apk_paths)

    if total_apk_count is not None:
        # may be time consuming for recursive lookup
        apk_paths, total_apk_count.value = Util.count_iterable_n_clone(apk_paths)

    # create count if not given
    if cnt_imported_apks is None:
        cnt_imported_apks = Value('i', 0, lock = RLock())

    # set concurrency
    if concurrency is None:
        concurrency = cpu_count()
    log.warn("Using %d processes", concurrency)

    clilog.info("Storage dir is %s" % storage.fs_storage.store_root_dir)
    if copy_apk:
        clilog.info("Copying APKs to %s ..." % storage.fs_storage.store_root_dir)

    def import_apks(apk_paths):
        apk_importer = ApkImporter(apk_paths, storage)
        for apk in apk_importer.import_apks(copy_apk = copy_apk, copy_to_mongodb = copy_to_mongodb,
                                                update = update, tag = tag):

            clilog.info("imported %s", apk.short_description())

            # use shared memory counter if given
            if cnt_imported_apks is not None:
                with cnt_imported_apks.get_lock():
                    cnt_imported_apks.value += 1

    pool = []


    # don't convert generator to list if only 1 process wanted
    apk_paths = [apk_paths] if concurrency == 1 else Util.split_n_uniform_distri(list(apk_paths), concurrency)

    # start parallel import
    # multiprocessing's pool causes pickle errors
    for i in range(concurrency):
        p = Process(target = import_apks, args = (apk_paths[i], ))
        log.debug("starting process %s", p)
        pool.append(p)
        p.start()

    for it in pool:
        log.debug("joined on process %s", p)
        it.join()

    apks_imported = cnt_imported_apks.value != 0
    # show some message that no APK has been imported
    if not apks_imported:
        log.warn("No .apk file has been imported! This means no .apk file has been found or they already have been imported.")
    else:
        clilog.info("done")

    # because not all apks may be importable, we cannot use we count for signal that the import is done
    if import_finished is not None:
        import_finished.value = 1

    clilog.info("Imported %d apks", cnt_imported_apks.value)

############################################################
#---Query
############################################################

    ############################################################
    #---  Query commands
    ############################################################

# query subcommands
COMMAND_QUERY_APKS = "apks"
COMMAND_QUERY_HASHES = "hashes"
COMMAND_QUERY_PACKAGE_NAMES = "package-names"
COMMAND_QUERY_PATHS = "paths"
COMMAND_QUERY_INFOS_ALL = "infos-all"
COMMAND_QUERY_INFOS = "infos"
COMMAND_QUERY_VERSIONS = "versions"
QUERY_COMMANDS = (COMMAND_QUERY_HASHES, COMMAND_QUERY_PACKAGE_NAMES,
     COMMAND_QUERY_INFOS_ALL, COMMAND_QUERY_INFOS,
     COMMAND_QUERY_VERSIONS, COMMAND_QUERY_APKS, COMMAND_QUERY_PATHS)

# TODO: ADD CHECKS FOR OTHER VALUES!
def action_query_result_db(storage, checks = {}, **kwargs):
    '''
    Get results from the database.

    Parameters
    ----------
    storage : ResultsStorageInterface
        The store to use.
    checks : dict, optional (default is {})
        Dictionary describing the checks to perform on some values.
        Will be passed to :py:method:`.MongoUtil.build_checks_filter` (as keyword arguments)
        checks_non_empty_list : iterable<str>, optional (default is ())
            Check the keys against a non empty list.
        checks_empty_list : iterable<str>, optional (default is ())
            Check the keys against an empty list.
        checks_true : iterable<str>, optional (default is ())
            Check if the values of the given keys are true.
        checks_false : iterable<str>, optional (default is ())
            Check if the values of the given keys are false.
        checks_not_null : iterable<str>, optional (default is ())
            Check if the values of the given keys are null (python None).
        checks_null : iterable<str>, optional (default is ())
            Check if the values of the given keys are not null (python None).
        conjunction : str, optional (default is 'or')
            Choose between 'or' and 'and'.
            Specifies how to to link the checks together.

    Other Parameters
    ----------------
    include_fields : list<str>, optional (default is [])
        List of fields to include in the result.
        Mutually exclusive with `exclude_fields`.
    exclude_fields : list<str>, optional (default is [])
        List of fields to exclude from the result.
        Mutually exclusive with `include_fields`.

    where : dict, optional (default is {})
        A filter.
    remove_id_field : bool, optional (default is True)
        Will remove the `_id` field by default.

    distinct_key : str, optional (default is None)
        If given, list the distinct values for the `distinct_key.
    list_ran_scripts: bool, optional (default is False)
        List all scripts that have been run on the given selection.
        Normally you want to supply the `package_name`.
        Overrides `distinct_key`.

    sort : bool, optional (default is True)
        If true sort by analysis date.
    latest : bool, optional (default is False)
        Get the result of the latest script run.
        Will only return one result.
    n : int, optional (default is None)
        Number of results to return.
        None means no limit.

    non_document : bool, optional (default is False)
        Get custom data from mongodb's gridfs.
    non_document_raw : bool, optional (default is False)
        Get the raw data from the database. Otherwise meta infos will be returned.
        Only interesting if `non_document`.

    package_name : str, optional (default is None)
    apk_hash : str, optional (default is None)
    version_name : str, optional (default is None)
    tag : str, optional (default is None)

    script_hash : str, optional (default is None)
    script_name : str, optional (default is None)
    script_version : str, optional (default is None)

    Notes
    -----
    If any of the other parameters is None it won't be used for filtering.

    Returns
    -------
    gridfs.grid_file.GridOutCursor
        If non_document and non_document_raw.
    pymongo.cursor.Cursor
        Otherwise

    Raises
    ------
    DatabaseLoadException

    Examples
    --------
    >>> import androlyzelab
    ... from androlyze.storage.resultdb.ResultDatabaseStorage import ResultDatabaseStorage
    ... from androlyze.model.script.ScriptUtil import dict2json
    ... storage = ResultDatabaseStorage('127.0.0.1', 27017)
    ... res = androlyze.action_query_result_db(storage, n = 2, script_name = "ChainedApkInfos", include_fields = ["apkinfo.components.activities"])
    ... for r in res:
    ...     # get dict
    ...     # print r
    ...     # get json
    ...     print dict2json(r)
    {
    "apkinfo": {
        "components": {
            "activities": {
                "all": [
                    "cn.wps.impress.test.selfvalidate.lmj.TestServiceActivity",
    ...
    '''
    # build check filter dict if some checks are given which shall be done on some attributes
    if checks:
        checks = MongoUtil.build_checks_filter(**checks)

    # update with checks dict or {}
    if 'where' in kwargs and kwargs['where'] is not None:
        kwargs['where'].update(checks)
    else:
        kwargs['where'] = checks

    non_document = kwargs.get("non_document", False)
    if kwargs.get("list_ran_scripts", False):
        kwargs['distinct_key'] = MongoUtil.get_attr_str(StaticResultKeys.RESOBJ_SCRIPT_META, StaticResultKeys.RESOBJ_SCRIPT_META_NAME, non_document)

    return storage.get_results(**kwargs)

def action_query_import_db(storage, query_cmd, hashes = None, package_names = None, tags = None, **kwargs):
    ''' Returns the result of the query action.

    For additional keyword-arguments see :py:meth:`.ImportStorageInterface.get_imported_apks`.

    Parameters
    ----------
    storage : ImportQueryInterface
        The store to use.
    query_cmd : str
        The query command.
        See variables prefixed with `COMMAND_QUERY_`.
    hashes : iterable<str>, optional (default is None)
    package_names : iterable<str>, optional (default is None)
    tags : iterable<str>, optional (default is None)
    order_by : str, optional (default is None)
        Sort apks by key.

    Returns
    -------
    iterable<Apk>.
        If `query_cmd is` `COMMAND_QUERY_APKS`
    iterable<str>

    Raises
    ------
    ValueError
        If an unknown `query_cmd` has been given
    '''
    if not query_cmd in QUERY_COMMANDS:
        raise ValueError("Unknown query cmd: %s" % query_cmd)

    res = None
    if query_cmd in (COMMAND_QUERY_INFOS, COMMAND_QUERY_INFOS_ALL, COMMAND_QUERY_APKS):
        apks = storage.get_imported_apks(hashes, package_names, tags, **kwargs)
        if query_cmd == COMMAND_QUERY_APKS:
            return apks
        # verbose
        if query_cmd == COMMAND_QUERY_INFOS_ALL:
            res = (apk.detailed_description() for apk in apks)
        # non-verbose
        elif query_cmd == COMMAND_QUERY_INFOS:
            res = (apk.short_description() for apk in apks)

    elif query_cmd == COMMAND_QUERY_PACKAGE_NAMES:
        res = storage.get_apk_package_names(hashes, tags)
    elif query_cmd == COMMAND_QUERY_PATHS:
        res = storage.get_apk_paths(hashes, package_names, tags)

    elif query_cmd in (COMMAND_QUERY_VERSIONS, COMMAND_QUERY_HASHES):
        if query_cmd == COMMAND_QUERY_HASHES:
            res =  storage.get_apk_hashes(package_names, tags)
        elif query_cmd == COMMAND_QUERY_VERSIONS:
            res = storage.get_versions(hashes, package_names, tags)
    return res

############################################################
#---Analyze
############################################################

ANALYZE_MODE_PARALLEL = 'parallel'
ANALYZE_MODE_NON_PARALLEL = 'non-parallel'
ANALYZE_MODE_DISTRIBUTED = 'distributed'

def action_analyze(storage, script_list, apks_or_paths = None,
                   mode = ANALYZE_MODE_PARALLEL, concurrency = None,
                   serialize_apks = True
                   ):
    '''
    Analyze the `apks_or_paths` with the given `script_list`.

    Parameters
    ----------
    storage : RedundantStorage
        The store to use.
    script_list : list<str>
        List of paths to scripts (complete filename with extension).
    apks_or_paths: list<str> or list<Apk>, optional (default is None)
        List of `Apk` or paths to the apks which shall be analyzed with the given scripts
        If you analyze from paths the `import_date` is not set!
    mode : str, optional (default is `ANALYZE_MODE_PARALLEL`)
        Do an parallel analysis by default. Choose between : , , .
    concurrency : int, optional (default is number of cpu cores)
        Number of workers to spawn.
    serialize_apks : bool, optional (default is True)
        If true, serialize .apk .
        Otherwise id (hash) of the apk will be send and fetched by the worker from the result db.
        Be sure to import the apks to the result db first!
    '''
    analyzer = create_analyzer(storage, script_list, apks_or_paths, mode, concurrency, serialize_apks)
    if analyzer is not None:
        return run_analysis(analyzer)

def create_analyzer(storage, script_list, apks_or_paths = None,
                   mode = ANALYZE_MODE_PARALLEL, concurrency = None,
                   serialize_apks = True
                   ):
    '''
    Create the analyzer only.

    Parameters
    ----------
    storage : RedundantStorage
        The store to use.
    script_list : list<str>
        List of paths to scripts (complete filename with extension).
    apks_or_paths: list<str> or list<Apk>, optional (default is None)
        List of `Apk` or paths to the apks which shall be analyzed with the given scripts
        If you analyze from paths the `import_date` is not set!
    mode : str, optional (default is `ANALYZE_MODE_PARALLEL`)
        Do an parallel analysis by default. Choose between : , , .
    concurrency : int, optional (default is number of cpu cores)
        Number of workers to spawn.
    serialize_apks : bool, optional (default is True)
        If true, serialize .apk .
        Otherwise id (hash) of the apk will be send and fetched by the worker from the result db.
        Be sure to import the apks to the result db first!
    '''
    from androlyze.model.script import ScriptUtil
    from androlyze.analyze.exception import AndroScriptError

    try:
        # list<type<AndroScript>>
        androscript_list = ScriptUtil.import_scripts(script_list)
        instantiated_scripts = sorted(ScriptUtil.instantiate_scripts(androscript_list, script_paths = script_list))

        if len(instantiated_scripts) == 0:
            log.warn("No scripts supplied!")
            return

        # get hashes for `AndroScript`s so that we can set the hash directly next time we instantiate the script
        script_hashes = [s.hash for s in instantiated_scripts]
        min_script_needs = ScriptUtil.get_minimum_script_options(instantiated_scripts)

        # log infos about scripts
        clilog.info('Loaded scripts:\n%s', '\n'.join((str(s) for s in instantiated_scripts)))
        log.info(ScriptUtil.androscript_options_descr(instantiated_scripts))

        if apks_or_paths:

            def create_analyzer():

                analyzer = None
                # argument for BaseAnalyzer
                args = storage, androscript_list, script_hashes, min_script_needs, apks_or_paths
                log.info("Mode: %s", mode)

                # normal analyzer
                if mode == ANALYZE_MODE_NON_PARALLEL:
                    from androlyze.analyze.Analyzer import Analyzer
                    analyzer = Analyzer(*args)
                # use parallel analyzer
                elif mode == ANALYZE_MODE_PARALLEL:
                    from androlyze.analyze.parallel.ParallelAnalyzer import ParallelAnalyzer
                    analyzer = ParallelAnalyzer(*args, concurrency = concurrency)
                # use distributed one
                elif mode == ANALYZE_MODE_DISTRIBUTED:
                    from androlyze.analyze.distributed.DistributedAnalyzer import DistributedAnalyzer
                    analyzer = DistributedAnalyzer(*args, concurrency = concurrency, serialize_apks = serialize_apks)

                return analyzer

            return create_analyzer()

    except ApkImportError as e:
        log.warn(e)
    except IOError as e:
        log.warn(AndroScriptError(e.filename, caused_by = e))
        sys.exit(1)
    except ImportError as e:
        log.exception(e)
    except Exception as e:
        log.exception(e)

def run_analysis(analyzer):
    ''' Run the analysis with the `analyzer`.

    Parameters
    ----------
    analyzer : BaseAnalyzer

    Returns
    -------
    int
        Number of analyzed apks.
    '''
    from androlyze.analyze.exception import AndroScriptError

    try:
        cnt_analyzed_apks = analyzer.analyze()
        if  cnt_analyzed_apks == 0:
            log.warn("No apk file has been analyzed !")
        else:
            log.warn("Analyzed %s apks", cnt_analyzed_apks)

        return cnt_analyzed_apks
    except AndroScriptError as e:
        log.exception(e)

############################################################
#---Delete
############################################################

def action_delete_apks_import(storage, delete_apk = False, hashes = None, package_names = None, tags = None, select_whole_db = False):
    ''' Delete from the import storage (database and/or filesys)

    Parameters
    ----------
    storage : RedundantStorage
        The store to use.
    delete_apk : boolean, optional (default is False)
    hashes : iterable<str>, optional (default is None)
    package_names : iterable<str>, optional (default is None)
    tags : iterable<str>, optional (default is None)
    select_whole_db : boolean, optional (default is False)
        If true, select the whole import database! Be careful!
        This means we do not take `hashes`, `package_names` and `tags` into acccount!

    Raises
    ------
    ValueError
    '''
    try:
        apks = None
        if select_whole_db:
            apks = action_query_import_db(storage, COMMAND_QUERY_APKS, hashes, package_names, tags)
        # If don't delete whole database!!!!!
        elif len(Util.filter_not_none((hashes, package_names, tags))) > 0:
            apks = action_query_import_db(storage, COMMAND_QUERY_APKS, hashes, package_names, tags)
        else:
            raise ValueError('''Neither hashes nor package names nor tags specified!
             If you wan't do use the whole database, set `select_whole_db` to true.
             ''')

        # use list, otherwise we have duplicates due to the generator
        for apk in list(apks):
            if delete_apk:
                clilog.info("Will delete from database and file system: \n%s ", apk.detailed_description())
            else:
                clilog.info("Will delete %s from database: %s ", apk.short_description(), storage.import_db_storage)
            storage.delete_entry_for_apk(apk, delete_apk)
    except StorageException as e:
        log.warn(e)

def action_delete_apks_res(storage,
                           where = None, non_document = False, whole_db = False, **kwargs):
    '''
    Delete some results from the database.

    Parameters
    ----------
    storage : RedundantStorage
        The store to use.
    where : dict, optional (default is {})
            A filter.
    non_document : bool, optional (default is False)
        Remove from gridfs.
    whole_db : bool, optional (default is False)

    Other Parameters
    ----------------
    package_name : str, optional (default is None)
    apk_hash : str, optional (default is None)
    version_name : str, optional (default is None)
    tag : str, optional (default is None)

    script_hash : str, optional (default is None)
    script_name : str, optional (default is None)
    script_version : str, optional (default is None)

    Notes
    -----
    If any of the other parameters is None it won't be used for filtering.
    They may will also overwrite the other ones.

    Returns
    -------
    int
        Number of documents which have been removed.
        If not `whole_db`
    None
    '''
    if whole_db:
        storage.erase_whole_db()
        return None

    return storage.delete_results(where, non_document, **kwargs)

############################################################
#---Sync
############################################################

def action_sync_fs(storage, continue_func = lambda _ : True, wait_for_db = True,
                   # progess
                   synced_entries = None, total_sync_entries = None):
    '''
    Sync file system with result database.

    Parameters
    ----------
    storage : RedundantStorage
        The store to use.
    continue_func : int -> bool, optional (defauls is True)
        This function will be executed before the actual sync starts with the nomber of total items to fetch.
        The function determines via return value if the action shall be done.
    wait_for_db : bool, optional (default is True)
            Wait until data could be fetched from db.
    synced_entries : multiprocessing.Value<int>, optional (default is None)
        If supplied store number of already synces entries.
    total_sync_entries : multiprocessing.Value<int>, optional (default is None)
        If supplied store number of total entries to sync.

    Returns
    -------
    int
        Number of entries to sync/synced.
    '''
    fs_storage = storage.fs_storage
    rds = storage.result_db_storage

    # get id' for non-gridfs
    document_ids = rds.get_ids(non_document = False)
    # get id' for gridfs
    gridfs_ids = rds.get_ids(non_document = True)
    # total number of entries
    total_entries = len(document_ids) + len(gridfs_ids)

    # check if really sync wanted
    if continue_func(total_entries):
        # do sync
        fs_storage.fetch_results_from_mongodb(rds, zip(document_ids, repeat(False)) + zip(gridfs_ids, repeat(True)),
                                              nice_progess = True, wait_for_db = wait_for_db,
                                              synced_entries = synced_entries, total_sync_entries = total_sync_entries)

    return total_entries

