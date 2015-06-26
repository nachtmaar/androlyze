
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.log.Log import log
from androlyze.storage.resultdb import ResultDatabaseStorage
from androlyze.storage.s3 import S3Storage

def get_apk_storage(settings):
    ''' Get an object implementing the `ApkCopyInterface`.
    
    Parameters
    ----------
    settings : Settings
    '''
    import androlyze.settings as s
    storage_engine = settings.get_apk_storage_engine()
    log.warn("Using APK storage: %s" % storage_engine)
    
    if storage_engine == s.SECTION_S3_STORAGE:
        return S3Storage.factory_from_config(settings)
    elif storage_engine == s.SECTION_RESULT_DB:
        return ResultDatabaseStorage.factory_from_config(settings)
    else:
        raise RuntimeError("No Storage engine defined! But requested!")