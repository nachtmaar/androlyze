
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sqlite3
import sys

from androlyze.loader.exception import CouldNotOpenApk
from androlyze.log.Log import log
from androlyze.model.android.apk.FastApk import FastApk
from androlyze.storage.ImportStorageInterface import ImportStorageInterface
from androlyze.storage.importdb.ImportQueryInterface import *
from androlyze.storage.exception import DatabaseStoreException, DatabaseOpenError, \
    DatabaseLoadException, DatabaseDeleteException
from androlyze.storage.importdb.exception import ImportQueryError

class ImportDatabaseStorage(object, ImportStorageInterface, ImportQueryInterface):
    '''
    Database for importing apks based on sqlite3 to have flat file databases which can be passed as arguments to AndroLyzeLab.

    This class implements the `ImportQueryInterface` for providing the information about the imported apks.

    The base error for the database is `DatabaseException` and for retrieving information it's ImportQueryError.

    See `ImportQueryInterface`.
    '''

    CREATE_STMT = ''' CREATE TABLE IF NOT EXISTS %s (
    %s TEXT PRIMARY KEY NOT NULL UNIQUE,
    %s TEXT NOT NULL,
    %s TEXT NOT NULL,
    %s TEXT NOT NULL,
    %s timestamp NOT NULL,
    %s TEXT,
    %s INTEGER DEFAULT 0,
    %s timestamp NOT NULL
    )''' % (TABLE_APK_IMPORT,
                    TABLE_APK_IMPORT_KEY_HASH,
                    TABLE_APK_IMPORT_KEY_PACKAGE_NAME,
                    TABLE_APK_IMPORT_KEY_VERSION_NAME,
                    TABLE_APK_IMPORT_KEY_PATH,
                    TABLE_APK_IMPORT_KEY_IMPORT_DATE,
                    TABLE_APK_IMPORT_KEY_TAG,
                    TABLE_APK_IMPORT_KEY_SIZE_APP_CODE,
                    TABLE_APK_IMPORT_KEY_BUILD_DATE
                    )

    INSERT_STMT = ''' INSERT INTO %s(%s, %s, %s, %s, %s, %s, %s, %s)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''' % (TABLE_APK_IMPORT,
                                      TABLE_APK_IMPORT_KEY_HASH,
                                      TABLE_APK_IMPORT_KEY_PACKAGE_NAME,
                                      TABLE_APK_IMPORT_KEY_VERSION_NAME,
                                      TABLE_APK_IMPORT_KEY_PATH,
                                      TABLE_APK_IMPORT_KEY_IMPORT_DATE,
                                      TABLE_APK_IMPORT_KEY_TAG,
                                      TABLE_APK_IMPORT_KEY_SIZE_APP_CODE,
                                      TABLE_APK_IMPORT_KEY_BUILD_DATE
                                      )

    UPDATE_STMT = ''' UPDATE %s SET %s = ?, %s = ?, %s = ?, %s = ?, %s = ?, %s = ?, %s = ? WHERE %s = ?
         ''' % (TABLE_APK_IMPORT,
              TABLE_APK_IMPORT_KEY_PACKAGE_NAME,
              TABLE_APK_IMPORT_KEY_VERSION_NAME,
              TABLE_APK_IMPORT_KEY_PATH,
              TABLE_APK_IMPORT_KEY_IMPORT_DATE,
              TABLE_APK_IMPORT_KEY_TAG,
              TABLE_APK_IMPORT_KEY_SIZE_APP_CODE,
              TABLE_APK_IMPORT_KEY_BUILD_DATE,
              TABLE_APK_IMPORT_KEY_HASH,
              )

    # statement to add the app_code_size column
    ADD_COLUMN_APP_CODE_SIZE = "ALTER TABLE %s ADD COLUMN %s INTEGER DEFAULT 0" % (TABLE_APK_IMPORT, TABLE_APK_IMPORT_KEY_SIZE_APP_CODE)

    # statement to add the build time column
    ADD_COLUMN_BUILD_DATE = "ALTER TABLE %s ADD COLUMN %s timestamp NOT NULL" % (TABLE_APK_IMPORT, TABLE_APK_IMPORT_KEY_BUILD_DATE)
    
    DELETE_STMT = ' DELETE FROM %s WHERE %s = ?' % (TABLE_APK_IMPORT, TABLE_APK_IMPORT_KEY_HASH)

    # time to wait e.g. for the file lock to disappear
    TIMEOUT = 60

    def __init__(self, import_db_name):
        '''
        Open the database and create the table structure if not already existing.

        Parameters
        ----------
        import_db_name : str
            Name of the database to use.

        Raises
        ------
        DatabaseOpenError
            If the database could not be opened or set up.
        '''
        log.info("Opening database %s", import_db_name)
        self.__db_name = import_db_name
        try:
            self.__conn = None
            self.__conn = sqlite3.connect(import_db_name,
                timeout = self.TIMEOUT,
                # use the declared type to determine the approriate converter/adapter
                # needed for date storage
                detect_types = sqlite3.PARSE_DECLTYPES
                )
            self.conn.row_factory = self.__key_val_description
            # create the tables if not existing
            self.__create()
            # upgrade db to latest layout
            self.__upgrade_db()
        except sqlite3.Error as e:
            raise DatabaseOpenError(import_db_name, caused_by = e), None, sys.exc_info()[2]

    def __upgrade_db(self):
        ''' Upgrade the db to the latest layout '''
        
        # try to execute all update statements
        for sql_stmt in (self.ADD_COLUMN_APP_CODE_SIZE, self.ADD_COLUMN_BUILD_DATE):
            
            try:
                self.conn.execute(sql_stmt)
            # ignore duplicate column error
            except sqlite3.OperationalError:
                pass

    def __del__(self):
        ''' Close database '''
        try:
            log.info("Closing database %s", self.__db_name)
            if self.conn is not None:
                self.conn.close()
        except sqlite3.Error as e:
            log.warn(e)

    def get_db_name(self):
        return self.__db_name

    def set_db_name(self, value):
        self.__db_name = value

    def del_db_name(self):
        del self.__db_name

    def get_conn(self):
        return self.__conn

    def set_conn(self, value):
        self.__conn = value

    def del_conn(self):
        del self.__conn

    def get_cursor(self):
        return self.__cursor

    def set_cursor(self, value):
        self.__cursor = value

    def del_cursor(self):
        del self.__cursor

    db_name = property(get_db_name, set_db_name, del_db_name, "str : Name of the database to use.")
    conn = property(get_conn, set_conn, del_conn, "sqlite3.Connection : The established connection to the database")

    def __str__(self):
        return self.db_name

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    ############################################################
    #---Database specific stuff
    ############################################################

    def __create(self):
        '''
        Create the tables if not already existing.

        Raises
        ------
        sqlite3.Error
        '''
        self.conn.cursor().execute(self.CREATE_STMT)

    ############################################################
    #---ImportQueryInterface
    # For documentation see the docstrings
    # of ImportQueryInterface
    ############################################################

    def get_imported_apks(self, hashes = None, package_names = None, tags = None, **kwargs):
        order_by = kwargs.get('order_by', TABLE_APK_IMPORT_KEY_PACKAGE_NAME)

        # prevent sql injection
        if not order_by in TABLE_APK_IMPORT_KEYS:
            raise ValueError("Sort key has to be in %s, is: %s" % (TABLE_APK_IMPORT_KEYS, order_by))

        ascending = kwargs.get("ascending", True)
        sort_direction = 'ASC' if ascending else 'DESC'

        try:
            SQL_STMT = 'SELECT * FROM %s ' % TABLE_APK_IMPORT

            # create temporary database to store many values and have them later in the IN clause available
            with self.conn as _conn:
                c = _conn.cursor()

                c.execute("DROP TABLE IF EXISTS data_helper")
                c.execute("CREATE TEMPORARY TABLE data_helper (value TEXT)")

                INSERT_HELPER_STMT = "INSERT INTO data_helper VALUES (?)"
                DYN_IN_STMT = 'WHERE %s IN (SELECT * FROM data_helper)'
                args = ()

                if hashes is not None:
                    args = tuple(hashes)
                    SQL_STMT += DYN_IN_STMT % TABLE_APK_IMPORT_KEY_HASH
                elif package_names is not None:
                    args = tuple(package_names)
                    SQL_STMT += DYN_IN_STMT % TABLE_APK_IMPORT_KEY_PACKAGE_NAME
                elif tags is not None:
                    args = tuple(tags)
                    SQL_STMT += DYN_IN_STMT % TABLE_APK_IMPORT_KEY_TAG

                # insert values into temporary table but only if `hashes` or `package_names` has been supplied
                # otherwise return all apks
                if args:
                    # executemany needs iterable<tuple>
                    INSERT_ARGS = ((a, ) for a in args)
                    c.executemany(INSERT_HELPER_STMT, INSERT_ARGS)

            # sort by package names and version
            SQL_STMT += ' ORDER BY %s COLLATE NOCASE %s, %s' % (order_by, sort_direction, TABLE_APK_IMPORT_KEY_PACKAGE_NAME)
            # get apks
            c = self.conn.cursor().execute(SQL_STMT)

            # treat cursor as iterator
            for apk_dict in c:
                yield FastApk(apk_dict[TABLE_APK_IMPORT_KEY_PACKAGE_NAME],
                              apk_dict[TABLE_APK_IMPORT_KEY_VERSION_NAME],
                              path = apk_dict[TABLE_APK_IMPORT_KEY_PATH],
                              _hash = apk_dict[TABLE_APK_IMPORT_KEY_HASH],
                              import_date = apk_dict[TABLE_APK_IMPORT_KEY_IMPORT_DATE],
                              tag = apk_dict[TABLE_APK_IMPORT_KEY_TAG],
                              size_app_code = apk_dict[TABLE_APK_IMPORT_KEY_SIZE_APP_CODE],
                              build_date = apk_dict.get(TABLE_APK_IMPORT_KEY_BUILD_DATE)
                            )

        except (sqlite3.Error, KeyError) as e:
            data = "all apks"
            if hashes is not None:
                data = ', '.join(hashes)
            elif package_names is not None:
                data = ', '.join(package_names)
            raise ImportQueryError(DatabaseLoadException(self, data , e)), None, sys.exc_info()[2]

    def get_versions(self, hashes = None, package_names = None, tags = None):
        return self._get_apk_infos(lambda apk : apk.version_name, hashes, package_names, tags)

    def get_apk_hashes(self, package_names = None, tags = None):
        return self._get_apk_infos(lambda apk : apk.hash, hashes = None, package_names = package_names, tags = tags)

    def get_apk_package_names(self, hashes = None, tags = None):
        return self._get_apk_infos(lambda apk : apk.package_name, hashes = hashes, tags = tags)

    def get_apk_paths(self, hashes = None, package_names = None, tags = None):
        '''
        Get the paths of the imported apks.

        Parameters
        ----------
        hashes : iterable<str>, optional (default is None)
        package_names : iterable<str>, optional (default is None)
        tags : iterable<str>, optional (default is None)

        Raises
        ------
        ImportQueryError

        Returns
        -------
        generator<str>
        '''
        return self._get_apk_infos(lambda apk : apk.path, hashes = hashes, package_names=package_names, tags = tags)

    ############################################################
    #---ImportStorageInterface
    ############################################################

    def create_entry_for_apk(self, apk, update = False, tag = None):
        ''' Create entry for a single `apk`.

        Parameters
        ----------
        apk : Apk
        update : bool, optional (default is False)
            Update an `apk` that has already been imported.
        tag : str, optional (default is None)
            Tag the apk with some text.

        Raises
        ------
        DatabaseStoreException
        '''
        try:
            # does committing and rollback in case of exception
            # but we also have autocommit for sql dml
            with self.conn as _conn:
                _hash, pn, vn, path, import_date, size_app_code, build_date = apk.hash, apk.package_name, apk.version_name, apk.path, apk.import_date, apk.size_app_code, apk.get_build_date()
                c = _conn.cursor()
                in_storage = self.contains(apk)
                # if already in db, update the entry
                if in_storage and update:
                    c.execute(self.UPDATE_STMT, (pn, vn, path, import_date, tag, size_app_code, build_date, _hash))
                # otherwise insert it
                elif not in_storage:
                    c.execute(self.INSERT_STMT, (_hash, pn, vn, path, import_date, tag, size_app_code, build_date))
        except (sqlite3.Error, CouldNotOpenApk) as e:
            raise DatabaseStoreException(self, apk, e), None, sys.exc_info()[2]

    def delete_entry_for_apk(self, apk, delete_apk = False):
        ''' Delete the `apk` from the database.

        Parameters
        ----------
        apk: Apk
        delete_apk : boolean, optional (default is False)
            Not recognized.

        Raises
        ------
        DatabaseDeleteException
        '''
        try:
            with self.conn as _conn:
                c = _conn.cursor()
                c.execute(self.DELETE_STMT, (apk.hash, ))
        except (sqlite3.Error, CouldNotOpenApk) as e:
            raise DatabaseDeleteException(self, apk, e), None, sys.exc_info()[2]

    def contains(self, apk):
        ''' Check if the `apk` has been imported yet.

        Parameters
        ----------
        apk: Apk

        Returns
        -------
        bool

        Raises
        ------
        DatabaseStoreException
        '''
        CHECK_STMT = 'SELECT %s FROM %s WHERE hash = ?' % (TABLE_APK_IMPORT_KEY_HASH, TABLE_APK_IMPORT)
        try:
            with self.conn as conn:
                c = conn.cursor().execute(CHECK_STMT, (apk.hash,))
                return self.__query_has_only_1_res(c)
        except sqlite3.Error as e:
            raise DatabaseStoreException(self, apk, e), None, sys.exc_info()[2]

    ############################################################
    #---Helper functions
    ############################################################

    def _get_apk_infos(self, project_func, hashes = None, package_names = None, tags = None):
        '''
        Helper function for selecting some attributes of the imported apks from the db.

        If neither `hashes` nor `package_names` nor `tags` are given,
        return all imported `Apk`s.

        Only one of the filter arguments will be used.

        Preferred order is: hashes, package_names, tags.

        Parameters
        ----------
        project_func : Apk -> object
            Function that returns the wanted attribute of the `Apk`.
        hashes : iterable<str>, optional (default is None)
        package_names : iterable<str>, optional (default is None)
        tags : iterable<str>, optional (default is None)


        Raises
        ------
        ImportQueryError

        Returns
        -------
        generator<object>
        '''
        apks = self.get_imported_apks(hashes, package_names, tags)
        for apk in apks:
            yield project_func(apk)

    @staticmethod
    def __query_has_only_1_res(cursor):
        ''' Check if the query returned only one result.

        Parameters
        ----------
        cursor : sqlite3.Cursor
        '''
        return len(cursor.fetchall()) == 1

    @staticmethod
    def __key_val_description(cursor, row):
        ''' Build a dictionary containing the column names as keys
        associated with the result of the `row`.

        Parameters
        ----------
        cursor : sqlite3.Cursor
        row : tuple
            Holds the result what shall be transformed into a key/value store

        Returns
        -------
        dict
        '''
        _dict = {}
        for idx, col in enumerate(cursor.description):
            _dict[col[0]] = row[idx]
        return _dict

if __name__ == "__main__":
    from androlyze.storage.exception import DatabaseException
    from traceback import format_exception

    IMPORT_DB = "../../../import.db"
    try:
        db = ImportDatabaseStorage(IMPORT_DB)
        # get versions for package name
        print '\n'.join(db.get_versions(["com.whatsapp"]))
        # get all hashes
        print '\n'.join(db.get_apk_hashes(["com.whatsapp"]))
        print '\n'.join(db.get_apk_hashes(["com.whatsapp", "a2dp.Vol"]))
        #print '\n'.join(db.get_apk_hashes(db.get_apk_package_names()))
        # get all import package names
        print '\n '.join(db.get_apk_package_names())
        # get all package names plus version
    except (DatabaseException, ImportQueryError):
        print '\n'.join(format_exception(*sys.exc_info()))
