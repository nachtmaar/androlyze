
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from datetime import datetime
from fnmatch import fnmatch
from io import BytesIO
import itertools
import os
from os.path import isfile, join, isdir
import sys

from androlyze.loader.exception import ApkImportError
from androlyze.log import log
from androlyze.model.android.Constants import ANDROID_FILE_EXTENSION
from androlyze.model.android.apk.FastApk import FastApk
from androlyze.storage.exception import StorageException


class ApkImporter(object):
    ''' Class for loading/importing a list of apk files '''

    def __init__(self, apk_paths, storage):
        '''
        Parameters
        ----------
        apk_paths: iterable<str>
            List of apk files (paths) or directories..
        storage : RedundantStorage
            The storage to use for importing.
        '''
        self.__apk_paths = self.get_apks_from_list_or_dir(apk_paths)
        self.__storage = storage

    def get_apk_paths(self):
        # use absolute paths in iterators
        self.__apk_paths, new_it = itertools.tee(self.__apk_paths)
        return (os.path.abspath(p) for p in new_it)

    def set_apk_paths(self, value):
        self.__apk_paths = value

    def del_apk_paths(self):
        del self.__apk_paths

    def get_storage(self):
        return self.__storage

    def set_storage(self, value):
        self.__storage = value

    def del_storage(self):
        del self.__storage

    storage = property(get_storage, set_storage, del_storage, "StorageInterface : storage for audit results of apks")
    apk_paths = property(get_apk_paths, set_apk_paths, del_apk_paths, "iterable<str> : List of apk files (paths)")

    def import_apks(self, copy_apk = False, copy_to_mongodb = False, update = False, tag = None):
        ''' Import APKs.

        Create a storage entry and copy the apk if `copy_apk` and not already in the storage.

        Will also set the path of the `Apk`s (the directory to which it got imported)
        at least if `copy_apk` is true.

        Parameters
        ----------
        copy_apk : bool, optional (default is False)
            If true also import the apk file (copy it)
        copy_to_mongodb : bool, optional (default is False)
            Also import into MongoDB. Needed for the distributed analysis.
        update : bool, optional (default is False)
            Update apks that have already been imported.
        tag : str, optional (default is None)
            Tag the apks.

        Returns
        -------
        generator<Apk>
            The imported `Apk`s. Even if you don't want the result value,
            you have to force the generator to continue until it's empty to get the import process finished.
        '''
        # get apks from directory
        apk_gen = self.apk_paths
        for apk_abs_path in apk_gen:
            try:
                with open(apk_abs_path, "rb") as apk_fh:
                    # file-like object in memory
                    # avoids double loading of file (for hashing and copying)
                    apk_in_memory = BytesIO(apk_fh.read())
                    apk =  self.import_from_flo(apk_in_memory, apk_abs_path,
                                                # copy apk
                                                copy2disk=copy_apk, copy2mongodb=copy_to_mongodb,
                                                update = update, tag = tag)
                    yield apk
            except ApkImportError as e:
                log.warn(e)

    def import_from_flo(self, file_like_object, import_path_str = "file-like object", copy2disk = False, copy2mongodb = False, update = False, tag = None):
        '''
        Import an apk from a `file_like_object` if not already in the storage.

        Will also set the path (absolute) of the returned `Apk` (the directory to which it got imported)
        at least if `copy2disk` is true.
        Also sets the import date and tag.

        Parameters
        ----------
        file_like_object
        import_path_str : str, optional (default is "file-like object")
            Optional string which will be passed to the Exceptions if they get raised.
            Describes from which the import failed.
        copy2disk : bool, optional (default is False)
            If true also import the apk file (copy it)
        copy2mongodb : bool, optional (default is False)
            Also import into MongoDB. Needed for the distributed analysis.
        update : bool, optional (default is False)
            Update apks that have already been imported.
        tag : str, optional (default is None)
            Tag the apks.

        Raises
        ------
        ApkImportError

        Returns
        -------
        Apk
            If no error occurred.
        '''
        try:
            apk = FastApk.fast_load_from_io(file_like_object, import_path_str, calculate_hash = True)
            storage = self.storage

            def set_apk_meta(apk):
                apk.import_date = datetime.utcnow()
                apk.tag = tag

            # set apk meta
            set_apk_meta(apk)

            # set import path as new path for apk file
            # needed to have the correct path when creating entry !

            # copy to disk and/or db
            _id, file_path = storage.copy_apk(apk, file_like_object, copy2db = copy2mongodb, copy2fs = copy2disk)

            # set path where file has been copied to
            # otherwise use supplied path
            if copy2disk:
                apk.path = file_path

            # create entry in storage
            storage.create_entry_for_apk(apk, update, tag)

            return apk
        except (StorageException, IOError) as e:
            raise ApkImportError(e), None, sys.exc_info()[2]

    @staticmethod
    def get_apks_from_dir(apk_dir):
        '''
        Get a list of apk files from the given directory (recursive).

        Parameters
        ----------
        apk_dir: str
            the directory from which to import the apk files

        Returns
        -------
        generator<str>
            Apk file names
        '''
        for dirpath, _, filenames in os.walk(apk_dir):
            filenames.sort()
            for _file in filenames:
                if ApkImporter.is_apk_file(_file):
                    yield join(dirpath, _file)

    @staticmethod
    def get_apks_from_list(apk_list):
        '''
        Filter the files in the list by checking if they have the APK file extension.

        Parameters
        ----------
        apk_paths : list<str>
            List of APK files

        Returns
        -------
        itertools.ifilter<str>
            Generator over apk files
        '''
        return itertools.ifilter(ApkImporter.is_apk_file, apk_list)

    @staticmethod
    def get_apks_from_list_or_dir(apks):
        ''' Get a list of apk files from directory or list by checking the .apk file extension.

        Parameters
        ----------
        apks: generator<str>
            List of directories or apk files.

        Returns
        -------
        generator<str>
            Path to Apks.

        Examples
        --------
        >>> from androlyze.loader.ApkImporter import ApkImporter
        >>> ApkImporter.get_apks_from_list_or_dir["foo.apk", "bar.apk"]
        >>> ApkImporter.get_apks_from_list_or_dir["foo/", "bar/"]
        >>> ApkImporter.get_apks_from_list_or_dir["foo.apk", "apk_dir/"]
        '''
        generators = []
        for apk in apks:
            apk_gen = None
            if isfile(apk):
                apk_gen = ApkImporter.get_apks_from_list([apk])
            elif isdir(apk):
                apk_gen = ApkImporter.get_apks_from_dir(apk)
            if apk_gen is not None:
                generators.append(apk_gen)
        return itertools.chain(*generators)

    @staticmethod
    def is_apk_file(filename):
        ''' Check if the `filename` has the .apk extension '''
        return fnmatch(filename, "*." + ANDROID_FILE_EXTENSION)
