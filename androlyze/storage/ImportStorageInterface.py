
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.log.Log import log
from androlyze.storage.exception import StorageException

class ImportStorageInterface:
    '''
    Interface for the import storage
    '''

    def create_entry_for_apk(self, apk, update = False, tag = None):
        ''' Create an entry for the `apk`.

        Will also update the path, if the file
        is already present in the database and has the same hash
        (at least if `update`).

        Parameters
        ----------
        apk : Apk
        update : bool, optional (default is False)
            Update an `apk` that has already been imported.
        tag : str, optional (default is None)
            Tag the apk with some text.

        Raises
        ------
        StorageException
        '''
        raise NotImplementedError

    def create_entry_for_apks(self, apks, update, tag = None):
        ''' Create entry for the `apks`.

        Parameters
        ----------
        apk: iterable<Apk>
        update : bool
            Update apks that have already been imported.
        tag : str, optional (default is None)
            Tag the apk with some text.
        '''
        for apk in apks:
            try:
                self.create_entry_for_apk(apk, update, tag)
            except StorageException as e:
                log.warn(e)

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
        raise NotImplementedError

    def contains(self, apk):
        ''' Check if the `apk` is present in the storage.

        Parameters
        ----------
        apk: Apk

        Returns
        -------
        bool
        '''
        raise NotImplementedError
