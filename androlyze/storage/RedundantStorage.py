
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from datetime import datetime

from androlyze.log.Log import log
from androlyze.storage.FileSysStorage import FileSysStorage
from androlyze.storage.ImportStorageInterface import ImportStorageInterface
from androlyze.storage.apk.ApkCopyInterface import ApkCopyInterface
from androlyze.storage.exception import StorageException
from androlyze.storage.importdb.ImportDatabaseStorage import ImportDatabaseStorage
from androlyze.storage.importdb.ImportQueryInterface import ImportQueryInterface
from androlyze.storage.resultdb.ResultsStorageInterface import ResultStorageInterface
from androlyze.util.Nil import nil


class  RedundantStorage(object, ImportStorageInterface, ImportQueryInterface, ResultStorageInterface, ApkCopyInterface):
    '''
    The store is redundant in the sense that it stores the results in the file system as well as in the database.
    But the preferred choice is always database over file system.
    The file system is only a more convenient way to explore the results via command line.

    The needed objects for the import db, file system and result db access will be created on demand!
    '''

    def __init__(self,
                 # import db stuff
                import_db_name,
                # file system stuff
                store_root_dir = None,
                # result db stuff
                result_db_name = None, result_db_addr = None, result_db_port = None,
                # auth
                result_db_username = None, result_db_passwd = None,
                # result db ssl stuff
                result_db_use_ssl = False, ssl_ca_cert = None,
                
                # set an apk storage
                distributed_apk_storage_factory = None
                ):
        '''
        Parameters
        ----------
        import_db_name : str
            Name of the database to use.
        store_root_dir: str, optional (default is None)
            Holds the path under which results will be stored.
            If no path is given, nothing will be stored in the file system at all.
        result_db_name : str, optional (default is "res")
            The name of the database to use.
            Will be created if not already existing.
        result_db_addr : str, optional (default is '127.0.0.1')
            Address of mongodb database server.
        result_db_port : int, optional (default is 27017)
            Port of mongodb database server.
        result_db_username : str, optional (default is None)
            No authentication at all.
        result_db_passwd : str, optional (default is None)
            No authentication at all.
        result_db_use_ssl : bool, optional (default is False)
            Use ssl for the connection.
        ssl_ca_cert : str, optional (default is None)
            The CA certificate.
            
        distributed_apk_storage_factory : function, optional (default is None)
            A function returning an object implementing the `ApkCopyInterface`.
            Use the function to create the storage only on demand.  
        '''
        self.__apk_distributed_storage = None
        
        # store all variables we need for creation of the storages
        # so that they can be created on demand
        self.__import_db_name = import_db_name
        self.__store_root_dir = store_root_dir
        self.__result_db_name = result_db_name
        self.__result_db_addr = result_db_addr
        self.__result_db_port = result_db_port
        self.__result_db_use_ssl = result_db_use_ssl
        self.__result_db_ca_cert = ssl_ca_cert
        self.__apk_storage_factory = distributed_apk_storage_factory

        # auth
        # store credentials for lazy creating of database
        # but dont forget it do delete after db creation!
        self.__username = result_db_username
        self.__passwd = result_db_passwd

        # create them on demand via the getters
        self.__import_db_storage = None
        self.__fs_storage = None
        self.__result_db_storage = None
        self.__apk_storage = None

        if self.fs_storage_disabled():
            log.info('File system result writing disabled!')

    def get_apk_distributed_storage(self):
        
        # create on demand
        if self.__apk_distributed_storage is None:
            self.__apk_distributed_storage = self.__apk_storage_factory()
        
        return self.__apk_distributed_storage

    def set_apk_distributed_storage(self, value):
        self.__apk_distributed_storage = value

    def del_apk_distributed_storage(self):
        del self.__apk_distributed_storage

    def get_result_db_ca_cert(self):
        return self.__result_db_ca_cert

    def get_result_db_use_ssl(self):
        return self.__result_db_use_ssl

    def get_result_db_name(self):
        return self.__result_db_name

    def get_result_db_addr(self):
        return self.__result_db_addr

    def get_result_db_port(self):
        return self.__result_db_port

    def get_result_db_storage(self):
        ''' Create `ResultDatabaseStorage` on demand '''
        from androlyze.storage.resultdb.ResultDatabaseStorage import ResultDatabaseStorage

        if self.__result_db_storage is None:
            self.__result_db_storage = ResultDatabaseStorage(self.result_db_name, self.result_db_addr, self.result_db_port,
                                                             # auth
                                                             username = self.__username, passwd = self.__passwd,
                                                             # security
                                                             use_ssl=self.result_db_use_ssl, ssl_ca_certs=self.result_db_ca_cert)
            # remove credentials from memory and scope!
            self.__del_credentials()

        return self.__result_db_storage

    def __del_credentials(self):
        ''' Delete credentials '''
        self.__username = None
        self.__passwd = None

        del self.__username
        del self.__passwd

    def set_result_db_storage(self, value):
        self.__result_db_storage = value

    def del_result_db_storage(self):
        del self.__result_db_storage

    def get_import_db_storage(self):
        ''' Create `ImportDatabaseStorage` on demand '''
        if self.__import_db_storage is None:
            self.__import_db_storage = ImportDatabaseStorage(self.__import_db_name)

        return self.__import_db_storage

    def get_fs_storage(self):
        ''' Create `FileSysStorage` on demand.

        If file sys result writing is disabled,
        return nil-like object that ignores all method calls and attribute lookups

        Returns
        -------
        FileSysStorage
            If result writing enabled.
        nil
            Otherwise.
        '''
        if self.__fs_storage is None:
            # disable storage to disk by returning an object that ignores all function calls and attribute lookups
            if self.fs_storage_disabled():
                return nil

            # otherwise return fs storage object
            # and create it if not already
            self.__fs_storage = FileSysStorage(self.__store_root_dir)

        return self.__fs_storage

    def set_import_db_storage(self, value):
        self.__import_db_storage = value

    def set_fs_storage(self, value):
        self.__fs_storage = value

    def del_import_db_storage(self):
        del self.__import_db_storage

    def del_fs_storage(self):
        del self.__fs_storage

    import_db_storage = property(get_import_db_storage, set_import_db_storage, del_import_db_storage, "ImportDatabaseStorage: import database storage")
    fs_storage = property(get_fs_storage, set_fs_storage, del_fs_storage, "FileSysStorage or nil: file system storage")
    result_db_storage = property(get_result_db_storage, set_result_db_storage, del_result_db_storage, "ResultDatabaseStorage : result database storage")
    apk_distributed_storage = property(get_apk_distributed_storage, set_apk_distributed_storage, del_apk_distributed_storage, "ApkCopyInterface : Distributed APK storage")
    
    result_db_name = property(get_result_db_name, None, None, 'str,: The name of the database to use. Will be created if not already existing.')
    result_db_addr = property(get_result_db_addr, None, None, "str : Address of mongodb database server.")
    result_db_port = property(get_result_db_port, None, None, "int : Port of mongodb database server.")
    result_db_use_ssl = property(get_result_db_use_ssl, None, None, " bool, optional (default is False) : Use ssl for the connection.")
    result_db_ca_cert = property(get_result_db_ca_cert, None, None, "str, optional (default is None) : The CA certificate")

    def create_or_open_sub_storages(self):
        ''' Create the `FileSysStorage` as well as the `ResultDatabaseStorage`.
        They are created and opened lazy on demand.
        This this method you force it to be created!

        Raises
        ------
        DatabaseOpenError
        '''
        self.result_db_storage
        self.fs_storage

    def fs_storage_disabled(self):
        ''' Check if the result writing to disk is disabled '''
        return self.__store_root_dir is None

    ############################################################
    #---ImportStorageInterface
    ############################################################

    def create_entry_for_apk(self, apk, update = False, tag = None, **kwargs):
        ''' Create entry in file system as well as in database.
        Will set the `import_date` of the `apk` if not already imported.
        Also sets the `tag`.

        Other Parameters
        ----------------
        no_db_import : bool, optional (default is False)
            If true, don't import into database.
            Just create file sys entry.

        See documentation of `ImportStorageInterface.create_entry_for_apk`.
        '''
        no_db_import = kwargs.get('no_db_import', False)

        already_in_storage = self.contains(apk) if not no_db_import else False

        def set_apk_meta(apk):
            apk.import_date = datetime.utcnow()
            apk.tag = tag

        if (update or not already_in_storage) and not no_db_import:
            set_apk_meta(apk)
            # create entry or update
            self.import_db_storage.create_entry_for_apk(apk, update, tag)
        # no import means cannot be in db -> set meta infos for apk
        elif no_db_import:
            set_apk_meta(apk)

        # res structure may be deleted or not present any more
        self.fs_storage.create_entry_for_apk(apk, update, tag)

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
        StorageException
        '''
        # first delete from fs if `delete_apk`
        # otherwise won't be in db anymore, which is needed to get the path
        self.fs_storage.delete_entry_for_apk(apk, delete_apk)
        self.import_db_storage.delete_entry_for_apk(apk, delete_apk)

    def contains(self, apk):
        ''' Check if the `apk` has been imported yet.
        Query database due to performance.

        Parameters
        ----------
        apk: Apk

        Returns
        -------
        bool
        '''
        return self.import_db_storage.contains(apk)

    ############################################################
    # ImportQueryInterface                                     #
    # For documentation see the docstrings                     #
    # of ImportQueryInterface.                                 #
    # All methods are redirected to the import database        #
    ############################################################

    def get_imported_apks(self, hashes = None, package_names = None, tags = None, **kwargs):
        return self.import_db_storage.get_imported_apks(hashes, package_names, tags, **kwargs)

    def get_versions(self, hashes = None, package_names = None, tags = None):
        return self.import_db_storage.get_versions(hashes, package_names, tags)

    def get_apk_hashes(self, package_names = None, tags = None):
        return self.import_db_storage.get_apk_hashes(package_names, tags)

    def get_apk_package_names(self, hashes = None, tags = None):
        return self.import_db_storage.get_apk_package_names(hashes, tags)

    def get_apk_paths(self, hashes = None, package_names = None, tags = None):
        return self.import_db_storage.get_apk_paths(hashes, package_names, tags)

    ############################################################
    #---ResultStorageInterface
    ############################################################

    def get_results(self, *args, **kwargs):
        ''' See doc of :py:meth:`.ResultDatabaseStorage.get_results` '''
        return self.result_db_storage.get_results(*args, **kwargs)

    def get_results_for_ids(self, *args, **kwargs):
        ''' See :py:method:`.ResultStorageInterface.get_results_for_ids` '''
        return self.result_db_storage.get_results_for_ids(*args, **kwargs)

    def store_result_for_apk(self, apk, script):
        '''
        Store the result for the `apk` in the file system as well as in the database.

        If a custom result object is used in `script` and it's not a `ResultObject`,
        str(custom res object) will be used for storage.

        Does also some checks on the script!

        Parameters
        ----------
        apk: Apk
        script: AndroScript

        Raises
        ------
        StorageException

        Returns
        -------
        See :py:method:`.ResultDatabaseStorage.store_result_for_apk`
        '''
        if (script.uses_custom_result_object() or script.is_big_res()) and script.cres is None:
            raise StorageException("Data cannot be stored for: %s, %s! Your custom result object is None!" % (apk.short_description(), script.name))

        # above ensures script.cres is not None!
        res = self.result_db_storage.store_result_for_apk(apk, script)
        self.fs_storage.store_result_for_apk(apk, script)
        return res

    def delete_results(self, *args, **kwargs):
        ''' See doc of :py:meth:`.ResultDatabaseStorage.delete_results` '''
        return self.result_db_storage.delete_results(*args, **kwargs)

    def erase_whole_db(self):
        ''' See doc of :py:meth:`.ResultDatabaseStorage.erase_whole_db` '''
        self.result_db_storage.erase_whole_db()

    ############################################################
    #---ApkCopyInterface
    ############################################################

    def copy_apk(self, apk, file_like_obj, copy2fs = False, copy2db = False, **kwargs):
        ''' See doc of :py:meth:`.ApkCopyInterface.copy_apk`.

        Returns both return values from :py:meth:`.ResultDatabaseStorage.copy_apk` as well as
        :py:meth:`.FileSysStorage.copy_apk`.

        Returns
        -------
        list<str>
        '''
        res = [None, None]
        if copy2db:
            res[0] = self.apk_distributed_storage.copy_apk(apk, file_like_obj, **kwargs)
        if copy2fs:
            res[1] = self.fs_storage.copy_apk(apk, file_like_obj, **kwargs)
        return res

    def get_apk(self, _hash, *kwargs):
        ''' See doc of :py:meth:`.ApkCopyInterface.copy_apk`. '''
        return self.apk_distributed_storage.get_apk(_hash, **kwargs)

    ############################################################
    #---MongoDB Syncing
    ############################################################

    def fetch_results_from_mongodb(self, *args, **kwargs):
        ''' See doc of :py:meth:`.FileSysStorage.fetch_results_from_mongodb` '''
        self.fs_storage.fetch_results_from_mongodb(self.result_db_storage, *args, **kwargs)

