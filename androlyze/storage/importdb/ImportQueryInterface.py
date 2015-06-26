
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

# database structure constants
TABLE_APK_IMPORT = "apk_import"
TABLE_APK_IMPORT_KEY_HASH = "hash"
TABLE_APK_IMPORT_KEY_PACKAGE_NAME = "package_name"
TABLE_APK_IMPORT_KEY_VERSION_NAME = "version_name"
TABLE_APK_IMPORT_KEY_PATH = "path"
TABLE_APK_IMPORT_KEY_IMPORT_DATE = "import_date"
TABLE_APK_IMPORT_KEY_TAG = "tag"
TABLE_APK_IMPORT_KEY_SIZE_APP_CODE = "size_app_code"
TABLE_APK_IMPORT_KEY_BUILD_DATE = "build_date"
TABLE_APK_IMPORT_KEYS = set([TABLE_APK_IMPORT_KEY_HASH, TABLE_APK_IMPORT_KEY_PACKAGE_NAME,
                         TABLE_APK_IMPORT_KEY_VERSION_NAME, TABLE_APK_IMPORT_KEY_PATH,
                         TABLE_APK_IMPORT_KEY_IMPORT_DATE, TABLE_APK_IMPORT_KEY_TAG,
                         TABLE_APK_IMPORT_KEY_SIZE_APP_CODE, TABLE_APK_IMPORT_KEY_BUILD_DATE
                         ])

class ImportQueryInterface:
    ''' Interface for querying the import database.
    All methods may raise an `ImportQueryError` in the case of an error.

    Filtering can be done via some of these properties (in this order):
        hashes
        package names
        tags

    Only one of the filter arguments will be used!
    '''


    def get_imported_apks(self, hashes = None, package_names = None, tags = None, **kwargs):
        '''
        Get the imported `Apk`s (sorted by package name and version).
        If neither `hashes` nor `package_names` nor `tags` are given,
        return all imported `Apk`s.

        Only one of the filter arguments will be used.

        Preferred order is: hashes, package_names, tags.

        Parameters
        ----------
        hashes : iterable<str>, optional (default is None)
        package_names : iterable<str>, optional (default is None)
        tags : iterable<str>, optional (default is None)

        Other Parameters
        ----------------
        order_by : str, optional (default is None)
            Means order by package name.
            Has to be one of the keys in `TABLE_APK_IMPORT_KEYS`.
        ascending : bool, optional (default is True)
            Sort ascending.

        Raises
        ------
        ImportQueryError

        Returns
        -------
        generator<FastApk>
        '''
        raise NotImplementedError

    def get_versions(self, hashes = None, package_names = None, tags = None):
        '''
        Get the imported versions.

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
        raise NotImplementedError

    def get_apk_hashes(self, package_names = None, tags = None):
        '''
        Get the imported hashes (sorted by package name and version).
        If neither `package_names` nor `tags` are given,
        return all hashes.

        Only one of the filter arguments will be used.

        Preferred order is: package_names, tags.

        Parameters
        ----------
        package_names : iterable<str>, optional (default is None)
            The package names for which to get the hash(es).
            If not given, return all hashes.
        tags : iterable<str>, optional (default is None)

        Raises
        ------
        ImportQueryError

        Returns
        -------
        generator<str>
        '''
        raise NotImplementedError

    def get_apk_package_names(self, hashes = None, tags = None):
        '''
        Get the package names.

        Parameters
        ----------
        hashes : iterable<str>, optional (default is None)
        tags : iterable<str>, optional (default is None)
            Filter package names which have one of the specified `tags`.
            If not given, don't filter at all.

        Raises
        ------
        ImportQueryError

        Returns
        -------
        generator<str>
        '''
        raise NotImplementedError

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
        raise NotImplementedError