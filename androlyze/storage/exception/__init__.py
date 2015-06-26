
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.error.WrapperException import WrapperException

############################################################
#---Helper functions
############################################################
def _create_delete_error_msg(content, destination):
    return "Could not delete %s from %s" % (content, destination)

def _create_store_error_msg(content, destination):
    return "Could not store result for %s to %s" % (content, destination)

def _create_load_error_msg(content, source):
    return "Could not load %s from %s" % (content, source)

############################################################
#---General storage exceptions
############################################################

class StorageException(WrapperException):
    ''' Base exception for data storage '''
    pass

############################################################
#---Database storage exceptions
############################################################

DB_STORE = "database"

class DatabaseException(StorageException):
    pass

class EDatabaseException(DatabaseException):
    ''' Extended DatabaseException that has the database as parameter as well as content '''

    def __init__(self, db, content, caused_by = None, **kwargs):
        '''
        Parameters
        ----------
        db : object
        content : object
            The object that couldn't be loaded/stored.
        caused_by: Exception, optional (default is None)
            the exception that caused this one to raise
       '''
        DatabaseException.__init__(self, caused_by = caused_by, **kwargs)
        self.db = db
        self.content = content

class DatabaseDeleteException(EDatabaseException):

    def _msg(self):
        return _create_delete_error_msg(self.content, self.db)

class DatabaseStoreException(EDatabaseException):

    def _msg(self):
        return _create_store_error_msg(self.content, self.db)

class DatabaseLoadException(EDatabaseException):

    def _msg(self):
        return _create_load_error_msg(self.content, self.db)

class DatabaseOpenError(DatabaseException):

    def __init__(self, db_name, **kwargs):
        super(DatabaseOpenError, self).__init__(**kwargs)
        self.db_name = db_name

    def _msg(self):
        return 'Could not open database: "%s"' % self.db_name

############################################################
#---S3 storage exceptions
############################################################

DB_STORE = "database"

class S3StorageException(StorageException):
    pass

class ES3StorageException(S3StorageException):
    ''' Extended DatabaseException that has the database as parameter as well as content '''

    def __init__(self, db, content, caused_by = None, **kwargs):
        '''
        Parameters
        ----------
        db : object
        content : object
            The object that couldn't be loaded/stored.
        caused_by: Exception, optional (default is None)
            the exception that caused this one to raise
       '''
        S3StorageException.__init__(self, caused_by = caused_by, **kwargs)
        self.db = db
        self.content = content

class S3StorageDeleteException(ES3StorageException):

    def _msg(self):
        return _create_delete_error_msg(self.content, self.db)

class S3StorageStoreException(ES3StorageException):

    def _msg(self):
        return _create_store_error_msg(self.content, self.db)

class S3StorageLoadException(ES3StorageException):

    def _msg(self):
        return _create_load_error_msg(self.content, self.db)

class S3StorageOpenError(ES3StorageException):

    def __init__(self, db_name, **kwargs):
        super(ES3StorageException, self).__init__(**kwargs)
        self.db_name = db_name

    def _msg(self):
        return 'Could not open bucket: "%s"' % self.db_name


############################################################
#---File system storage exceptions
############################################################

class FileSysException(StorageException):
    def __init__(self, file_path, fs_storage, *args, **kwargs):
        '''
        Parameters
        ----------
        file_path: str
            the path of the file
        fs_store : FileSysStorage
        '''
        super(FileSysException, self).__init__(*args, **kwargs)
        self.file_path = file_path
        self.fs_storage = fs_storage

class FileSysStoreException(FileSysException):

    def __init__(self, file_path, content, fs_storage, caused_by = None):
        '''
        Parameters
        ----------
        file_path: str
            the path of the file
        content: object
            the content which should be stored
        fs_store : FileSysStorage
        caused_by: Exception, optional (default is None)
            the exception that caused this one to raise
        '''
        super(FileSysStoreException, self).__init__(file_path, fs_storage, caused_by = caused_by)
        self.content = content

    def _msg(self):
        return _create_store_error_msg(self.content, self.file_path)

class FileSysCreateStorageStructureException(FileSysException):

    def __init__(self, file_path, fs_storage, caused_by = None):
        '''
        Parameters
        ----------
        file_path: str
            the path of the file
        fs_store : FileSysStorage
        caused_by: Exception, optional (default is None)
            the exception that caused this one to raise
        '''
        super(FileSysCreateStorageStructureException, self).__init__(file_path, fs_storage, caused_by = caused_by)

    def _msg(self):
        return "Could not create the file system structure: %s" % self.file_path

class FileSysLoadException(FileSysException):

    def _msg(self):
        return _create_load_error_msg(self.file_path, self.fs_storage)

class FileSysDeleteException(FileSysException):

    def _msg(self):
        return _create_delete_error_msg(self.file_path, self.fs_storage)
