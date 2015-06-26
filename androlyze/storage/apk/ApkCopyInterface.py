
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

class ApkCopyInterface:
    '''
    Interface for copying an .apk
    '''

    def copy_apk(self, apk, file_like_obj, copy2fs = False, copy2db = False, **kwargs):
        '''
        Parameters
        ----------
        apk: Apk
            Holds meta information needed to create the subdirectory names.
        file_like_obj
            A file-like object which holds the .apk data
        copy2fs : bool, optional (default is False)
            If true, copy to file system.
        copy2db : bool, optional (default is False)
            If true, copy to mongodb.

        Raises
        ------
        StorageException

        Returns
        -------
        Can optionally return some path, storage information.
        '''
        raise NotImplementedError

    def get_apk(self, _hash, apk = None, **kwargs):
        '''
        Get the `EAndroApk` from `_hash`.

        Parameters
        ----------
        _hash : str
            Hash of the .apk
        apk : Apk, optional (default is None)
            Some storage servies may need additional information from the `apk`.
            E.g. a `FastApk` carrying only the metainformation.
        
        Raises
        ------
        StorageException

        Returns
        -------
        EAndroApk
            Apk constructed from raw data and meta infos.
        '''
        raise NotImplementedError

    def is_s3(self):
        from androlyze.storage.s3.S3Storage import S3Storage
        return isinstance(self, S3Storage)
    
    def is_mongodb(self):
        from androlyze.storage.resultdb.ResultDatabaseStorage import ResultDatabaseStorage
        return isinstance(self, ResultDatabaseStorage)
    