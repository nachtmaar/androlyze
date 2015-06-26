
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androguard.core.bytecodes.apk import APK
from androlyze.model.android.Constants import COMPILED_APP_CODE
from androlyze.model.android.apk.Apk import Apk
from androlyze.util import Util
from datetime import datetime

class EAndroApk(Apk, APK):
    ''' Extends the androguard `APK` class with a sha256 hash function and implements the `Apk` interface.'''

    def __init__(self, *args, **kwargs):
        ''' Has the same parameters as the superclass.

        Other Parameters
        ----------
        tag : str, optional (default is None)

        Raises
        ------
        BadZipfile
        struct.error
        '''
        kwargs["zipmodule"] = 2
        APK.__init__(self, *args, **kwargs)

        if kwargs.get("raw", None) is None:
            # don't use raw data as path
            self.path = None

        Apk.__init__(self)

        self._hash = None
        self.import_date = None
        self.tag = kwargs.get("tag", None)

    def __eq__(self, other):
        if isinstance(other, EAndroApk):
            return self is other or self.hash == other.hash
        return False

    def get_path(self):
        return self.filename

    def get_package_name(self):
        return self.get_package()

    def get_version_name(self):
        return self.get_androidversion_name()

    def set_path(self, value):
        self.filename = value

    def set_package_name(self, value):
        self.package = value

    def set_version_name(self, value):
        self.androidversion["Name"] = value

    def del_path(self):
        del self.filename

    def del_package_name(self):
        del self.package

    def del_version_name(self):
        del self.androidversion["Name"]

    def get_import_date(self):
        return self._import_date

    def set_import_date(self, value):
        self._import_date = value

    def del_import_date(self):
        del self._import_date

    def get_hash(self):
        ''' Get the sha256 message digest of the APK file.
        The hash will be computed from memory.
        '''
        if self._hash is None:
            self._hash = Util.sha256(self.get_raw())
        return self._hash

    def get_tag(self):
        return self._tag

    def set_tag(self, value):
        self._tag = value

    def del_tag(self):
        del self._tag

    def get_size_app_code(self):
        ''' Get size of app code on demand (uncompressed .dex) file '''
        if self._size_app_code == 0:
            file_size = self.zip.getinfo(COMPILED_APP_CODE).file_size
            self.size_app_code = file_size
        return self._size_app_code

    def get_build_date(self):
        ''' Get the date of the classes.dex file (build date).
        
        Returns
        -------
        datetime.datetime
            The build date.
        '''
        return datetime(*self.zip.getinfo(COMPILED_APP_CODE).date_time)
    
    path = property(get_path, set_path, del_path, "str - path to apk file")
    package_name = property(get_package_name, set_package_name, del_package_name, "str - unique apk identifier (at least in the store)")
    version_name = property(get_version_name, set_version_name, del_version_name, "str - version")
    hash = property(get_hash, lambda s, v: s.set_hash(v), lambda s: s.del_hash(), "str - sha256 of raw apk file (hexstring)")
    import_date = property(get_import_date, set_import_date, del_import_date, " datetime.datetime : the import date (default is None)")
    tag = property(get_tag, set_tag, del_tag, "str : some tag")
    size_app_code = property(get_size_app_code, lambda s, v: s.set_size_app_code(v), lambda s: s.del_size_app_code(), "int : size of the uncompressed .dex file")
    build_date = property(get_build_date, lambda s, v: s.set_build_date(v), lambda s: s.del_build_date(), "datetime.dateime : build date (inferred from classes.dex timestamp)")

if __name__ == '__main__':
    # APK_NAME = "/home/nils/projects/thesis/a2dp.Vol.apk"

    # this file shows a problem, it doesn't have the android namespace, but ns0 instead
    #APK_NAME = "/home/nils/projects/thesis/android/apks/com.keyc.android.weather.apk"
    APK_NAME = "/mnt/stuff/androlyze/import/apk/com.whatsapp/2.7.3581/071435b4c72d45593ba64d411463ad18e02cbd3d90296d38f5b42d7e9d96ea9b/com.whatsapp_2.7.3581.apk"

    a = EAndroApk(APK_NAME)
    a.tag = "some tag"
    print a
