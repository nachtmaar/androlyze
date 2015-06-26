
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from os import makedirs
import os
from os.path import join, exists
import shutil
import sys
from time import sleep

from androlyze.loader.exception import CouldNotOpenApk
from androlyze.log.Log import log, clilog
from androlyze.model.analysis.result.StaticResultKeys import *
from androlyze.model.android.apk.FastApk import FastApk
from androlyze.model.script import ScriptUtil as ScriptUtil
from androlyze.model.script.AndroScript import AndroScript
from androlyze.storage import Util as StorageUtil
from androlyze.storage.ImportStorageInterface import ImportStorageInterface
from androlyze.storage.ResultWritingInterface import ResultWritingInterface
from androlyze.storage.apk.ApkCopyInterface import ApkCopyInterface
from androlyze.storage.exception import FileSysStoreException, \
    FileSysCreateStorageStructureException, FileSysDeleteException, \
    DatabaseLoadException
from androlyze.storage.resultdb import MongoUtil
from pymongo.errors import PyMongoError
from androlyze.util import Util 

class FileSysStorage(object, ImportStorageInterface, ResultWritingInterface, ApkCopyInterface):
    '''
    Manages the file system storage.
    '''

    # directory name where the results will be kept
    APK_RES_DIRNAME = "res"

    # directory name where the apks will be imported to
    APK_IMPORT_DIRNAME = "apk"

    def __init__(self, store_root_dir):
        '''
        Create a file system store that manages the import of apks to the file system as well as storing results of the analysis.

        Parameters
        ----------
        store_root_dir: str
            The root directory under which the results will be stored.
        '''
        # use absolute path
        self.__store_root_dir = os.path.abspath(store_root_dir)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.store_root_dir)

    def get_store_root_dir(self):
        return self.__store_root_dir

    def set_store_root_dir(self, value):
        self.__store_root_dir = value

    def del_store_root_dir(self):
        del self.__store_root_dir

    store_root_dir = property(get_store_root_dir, set_store_root_dir, del_store_root_dir, "str - holds the path under which results will be stored")

    def create_filesys_structure(self, file_path):
        '''
        Create the file system path where the results will be kept for the specified `file_path`

        Parameters
        ----------
        file_path : str
            The path structure to create.

        Raises
        ------
        FileSysCreateStorageStructureException
            If the directories could not be created or the apk file could not be opened.
        '''
        try:
            self._checkn_create_storage_root_paths()
            # check that path does not already exist
            if not exists(file_path):
                makedirs(file_path)
        except (OSError, CouldNotOpenApk) as e:
            raise FileSysCreateStorageStructureException(file_path, self, e), None, sys.exc_info()[2]

    ############################################################
    #---StorageInterface
    ############################################################

    def create_entry_for_apk(self, apk, update = False, tag = None):
        '''
        Create the file system path where the results will be kept for the specified `apk` file.

        Parameters
        ----------
        apk : Apk
        update : bool, optional (default is False)
            Has no effect here.
        tag : str, optional (default is None)
            Has no effect here.

        Raises
        ------
        FileSysCreateStorageStructureException
            If the directories could not be created or the apk file could not be opened.
        '''
        self.create_filesys_structure(self.get_apk_res_path(apk))

    def delete_entry_for_apk(self, apk, delete_apk = False):
        ''' Delete the entry for `apk`.

        Parameters
        ----------
        apk: Apk
        delete_apk : boolean, optional (default is False)
            If true, also delete the .apk file from the file system
            (but only if it is in the storage directory!).

        Raises
        ------
        FileSysDeleteException
        '''
        try:
            # only delete the apk
            if delete_apk and self.is_in_store_dir(apk):
                path = self.get_apk_res_path(apk)

                # delete the apk/package_name/version_name/
                apk_import_path = join(self.get_apk_import_base_path(), apk.package_name, apk.version_name)

                # change dir, to remove only up to this point
                os.chdir(join('..', apk_import_path))
                shutil.rmtree(apk_import_path)

                try:
                    apk_import_path = join(self.get_apk_import_base_path(), apk.package_name)
                    # also try to delete apk/package_name if dir is empty
                    if self._get_cnt_visible_dirs(apk_import_path) == 0:
                        os.chdir(join('..', apk_import_path))
                        shutil.rmtree(apk_import_path)
                # will raise an error if dir not empty -> ignore it
                except OSError:
                    pass
        except (OSError, CouldNotOpenApk) as e:
            raise FileSysDeleteException(path, self, e), None, sys.exc_info()[2]

    ############################################################
    #---ResultWritingInterface
    ############################################################

    def store_result_for_apk(self, apk, script):
        '''
        Store the results in the file system.

        If a custom result object is used in `script` and it's not a `ResultObject`,
        str(custom res object) will be used for writing to disk.

        Parameters
        ----------
        apk: Apk
        script: AndroScript

        Raises
        ------
        FileSysStoreException

        Returns
        -------
        str
            Path to result file.
        '''
        try:
            res_filename = self.get_apk_res_filename(apk, script)
            with open(res_filename, "w") as f:
                log.debug("storing results for %s, %s to %s", apk.short_description(), script, res_filename)
                if not script.uses_custom_result_object():
                    f.write(script.res.write_to_json())
                else:
                    res = self.get_custom_res_obj_representation(script)
                    # log json if custom res obj is `ResultObject
                    if ScriptUtil.is_result_object(res):
                        res = res.write_to_json()
                    f.write(res)
            return res_filename
        except IOError as e:
            raise FileSysStoreException(res_filename, str(apk), self, e)

    ############################################################
    #---ApkCopyInterface
    ############################################################

    def copy_apk(self, apk, file_like_obj, **kwargs):
            '''
            Copy the `apk` to the file system (path specified through `store_root_dir`).

            See also: :py:meth:`.ApkCopyInterface.copy_apk`.

            Parameters
            ----------
            apk: Apk
                Holds meta information needed to create the subdirectory names.
            file_like_obj
                A file-like object which holds the .apk data

            Raises
            ------
            IOError
            FileSysCreateStorageStructureException

            Returns
            -------
            str
                The path were the apk file has been copied
            '''
            apk_file_path = self.get_apk_import_file_name(apk)
            log.debug("copying %s to %s", apk.short_description(), apk_file_path)

            # create path for apk if not existing
            apk_import_path = None
            try:
                apk_import_path = self.get_apk_import_path(apk)
                if not exists(apk_import_path):
                    makedirs(apk_import_path)
            except OSError as e:
                raise FileSysCreateStorageStructureException(apk_import_path, self, e), None, sys.exc_info()[2]

            # copy apk
            with open(apk_file_path, "wb") as apk_copy:
                file_like_obj.seek(0)
                apk_copy.write(file_like_obj.read())

            return apk_file_path

    ############################################################
    #--Custom
    ############################################################

    def get_apk_import_base_path(self):
        ''' Returns the base path where the .apk will be stored '''
        return join(self.store_root_dir, self.APK_IMPORT_DIRNAME)

    def get_apk_res_base_path(self):
        ''' Returns the base path where the results of the `apk` analysis will be kept '''
        return join(self.store_root_dir, self.APK_RES_DIRNAME)

    ############################################################
    #---Apk based path getter functions
    ############################################################

    def get_apk_import_file_name(self, apk):
        '''
        Returns the full path where the .apk will be stored.

        Parameters
        ----------
        apk : Apk

        Returns
        ------
        str
        '''
        return join(self.get_apk_import_base_path(), self.get_apk_sub_path(apk), apk.get_apk_filename_from_manifest())

    def get_apk_res_filename(self, apk, script):
        ''' Return the path for the result filename.

        Parameters
        ----------
        apk : Apk
        script : AndroScript

        Raises
        ------
        CouldNotOpenApk
            If the APK could no be opened
        '''
        apk_sub_path = self.get_apk_sub_path(apk)
        return join(self.get_apk_res_base_path(), apk_sub_path, script.get_file_name())

    def get_apk_res_path(self, apk):
        '''
        Returns the path structure for results of the `apk` analysis.

        Parameters
        ----------
        apk: Apk

        Returns
        -------
        str: path

        Raises
        ------
        CouldNotOpenApk
            If the APK could no be opened
        '''
        return join(self.store_root_dir, self.APK_RES_DIRNAME, self.get_apk_sub_path(apk))

    def get_apk_import_path(self, apk):
        '''
        Returns the path structure for import directory of the `apk`.

        Parameters
        ----------
        apk: Apk

        Returns
        -------
        str: path

        Raises
        ------
        CouldNotOpenApk
            If the APK could no be opened
        '''
        return join(self.store_root_dir, self.APK_IMPORT_DIRNAME, self.get_apk_sub_path(apk))

    def get_apk_sub_path(self, apk):
        '''
        Returns the sub path structure for the `apk`.

        The structure is:
        ...
        |-> package
          |-> version
            |-> sha256

        Parameters
        ----------
        apk: Apk

        Returns
        -------
        str: path

        Raises
        ------
        CouldNotOpenApk
            If the APK could no be opened
        '''
        package = apk.package_name
        version_name = apk.version_name
        # if hash caluclated from file, can raise CouldNotOpenApk
        sha256 = apk.hash
        return StorageUtil.get_apk_path(package, version_name, sha256)

    ############################################################
    #---Non-apk based path getter functions
    ############################################################

    def get_apk_res_path_all_args(self, package_name, version_name, _hash):
        '''
        Returns the path structure for result storage.

        Parameters
        ----------
        package_name : str
            Package name of the apk.
            Unique apk identifier (at least in the store)
        version_name : str
            Version name
        _hash : str
            The hash of the apk.

        Returns
        -------
        str: path
        '''
        return join(self.store_root_dir, self.APK_RES_DIRNAME, StorageUtil.get_apk_path(package_name, version_name, _hash))
    
    ############################################################
    #---Helper functions
    ############################################################

    def _checkn_create_storage_root_paths(self):
        '''
        Check if the structure for the import and analysis results already exists.
        Otherwise create it.

        Raises
        ------

        FileSysCreateStorageStructureException
        '''
        path = None
        # create basic path structure for import and results of the apks

        # apk import structure
        try:
            path = self.get_apk_import_base_path()
            if not exists(path):
                makedirs(path)
        except OSError as e:
            raise FileSysCreateStorageStructureException(path, self, e), None, sys.exc_info()[2]

        # apk result structure
        try:
            path = self.get_apk_res_base_path()
            if not exists(path):
                makedirs(path)
        except OSError as e:
            raise FileSysCreateStorageStructureException(path, self, e), None, sys.exc_info()[2]

    def is_in_store_dir(self, apk):
        ''' Check if the path of the `apk` is in the store dir.

        Parameters
        ----------
        apk : Apk
        '''
        return apk.path.startswith(self.store_root_dir)

    @staticmethod
    def _get_cnt_visible_dirs(root_dir):
        ''' Get the number of directories in `root_dir` minus the ones beginning with "." '''
        cnt = 0
        for subdir in os.listdir(root_dir):
            path = join(root_dir, subdir)

            if os.path.isdir(path) and not subdir.startswith("."):
                cnt +=1
        return cnt
    ############################################################
    #---Custom storage
    ############################################################

    def store_result_dict(self, res_dict):
        '''
        Store the analysis results from the `res_dict`.
        All needed infos for storage will be taken from it.

        Parameters
        ----------
        res_dict : dict
            See `ResultObject.description_dict`
        '''

        fastapk = FastApk.load_from_result_dict(res_dict)
        script = AndroScript.load_from_result_dict(res_dict, fastapk)

        try:
            self.create_entry_for_apk(fastapk, update = True)
            self.store_result_for_apk(fastapk, script)
        except FileSysStoreException as e:
            log.warn(e)

    def store_custom_data(self, package_name, version_name, _hash, file_name, data):
        '''
        Store custom data to the file system (also with the result directory as root)

        Parameters
        ----------
        package_name : str
            Package name of the apk.
            Unique apk identifier (at least in the store)
        version_name : str
            Version name
        _hash : str
            The hash of the apk.
        file_name : str
            File name.
        data : object
            The data what shall be written to disk.
            Will write str(data) to disk.

        Raises
        ------
        FileSysStoreException
        '''
        try:
            # create basic fs structure
            base_path = self.get_apk_res_path_all_args(package_name, version_name, _hash)
            self.create_filesys_structure(base_path)

            file_path = join(base_path, file_name)
            try:
                with open(file_path, "w") as f:
                    f.write(str(data))
            except IOError as e:
                raise FileSysStoreException(file_path, "custom data", self, e)
        except FileSysCreateStorageStructureException as e:
            log.exception(e)

    ############################################################
    #---MongoDB Syncing
    ############################################################

    def fetch_results_from_mongodb(self, rds, results, wait_for_db = True,
                                   # progress
                                   nice_progess = False, synced_entries = None, total_sync_entries = None):
        '''
        Fetch some results from the result database and write them to disk.

        If data cannot be loaded from db, try until it can be.

        Parameters
        ----------
        rds : ResultDatabaseStorage
            The database to query for the results.
        results : list< tuple<id, gridfs (bool)> >
            Define which results shall be fetched.
        wait_for_db : bool, optional (default is True)
            Wait until data could be fetched from db.
        nice_progess : bool, optional (default is False)
            If enabled update show some nice progress bar on the cli.
        synced_entries : multiprocessing.Value<int>, optional (default is None)
            If supplied store number of already synces entries.
        total_sync_entries : multiprocessing.Value<int>, optional (default is None)
            If supplied store number of total entries to sync.

        Raises
        ------
        DatabaseLoadException
            If `wait_for_db` is False and an error occurred.
        '''
        # retry in ... seconds
        DATABASE_RETRY_TIME = 5

        # if true assume both counts are shared memory (Value)
        use_shared_memory = synced_entries is not None and total_sync_entries is not None

        if results is not None:
            results_stored = False
            while not results_stored:
                try:
                    # get ids
                    non_gridfs_ids, gridfs_ids = MongoUtil.split_result_ids(results)

                    # counts
                    cnt_non_gridfs_ids = len(non_gridfs_ids)
                    cnt_gridfs_ids = len(gridfs_ids)

                    if use_shared_memory:
                        total_sync_entries.value = cnt_gridfs_ids + cnt_non_gridfs_ids

                    # gridfs raw data as well as metadata
                    gridfs_entries_raw = []
                    if gridfs_ids:
                        gridfs_entries_raw = rds.get_results_for_ids(gridfs_ids, non_document = True, non_document_raw = True)

                    # regular documents (non gridfs)
                    non_gridfs_entries = []
                    if non_gridfs_ids:
                        non_gridfs_entries = rds.get_results_for_ids(non_gridfs_ids, non_document = False, non_document_raw = True)

                    if not nice_progess:
                        log.debug("fetching %d non-documents (gridfs) ... ", cnt_gridfs_ids)

                    for i, gridfs_entry_raw in enumerate(gridfs_entries_raw, 1):

                        # get our stored metadata (for script and apk)
                        gridfs_entry_meta = gridfs_entry_raw.metadata

                        if not nice_progess:
                            log.debug("getting results for %s", gridfs_entry_meta[RESOBJ_APK_META][RESOBJ_APK_META_PACKAGE_NAME])
                        else:
                            Util.print_dyn_progress(Util.format_progress(i, cnt_gridfs_ids))

                        # use apk to extract data from dict
                        fastapk = FastApk.load_from_result_dict(gridfs_entry_meta)
                        # get filename
                        file_name = gridfs_entry_raw.filename

                        # write results to disk
                        try:
                            self.store_custom_data(fastapk.package_name, fastapk.version_name, fastapk.hash, file_name, gridfs_entry_raw.read())
                        except FileSysStoreException as e:
                            log.exception(e)

                        # update shared memory progress indicitor
                        if use_shared_memory:
                            with synced_entries.get_lock():
                                synced_entries.value += 1

                    if not nice_progess:
                        log.debug("fetching %d documents (non-gridfs) ... ", cnt_non_gridfs_ids)

                    for i, non_gridfs_entry in enumerate(non_gridfs_entries, 1):
                        if not nice_progess:
                            clilog.debug("getting results for %s" % non_gridfs_entry[RESOBJ_APK_META][RESOBJ_APK_META_PACKAGE_NAME])
                        else:
                            Util.print_dyn_progress(Util.format_progress(i, cnt_non_gridfs_ids))

                        # write results to disk
                        self.store_result_dict(non_gridfs_entry)

                        # update shared memory progress indicitor
                        if use_shared_memory:
                            with synced_entries.get_lock():
                                synced_entries.value += 1

                    # if not wait for db wanted stop here
                    results_stored = True or not wait_for_db

                except (DatabaseLoadException, PyMongoError) as e:
                    if not wait_for_db:
                        raise
                    log.warn(e)
                    Util.log_will_retry(DATABASE_RETRY_TIME, exc = e)
                    sleep(DATABASE_RETRY_TIME)
