
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from collections import OrderedDict
import os
import ssl
import sys

from androlyze.analyze import AnalyzeUtil
from androlyze.log.Log import log
from androlyze.model.analysis.result.StaticResultKeys import *
from androlyze.model.android.apk.FastApk import FastApk
from androlyze.storage.apk.ApkCopyInterface import ApkCopyInterface
from androlyze.storage.exception import DatabaseOpenError, \
    DatabaseDeleteException, DatabaseStoreException, DatabaseLoadException
from androlyze.storage.resultdb import MongoUtil
from androlyze.storage.resultdb.MongoUtil import escape_keys, \
    MONGODB_IN_OPERATOR
from androlyze.storage.resultdb.ResultsStorageInterface import ResultStorageInterface
from bson.errors import BSONError
import gridfs
from gridfs.errors import NoFile
import pymongo
from pymongo.errors import PyMongoError, ConnectionFailure

# collection name for normal documents
RESULT_DOCUMENTS_COLLECTION_NAME = "docs"

# gridfs collections prefix
GRIDFS_COLLS_PREFIX = "fs"

# gridfs chunks collection
GRIDFS_CHUNKS = 'chunks'

# gridfs files metadata key
GRIDFS_FILES_METADATA = 'metadata'
# gridfs files filename key
GRIDFS_FILES_FILENAME = 'filename'

# gridfs files collection
GRIDFS_FILES = "files"

# gridfs collections
FILES_COLL_NAME = '%s.%s' % (GRIDFS_COLLS_PREFIX, GRIDFS_FILES)
CHUNKS_COLL_NAME = '%s.%s' % (GRIDFS_COLLS_PREFIX, GRIDFS_CHUNKS)

# apk database
APK_DB_NAME = 'apks'

# tuple of exceptions that indiciate connection errors
CONNECTION_FAIL_ERRORS = (ConnectionFailure, )

MAX_BSON_SIZE = 16770000

