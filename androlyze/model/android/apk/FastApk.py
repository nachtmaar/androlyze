
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys
from xml.dom import minidom

from androlyze.loader.exception import CouldNotOpenApk, CouldNotOpenManifest
from androlyze.model.android.Constants import MANIFEST_FILENAME, MANIFEST_NS, \
    MANIFEST_VERSION_NAME, MANIFEST_PACKAGE, MANIFEST_TAG_NAME, COMPILED_APP_CODE
from androlyze.model.android.apk.Apk import Apk
from androlyze.util import Util
from androlyze.model.analysis.result.StaticResultKeys import RESOBJ_APK_META,\
    RESOBJ_APK_META_PACKAGE_NAME, RESOBJ_APK_META_VERSION_NAME,\
    RESOBJ_APK_META_PATH, RESOBJ_APK_META_HASH, RESOBJ_APK_META_IMPORT_DATE,\
    RESOBJ_APK_META_TAG, RESOBJ_APK_META_BUILD_DATE
from datetime import datetime

class FastApk(Apk, object):
    '''
    Provides a fast way to access the basic attributes of an APK file.

    See Also
    --------
    http://developer.android.com/guide/topics/manifest/manifest-intro.html
    '''

    def __init__(self, package_name, version_name, path = None, _hash = None, import_date = None, tag = None, size_app_code = 0, build_date = None):
        ''' Create an apk instance. If the sha digest is not given,
        it will be calculated by loading the file at the time of the first retrieval. '''
        Apk.__init__(self)

        self.package_name = package_name
        self.version_name = version_name
        self.import_date = import_date
        self.tag = tag
        self.hash = _hash
        self.path = path
        self.size_app_code = size_app_code
        self.build_date = build_date

    def __eq__(self, other):
        if isinstance(other, FastApk):
            return self is other or self.hash == other.hash
        return False

    ############################################################
    #--- Other
    ############################################################

    @staticmethod
    def androguard_load_from_path(apk_file_path):
        ''' Load a FastApk from path with the help of androguard.

        Notes
        -----
        Androguard cannot read data properly from manifest files which do not have the android prefix.

        Parameters
        ----------
        apk_file_path: str
            path of apk

        Returns
        -------
        apk: FastApk
        '''
        from androguard.core.bytecodes import apk as androapk
        aapk = androapk.APK(apk_file_path)
        return FastApk(aapk.get_package(), aapk.get_androidversion_name(), apk_file_path)

    @staticmethod
    def fast_load_from_io(file_like_object = None, apk_file_path = None, calculate_hash = True):
        ''' Load a FastApk from file-like object or path by unzipping only the manifest file
        and calculating the hash.

        Parameters
        ----------
        file_like_object : file-like-object, optional (default is None)
            A file-like obj that points to the apk.
            If non given, try to open a file_like_object from the given `apk_file_path`.
        apk_file_path: str, optional (default is "not set")
            Path of apk
        calculate_hash : bool
            If true calculate the hash.
            This means the file has be to loaded completely into memory.
            If False, the hash will be calculated the first time it gets retrieved.

        Returns
        -------
        apk: FastApk

        Raises
        ------
        CouldNotOpenApk
            If the apk file could not be opened
        CouldNotReadManifest
            If the manifest file could not be read
        '''
        from androguard.core.bytecodes import apk as androapk
        from androguard.patch import zipfile

        # apk will be loaded from `flo` variable
        flo = file_like_object

        # indicates if file has been opened from path
        file_open_from_path = False
        # no file_like_object given, open file from path
        if file_like_object is None and isinstance(apk_file_path, str):
            try:
                flo = open(apk_file_path, "rb")
                file_open_from_path = True
            except IOError as e:
                flo.close()
                raise CouldNotOpenApk(apk_file_path, e), None, sys.exc_info()[2]

        # if file path not set, show at least that it's not seen in the exceptions
        if apk_file_path is None:
            apk_file_path = "not set"

        # load apk into memory and calculate hash if option set
        flo.seek(0)
        _hash = None
        if calculate_hash:
            data = flo.read()
            # calculate hash
            _hash = Util.sha256(data)
            flo.seek(0)

        try:
            if zipfile.is_zipfile(flo):
                z = zipfile.ZipFile(flo)
                # only read manifest from zip file
                binary_manifest = z.read(MANIFEST_FILENAME)
                ap = androapk.AXMLPrinter(binary_manifest)
                dom = minidom.parseString(ap.get_buff())
                manifest_tag = dom.getElementsByTagName(MANIFEST_TAG_NAME)
                # check that manifest tag is available
                if len(manifest_tag) > 0:
                    
                    # get size of uncompresses .dex file
                    size_app_code = z.getinfo(COMPILED_APP_CODE).file_size
                    # get build date (last timestamp of classes.dex in zipfile)
                    build_date = datetime(
                                          # use tuple from zipfile and pass the unpacked content to the constructor
                                          *z.getinfo(COMPILED_APP_CODE).date_time
                                          )
                    
                    
                    manifest_items = manifest_tag[0].attributes
                    # use the namespace to ignore wrong prefixes like "ns0"
                    version_name = manifest_items.getNamedItemNS(MANIFEST_NS, MANIFEST_VERSION_NAME).nodeValue
                    package = manifest_items.getNamedItem(MANIFEST_PACKAGE).nodeValue
                    return FastApk(package, version_name, path = apk_file_path, _hash = _hash, size_app_code = size_app_code, build_date = build_date)
            raise CouldNotOpenManifest(apk_file_path), None, sys.exc_info()[2]
        except Exception as e:
            raise CouldNotOpenApk(apk_file_path, caused_by = e), None, sys.exc_info()[2]
        finally:
            # close file if manually opened from path
            if file_open_from_path:
                flo.close()

    @staticmethod
    def androguard_load_from_io(file_like_object = None, apk_file_path = None, calculate_hash = True):
        ''' Load a FastApk from file-like object or path by using `androgaurd`.
        Parameters
        ----------
        file_like_object : file-like-object, optional (default is None)
            A file-like obj that points to the apk.
            If non given, try to open a file_like_object from the given `apk_file_path`.
        apk_file_path: str, optional (default is "not set")
            Path of apk
        calculate_hash : bool
            If true calculate the hash.
            This means the file has be to loaded completely into memory.
            If False, the hash will be calculated the first time it gets retrieved.

        Returns
        -------
        apk: FastApk

        Raises
        ------
        CouldNotOpenApk
            If the apk file could not be opened
        '''
        # prevent circular import
        from androlyze.analyze import AnalyzeUtil

        # apk will be loaded from `flo` variable
        flo = file_like_object

        # indicates if file has been opened from path
        file_open_from_path = False
        # no file_like_object given, open file from path
        if file_like_object is None and isinstance(apk_file_path, str):
            try:
                flo = open(apk_file_path, "rb")
                file_open_from_path = True
            except IOError as e:
                flo.close()
                raise CouldNotOpenApk(apk_file_path, e), None, sys.exc_info()[2]

        # if file path not set, show at least that it's not seen in the exceptions
        if apk_file_path is None:
            apk_file_path = "not set"

        # load apk into memory and calculate hash if option set
        flo.seek(0)
        _hash = None
        data = flo.read()
        if calculate_hash:
            # calculate hash
            _hash = Util.sha256(data)
            flo.seek(0)

        apk = AnalyzeUtil.open_apk(data, raw = True, path = apk_file_path)

        if file_open_from_path:
            flo.close()

        if apk is not None:
            try:
                return FastApk.load_from_eandroapk(apk)
            except KeyError:
                pass

        # could not open apk -> raise error
        raise CouldNotOpenApk(file_path = apk_file_path)


    @staticmethod
    def load_from_androguard_apk(andro_apk):
        '''
        Load a `FastApk` from androguard `APK`

        Parameters
        ----------
        andro_apk: APK (androguard apk)

        Returns
        -------
        FastApk
        '''
        return FastApk(andro_apk.get_package(), andro_apk.get_androidversion_name(), andro_apk.filename)

    @staticmethod
    def load_from_eandroapk(eandro_apk):
        '''
        Load a `FastApk` from an `EAndroApk`.

        Parameters
        ----------
        eandro_apk: EAndroApk

        Returns
        -------
        FastApk
        '''
        return FastApk(eandro_apk.package_name, eandro_apk.version_name, path = eandro_apk.path, _hash = eandro_apk.hash, import_date = eandro_apk.import_date, tag = eandro_apk.tag, size_app_code = eandro_apk.size_app_code, build_date = eandro_apk.build_date)

    @staticmethod
    def load_from_result_dict(res_dict):
        '''
        Load a `FastApk` from the `res_dict`.

        Parameters
        ----------
        res_dict : dict
            See `ResultObject.description_dict`
        '''
        package_name = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_PACKAGE_NAME]
        version_name = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_VERSION_NAME]
        path = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_PATH]
        _hash = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_HASH]
        import_date = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_IMPORT_DATE]
        tag = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_TAG]
        build_date = res_dict[RESOBJ_APK_META][RESOBJ_APK_META_BUILD_DATE]
        return FastApk(package_name, version_name, path, _hash, import_date, tag, build_date = build_date)

if __name__ == '__main__':
    import json
    from androlyze.log.Log import log

    #from androlyze.model.script.AndroScript import AndroScript

    #APK_NAME = "/mnt/stuff/android/apks/com.parkdroid.apk"
    APK_NAME = "/mnt/stuff/androlyze/import/apk/com.whatsapp/2.7.3581/071435b4c72d45593ba64d411463ad18e02cbd3d90296d38f5b42d7e9d96ea9b/com.whatsapp_2.7.3581.apk"
    try:
        with open(APK_NAME, "rb") as f:
            print FastApk.fast_load_from_io(file_like_object = f)

        apk = FastApk.fast_load_from_io(file_like_object = None, apk_file_path = APK_NAME)
        apk.tag = "exploitable"
        print apk
        print json.dumps(apk.meta_dict(), indent = 4)

        print apk
        #res.log_true("check1", "checks")
        #res.log_true("check2", "checks")
        #storage.store_result_for_apk(apk, AndroScript("script1"), res)
        # androguard cannot load some apk files which the fast loader can
    except Exception as e:
        log.exception(e)
    print "done"