class ResultDatabaseStorage(object, ResultStorageInterface, ApkCopyInterface):
    ''' Class for storing documents and/or binary data in mongodb. '''

    def __init__(self, db_name = None, dest_addr = None, dest_port = None,
                # auth
                username = None, passwd = None,
                # ssl
                use_ssl = False, ssl_ca_certs = None,
                
                ):
        '''
        Create (if not existing) and open the database and collections.

        Parameters
        ----------
        db_name : str, optional (default is "res")
            The name of the database to use.
            Will be created if not already existing.
        dest_addr : str, optional (default is '127.0.0.1')
            Address of mongodb database server.
        dest_port : int, optional (default is 27017)
            Port of mongodb database server.
        username : str, optional (default is None)
            No authentication at all.
        passwd : str, optional (default is None)
            No authentication at all.
        use_ssl : bool, optional (default is False)
            Use ssl for the connection.
        ssl_ca_certs : str, optional (default is None)
            The CA certificate.
        
        Raises
        ------
        DatabaseOpenError
        '''

        # db name not allowed
        if db_name == APK_DB_NAME:
            raise DatabaseOpenError(db_name, msg = 'Database name "%s" reserved for apk storage!' % db_name), None, sys.exc_info()[2]

        # set default values
        if db_name is None:
            db_name = 'res'
        if dest_addr is None:
            dest_addr = '127.0.0.1'
        if dest_port is None:
            dest_port = 27017

        try:
            self.__db_name = db_name
            self.__dest_addr = dest_addr
            self.__dest_port = dest_port
            self.__use_ssl = use_ssl

            # only pass ssl parameters if ssl enabled
            ssl_params = dict(ssl = use_ssl, ssl_cert_reqs = ssl.CERT_NONE) if use_ssl else {}

            # set None cause if connection cannot be initiated, conn var will not in scope
            self.conn = None
            self.__conn = conn = pymongo.MongoClient(host = dest_addr, port = dest_port, **ssl_params)

            # authentication is per database!
            # do auth before probable db creation etc.
            if None not in (username, passwd):
                # authenticate if credentials given
                log.debug("authenticating with mongodb ...")
                conn["admin"].authenticate(username, passwd)
            else:
                log.debug("not authenticating with mongodb ... no credentials supplied!")

            self.__db = conn[self.db_name]

            # apk db
            self.__apk_db = conn[APK_DB_NAME]
            
            self.__apk_coll = gridfs.GridFS(self.__apk_db, GRIDFS_COLLS_PREFIX)

            # create/open collections
            self.__res_coll = self._open_res_coll()
            self.__files_coll = self.__db[GRIDFS_COLLS_PREFIX][GRIDFS_FILES]
            # grid fs for binary files, supports files > 16 mb
            self.__grid_fs = self._open_gridfs()

            # create indexes
            self._create_idx_for_colls()

            log.info("Opened database: %s", self)
            log.debug("CA certificate: %s", ssl_ca_certs)

        except PyMongoError as e:
            raise DatabaseOpenError(str(self), caused_by = e), None, sys.exc_info()[2]

    def __del__(self):
        ''' Close db connection '''
        if self.conn is not None:
            log.debug("Closing db connection ... ")
            self.conn.close()

    def get_apk_db(self):
        return self.__apk_db

    def get_apk_coll(self):
        return self.__apk_coll

    def set_apk_db(self, value):
        self.__apk_db = value

    def set_apk_coll(self, value):
        self.__apk_coll = value

    def del_apk_db(self):
        del self.__apk_db

    def del_apk_coll(self):
        del self.__apk_coll

    def __str__(self):
        return '%s: mongodb://%s:%s/%s/?ssl=%s' % (self.__class__.__name__, self.dest_addr, self.dest_port, self.db_name, self.use_ssl)

    def get_db_name(self):
        return self.__db_name

    def set_db_name(self, value):
        self.__db_name = value

    def del_db_name(self):
        del self.__db_name

    def get_files_coll(self):
        return self.__files_coll

    def set_files_coll(self, value):
        self.__files_coll = value

    def del_files_coll(self):
        del self.__files_coll

    def get_grid_fs(self):
        return self.__grid_fs

    def set_grid_fs(self, value):
        self.__grid_fs = value

    def del_grid_fs(self):
        del self.__grid_fs

    def get_dest_addr(self):
        return self.__dest_addr

    def get_dest_port(self):
        return self.__dest_port

    def set_dest_addr(self, value):
        self.__dest_addr = value

    def set_dest_port(self, value):
        self.__dest_port = value

    def del_dest_addr(self):
        del self.__dest_addr

    def del_dest_port(self):
        del self.__dest_port

    def get_res_coll(self):
        return self.__res_coll

    def set_res_coll(self, value):
        self.__res_coll = value

    def del_res_coll(self):
        del self.__res_coll

    def get_conn(self):
        return self.__conn

    def get_db(self):
        return self.__db

    def set_conn(self, value):
        self.__conn = value

    def set_db(self, value):
        self.__db = value

    def del_conn(self):
        del self.__conn

    def del_db(self):
        del self.__db

    def get_use_ssl(self):
        return self.__use_ssl

    db_name = property(get_db_name, set_db_name, del_db_name, "db_name : str, optional (default is 'res') - The name of the database to use. Will be created if not already existing.")
    dest_addr = property(get_dest_addr, set_dest_addr, del_dest_addr, "str, optional (default is '127.0.0.1') : Address of mongodb database server.")
    dest_port = property(get_dest_port, set_dest_port, del_dest_port, "int, optional (default is 27017) : Port of mongodb database server.")
    use_ssl = property(get_use_ssl, None, None, " bool, optional (default is False) : Use ssl for the connection.")
    conn = property(get_conn, set_conn, del_conn, "pymongo.mongo_client.MongoClient : Mongodb connection")
    db = property(get_db, set_db, del_db, "pymongo.database.Database : Database")
    res_coll = property(get_res_coll, set_res_coll, del_res_coll, "pymongo.collection.Collection : results collection for documents")
    grid_fs = property(get_grid_fs, set_grid_fs, del_grid_fs, "gridfs.GridFS : Gridfs object for non-document and binary storage.")
    files_coll = property(get_files_coll, set_files_coll, del_files_coll, "pymongo.collection.Collection : files follection of gridfs")

    apk_db = property(get_apk_db, set_apk_db, del_apk_db, "pymongo.database.Database : Apk database")
    apk_coll = property(get_apk_coll, set_apk_coll, del_apk_coll, "gridfs.GridFS : Apk collection (gridfs)")

    ############################################################
    #---ResultStorageInterface
    ############################################################

    def store_result_for_apk(self, apk, script):
        ''' See doc of :py:meth:`.ResultWritingInterface.store_result_for_apk`.

        Returns
        -------
        tuple<str, bool>
            First component is the id of the entry
            and the second a boolean indication if the result has been stored in gridfs.
        None
            If an error occurred.
        '''
        try:
            # escape keys for mongodb insert
            res_obj_dict = escape_keys(script.result_dict(gen_id = False))
            _id = script.gen_unique_id()

            # if data is to big or custom result object used -> store with gridfs
            if script.uses_custom_result_object() or script.is_big_res():
                log.debug("storing results for %s, %s in %s (id: %s)", apk.short_description(), script, self.grid_fs, _id)
                result = self.get_custom_res_obj_representation(script)

                gridfs = self.grid_fs

                # gridfs doesn't have an update method -> delete and insert
                if gridfs.exists(**{RESOBJ_ID : _id}):
                    # delete by _id
                    gridfs.delete(_id)

                # store file together with metadata from `ResultObject`
                gridfs.put(result, metadata = res_obj_dict, filename = script.get_file_name(), _id = _id)

                # return id
                return _id, True

            # normal json data
            else:
                log.debug("storing results for %s, %s in %s db(id: %s)", apk.short_description(), script, self.res_coll, _id)
                # set id so we don't have multiple results for same script and apk
                res_obj_dict[RESOBJ_ID] = _id
                # update or insert if not existing
                self.res_coll.update({RESOBJ_ID : _id}, res_obj_dict, upsert = True)
                # return id
                return _id, False
        except (PyMongoError, BSONError) as e:
            raise DatabaseStoreException(self, "script: %s" % script, caused_by = e), None, sys.exc_info()[2]

    def get_results(self,
                    include_fields = None, exclude_fields = None,
                    where = None, distinct_key = None,
                    n = None, sort = True, latest = False,
                    non_document = False, non_document_raw = False,
                    remove_id_field = True,
                    **kwargs):
        ''' See doc of :py:meth:`.ResultStorageInterface.get_results` '''

        if include_fields is not None and exclude_fields is not None:
            raise ValueError("include_fields and exclude_fields are mutually exclusive!")

        if include_fields is None:
            include_fields = []
        if exclude_fields is None:
            exclude_fields = []
        if where is None:
            where = {}

        # latest means enable sorting and only return one result
        if latest:
            sort = True
            n = 1

        # create projection dict
        fields = [(p, 0) for p in exclude_fields] + [(p, 1) for p in include_fields]

        if remove_id_field:
            # we don't want the id field
            fields += [(RESOBJ_ID, 0)]

        select = dict(fields)

        # no projection criteria given, disable!
            # because empty dict means only id
        if not select:
            select = None

        where.update(self.create_where_clause(kwargs, from_gridfs = non_document))

        try:
            res_cursor = None
            # get appropriate collection
            coll = self.__get_collection(gridfs_files_coll = non_document and not non_document_raw,
                                         gridfs_obj = non_document and non_document_raw)

            # pymongo 3.0 removed the as_class option in the collection.find method
            # this is the fix
            find_kwargs = {}
            if int(pymongo.version[0]) < 3:
                find_kwargs['as_class'] = OrderedDict
                
            # grid fs
            if non_document:
                if non_document_raw:
                    log.debug("mongodb query: find(%s) on gridfs", where)
                    res_cursor = coll.find(where)
                else:
                    # using the gridfs files collection directly enables us projection an attributes
                    log.debug("mongodb query: find(%s, %s) ", where, select)
                    res_cursor = coll.find(where, select, **find_kwargs)

            # normal collection
            else:
                res_cursor = coll.find(where, select, **find_kwargs)
                log.debug("mongodb query: find(%s, %s) ", where, select)


            # enable sorting if wanted
            if sort:
                # construct sorting criteria structure, structure is different if using gridfs
                sort_crit = [(
                  MongoUtil.get_attr_str(RESOBJ_SCRIPT_META, RESOBJ_SCRIPT_META_ANALYSIS_DATE, gridfs=non_document)
                  , -1)]
                res_cursor = res_cursor.sort(sort_crit)

            # limit results if wanted
            if n is not None:
                res_cursor = res_cursor.limit(n)

            # generator that abstracts if normal collection or is gridfs
            if non_document:
                if non_document_raw:
                    return res_cursor

            if distinct_key is not None:
                res_cursor = res_cursor.distinct(distinct_key)

            return res_cursor

        except PyMongoError as e:
            raise DatabaseLoadException(self, "find(%s, %s)", where, select, caused_by = e), None, sys.exc_info()[2]

    def get_results_for_ids(self, ids, non_document = False, non_document_raw = False):
        ''' See :py:method:`.ResultStorageInterface.get_results_for_ids` '''
        return self.get_results(where = {RESOBJ_ID : {MONGODB_IN_OPERATOR : ids}},
                                non_document = non_document, non_document_raw = non_document_raw)

    def delete_results(self,
                       where = None, non_document = False, **kwargs):
        ''' See doc of :py:meth:`.ResultStorageInterface.delete_results` '''
        coll = self.__get_collection(gridfs_obj = non_document)

        if where is None:
            where = {}

        where.update(self.create_where_clause(kwargs, from_gridfs = non_document))

        n = 0
        try:
            # do the query
            log.debug("mongodb remove(%s)", where)

            # gridfs
            if non_document:
                # get ids and delete
                for _id in self.get_ids(where = where, non_document = non_document):
                    coll.delete(_id)
                    log.debug("Deleted element with id: %s from mongodb gridfs!", _id)
                    n += 1

            # normal collection
            else:
                write_result = coll.remove(where, getLastError=True)
                if write_result is not None:
                    n = write_result["n"]

            return n

        except PyMongoError as e:
            log.exception(DatabaseDeleteException(self, where, e))
            return n

    def erase_whole_db(self):
        '''
        Use to drop collections and recreate them.
        See doc of :py:meth:`.ResultStorageInterface.erase_whole_db`

        '''
        self.__recreate_collections(gridfs = True, res_collection = True)

    ############################################################
    #---ApkCopyInterface
    ############################################################

    def copy_apk(self, apk, file_like_obj, **kwargs):
        ''' See doc of :py:meth:`.ApkCopyInterface.copy_apk`.

        Inserts the apk from the `file_like_obj` into mongodb's gridfs,
        but only if not already in db.

        Returns
        -------
        The id of the apk (in db)
        '''
        file_like_obj.seek(0)
        try:
            gridfs = self.__apk_coll

            # escape keys accoring to mongodb rules
            apk_meta = escape_keys(apk.meta_dict())

            _id = apk.hash
            # gridfs doesn't have an update method -> delete and insert
            if not gridfs.exists(**{RESOBJ_ID : _id}):

                # store file together with metadata
                filename = os.path.basename(apk_meta[RESOBJ_APK_META][RESOBJ_APK_META_PATH])
                gridfs.put(file_like_obj, metadata = apk_meta[RESOBJ_APK_META], filename = filename, _id = _id, chunkSize = MAX_BSON_SIZE)
                log.info("put %s into %s", apk.short_description(), self)
        except (PyMongoError, BSONError) as e:
            raise DatabaseStoreException(self, "apk: %s" % apk.short_description(), caused_by = e), None, sys.exc_info()[2]

        # return id
        return _id

    def get_apk(self, _hash, **kwargs):
        '''
        Get the `EAndroApk` from `_hash`.

        Parameters
        ----------
        _hash : str
            Hash of the .apk (sha256)

        Raises
        ------
        DatabaseLoadException
        NoFile
            If the file is not present.

        Returns
        -------
        EAndroApk
            Apk constructed from raw data and meta infos.
        '''
        try:
            gridfs = self.__apk_coll
            log.info("getting apk: %s from mongodb ...", _hash)
            gridfs_obj = gridfs.get(_hash)
            # get raw .apk
            apk_zipfile = gridfs_obj.read()

            # get apk meta infos
            apk_meta = gridfs_obj.metadata
            package_name, version_name, path, _hash, import_date, tag = apk_meta[RESOBJ_APK_META_PACKAGE_NAME], apk_meta[RESOBJ_APK_META_VERSION_NAME], apk_meta[RESOBJ_APK_META_PATH], apk_meta[RESOBJ_APK_META_HASH], apk_meta[RESOBJ_APK_META_IMPORT_DATE], apk_meta[RESOBJ_APK_META_TAG]

            # use to hold apk meta infos
            fast_apk = FastApk(package_name, version_name, path, _hash, import_date, tag)
            eandro_apk = AnalyzeUtil.open_apk(apk_zipfile, fast_apk, raw = True)

            log.info("got apk")
            return eandro_apk
        except NoFile:
            raise
        except PyMongoError as e:
            raise DatabaseLoadException(self, content = "Apk (hash=%s)" % _hash, caused_by = e), None, sys.exc_info()[2]

    ############################################################
    #---MongoDB query builder helper functions
    ############################################################

    def create_where_clause(self, kwargs, from_gridfs = False):
        '''
        Create where clause from `kwargs`.

        Parameters
        ----------
        from_gridfs : bool, optional (default is False)
            Whether to build where clause for gridfs.

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

        Returns
        -------
        '''
        # create filter dict
        wheres = []
        wheres += MongoUtil.build_apk_meta_where(kwargs, gridfs = from_gridfs)
        wheres += MongoUtil.build_script_meta_where(kwargs, gridfs = from_gridfs)
        return dict(wheres)

    ############################################################
    #---Other
    ############################################################

    def get_eandro_apk(self, _id):
        '''
        Get the `EAndroApk` from database.

        Returns
        -------
        EAndroApk
        None
            If Apk could not be loaded
        '''
        try:
            return self.get_apk(_id)
        except (DatabaseLoadException, NoFile) as e:
            log.warn(e)

    ############################################################
    #---Helper stuff
    ############################################################

    def _create_idx_for_colls(self):
        ''' Create index(es) for the collections '''

        def create_idx(coll):
            ''' Create index on a single collection '''
            # apk meta
            coll.ensure_index([(MongoUtil.get_attr_str(RESOBJ_SCRIPT_META, RESOBJ_APK_META_PACKAGE_NAME, gridfs = False), -1)])
            coll.ensure_index([(MongoUtil.get_attr_str(RESOBJ_SCRIPT_META, RESOBJ_APK_META_BUILD_DATE, gridfs = False), -1)])
            # script meta
            coll.ensure_index([(MongoUtil.get_attr_str(RESOBJ_SCRIPT_META, RESOBJ_SCRIPT_META_ANALYSIS_DATE, gridfs = False), -1)])
            coll.ensure_index([(MongoUtil.get_attr_str(RESOBJ_SCRIPT_META, RESOBJ_SCRIPT_META_NAME, gridfs = False), -1)])

        # create indexes
        create_idx(self.res_coll)
        create_idx(self.files_coll)

    def _open_res_coll(self):
        '''
        Create/open results collection.

        Raises
        ------
        PyMongoError
        '''
        res_coll = self.db[RESULT_DOCUMENTS_COLLECTION_NAME]
        
        # pymongo 3.0 removed the as_class option in the collection.find method
        # this is the fix
        if int(pymongo.version[0]) >= 3:
            from bson.codec_options import CodecOptions
            res_coll = res_coll.with_options(codec_options = CodecOptions(document_class = OrderedDict))
            
        return res_coll

    def _open_gridfs(self):
        '''
        Create/open gridfs.

        Raises
        ------
        PyMongoError
        '''
        return gridfs.GridFS(self.db, GRIDFS_COLLS_PREFIX)

    def __get_collection(self, gridfs_files_coll = False, gridfs_obj = False):
        ''' Get the right collection.

        If no parameter supplied or all False,
        the collection for normal document storage will be returned.

        Parameters are mutually exclusive!

        Parameters
        ----------
        gridfs_files_coll : bool, optional (default is False)
            If you need to access the gridfs fils collection.
            Returns a normal collection, no `GridFS` object!
        gridfs_obj : bool, optional (default is False)
            Get the GridFS object.

        Returns
        -------
        gridfs.GridFS
            If `gridfs_obj`
        pymongo.collection.Collection
            Otherwise
        '''
        if gridfs_files_coll:
            return self.get_files_coll()

        if gridfs_obj:
            return self.grid_fs

        return self.get_res_coll()

    def get_ids(self,
                  non_document = False, where = None):
        '''
        Get the id's for the results filtered by `where`.

        Parameters
        ----------
        non_document : bool, optional (default is False)
            If True, use gridfs.
        where : dict, optional (default is None)
            Dictionary doing the filtering.
            If not given, get all ids.

        Returns
        ------
        list<str>
        '''
        id_gen = self.get_results(where = where, remove_id_field = False,
                                  non_document = non_document,
                                  include_fields = [RESOBJ_ID])

        # get id out of dict
        return [id_dict[RESOBJ_ID] for id_dict in id_gen]

    def get_all_ids(self, where = None):
        '''
        Get all id's filtered by `where`.

        Parameters
        ----------
        where : dict, optional (default is None)
            Dictionary doing the filtering.
            If not given, get all ids.

        Returns
        ------
        list<str>
        '''
        return self.get_ids(non_document = True, where = where) + self.get_ids(non_document = False, where = where)

    def __recreate_collections(self, gridfs = False, res_collection = False):
        '''
        Drop and recreate collections.

        Parameters
        ----------
        gridfs : bool, optional (default is False)
            Recreate gridfs.
        res_collection, bool, optional (default is False)
            Recreate results collection.
        '''
        try:
            if gridfs:
                log.debug("dropping collection %s", GRIDFS_COLLS_PREFIX)

                log.debug("dropping collection %s", FILES_COLL_NAME)
                self.db.drop_collection(FILES_COLL_NAME)

                log.debug("dropping collection %s", CHUNKS_COLL_NAME)
                self.db.drop_collection(CHUNKS_COLL_NAME)

                log.debug("recreating collection %s", GRIDFS_COLLS_PREFIX)
                self._open_gridfs()

                self._create_idx_for_colls()
        except PyMongoError as e:
            log.critical(e)

        try:
            if res_collection:
                log.debug("dropping collection %s", RESULT_DOCUMENTS_COLLECTION_NAME)
                self.db.drop_collection(RESULT_DOCUMENTS_COLLECTION_NAME)
                self._open_res_coll()
                log.debug("recreating collection %s", RESULT_DOCUMENTS_COLLECTION_NAME)
        except PyMongoError as e:
            log.critical(e)

def factory_from_config(settings):
    ''' Get a factory_from_config object from the distributed config.
    
    Parameters
    ----------
    settings : Settings
     '''
    from androlyze.celery.celerysettings import settings
    return ResultDatabaseStorage(*settings.get_mongodb_settings())

if __name__ == '__main__':
    from androlyze.model.script.ScriptUtil import dict2json
    print "foo"
    res_db = ResultDatabaseStorage()
    _if = ["script meta", "apk meta", "apkinfo.libraries"]
    _if = None
    ef = ["apkinfo"]
    wheres = [("apk meta.package name", "a2dp.Vol")]
    version = "0.1"
    for res in res_db.get_results(include_fields = _if, exclude_fields = ef, wheres = wheres, n = 2, version=version):
        print dict2json(res)

    print res_db