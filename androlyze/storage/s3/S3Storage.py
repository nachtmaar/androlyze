
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from io import BytesIO
from pprint import pprint
import re
import sys

from boto.exception import BotoClientError, S3ResponseError
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from androlyze.analyze import AnalyzeUtil
from androlyze.log.Log import log
from androlyze.model.analysis.result.StaticResultKeys import RESOBJ_APK_META
from androlyze.storage import Util
from androlyze.storage.apk.ApkCopyInterface import ApkCopyInterface
from androlyze.storage.exception import S3StorageOpenError, \
    S3StorageStoreException, S3StorageLoadException


class S3Storage(object, ApkCopyInterface):

    def __init__(self, aws_id, aws_key, aws_bucket_name, s3_hostname = None):
        '''
        Parameters
        ----------
        aws_id : str
            ID of the Amazon AWS account.
        aws_key : str
            Key of the Amazon AWS account.
        aws_bucket_name : str
            Bucket name where the APKs are stored.
        s3_hostname : str, optional (default is None)
            The URL for the S3 storage.
            E.g. "s3-eu-west-1.amazonaws.com"
        '''
        
        self._s3_conn = S3Connection(aws_id, aws_key, host=s3_hostname)
        self._apk_bucket_name = aws_bucket_name
        
        if "." in aws_bucket_name:
            raise RuntimeError("Do not use '.' inside the bucket name: '%s'" % aws_bucket_name)
        
        try:
            self._apk_bucket = self.s3_conn.get_bucket(self.apk_bucket_name)
            
            log.info("opening %s", self)
        except (BotoClientError, S3ResponseError) as e:
            raise S3StorageOpenError(self.apk_bucket_name, caused_by = e)

    def __str__(self, *args, **kwargs):
        return 'S3 bucket: %s' % self.apk_bucket_name
    
    def get_apk_bucket_name(self):
        return self._apk_bucket_name

    def set_apk_bucket_name(self, value):
        self._apk_bucket_name = value

    def del_apk_bucket_name(self):
        del self._apk_bucket_name
    
    def get_s3_conn(self):
        return self._s3_conn

    def set_s3_conn(self, value):
        self._s3_conn = value

    def del_s3_conn(self):
        del self._s3_conn

    def get_apk_bucket(self):
        return self._apk_bucket

    def set_apk_bucket(self, value):
        self._apk_bucket = value

    def del_apk_bucket(self):
        del self._apk_bucket

    s3_conn = property(get_s3_conn, set_s3_conn, del_s3_conn, "S3Connection : Connection to Amazon S3")
    apk_bucket = property(get_apk_bucket, set_apk_bucket, del_apk_bucket, "Bucket: APK bucket")
    apk_bucket_name = property(get_apk_bucket_name, set_apk_bucket_name, del_apk_bucket_name, "str: Name of the APK bucket")
    
    ############################################################
    #---Bucket stuff
    ############################################################
    
    def bucket_create(self, key, val, metadata_dict = {}):
        '''
        Create an object in the bucket, but only if not yet present (save traffic).
        
        Parameters
        ---------
        key : str
        val : file-like object 
        metadata_dict : dict
        
        Returns
        -------
        Key
        '''
        s3_key = Key(self.apk_bucket)
        
        s3_key.key = key
        # important: set metadata before actual upload
        s3_key.metadata = metadata_dict
        s3_key.content_type = 'application/vnd.android.package-archive'
        # upload
        log.debug("uploading %s", s3_key.key)
        s3_key.set_contents_from_file(val, replace = False)
        
        return s3_key
    
    def bucket_get(self, key):
        '''
        Get a `Key` object from S3 with the given `key`.
        
        Parameters
        ----------
        key: str
            Identifier of the object in the bucket
            
        Returns
        -------
        Key
        '''
        k = Key(self.apk_bucket)
        k.key = key
        
        return k
    
    @staticmethod
    def fmt_metadata(metadata): 
        '''
        Escape the dictionary suitable for boto.
        
        Parameters
        ----------
        metadata : dict
        '''
        def fmt(v):
            fallback = 'N/A'
            if v is None:
                return fallback
            return v
            
        metadata = Util.escape_dict(metadata,
                                fmt, 
                                escape_keys = False,
                                escape_values = True)
        
        metadata = Util.escape_dict(metadata,
                                lambda v: re.sub("\s+", "_", v), 
                                escape_keys = True,
                                escape_values = False)
        
        return metadata
        
    ############################################################
    #---ApkCopyInterface
    ############################################################
    
    def copy_apk(self, apk, file_like_obj, **kwargs):
        ''' See doc of :py:meth:`.ApkCopyInterface.copy_apk`. 

        Copy the apk into the S3 storage.
        
        Returns
        -------
        boto.s3.key.Key
            The stored object.
        '''
        file_like_obj.seek(0)
        # use path as id to simulate folder structure in S3
        _id = self.get_s3_id(apk) 
        try:
            metadata = self.fmt_metadata(apk.meta_dict()[RESOBJ_APK_META])
            key =  self.bucket_create(_id, file_like_obj, metadata)
            return key
        except (BotoClientError, S3ResponseError) as e:
            raise S3StorageStoreException(self, "apk: %s" % apk.short_description(), caused_by = e), None, sys.exc_info()[2]
    
    @staticmethod
    def get_s3_id(apk):
        '''
        Parameters
        ----------
        apk : Apk
        
        Returns
        -------
        str
            The id for the apk in the S3 storage
        '''
        return Util.get_apk_path_incl_filename(apk)
    
    def get_apk(self, _hash, apk = None, **kwargs):
        '''
        Get the `EAndroApk` from `_hash`.

        Parameters
        ----------
        _hash : str
            Hash of the .apk (sha256)
        apk : Apk
            Carries metainformation needed to build the whole path to the element in S3.

        Raises
        ------
        S3StorageLoadException

        Returns
        -------
        EAndroApk
            Apk constructed from raw data and meta infos.
        '''
        # use to hold apk meta infos
        #fast_apk = FastApk(package_name, version_name, path, _hash, import_date, tag)
        try:
            apk_raw = BytesIO()
            if apk is None:
                raise S3StorageLoadException(self, content = "Apk:%s" % apk.short_description(), caused_by = RuntimeError("No APK metainformation given!")), None, sys.exc_info()[2]
            _id = Util.get_apk_path_incl_filename(apk)
            self.bucket_get(_id).get_contents_to_file(apk_raw)
            apk_raw.seek(0)
            eandro_apk = AnalyzeUtil.open_apk(apk_raw.read(), None, raw = True)
            return eandro_apk 
        except (BotoClientError, S3ResponseError) as e:
            raise S3StorageLoadException(self, content = "Apk:%s" % apk.short_description(), caused_by = e), None, sys.exc_info()[2]

def factory_from_config(settings):
    ''' Get an `S3Storage` object` from the distributed config file.
    
    Parameters
    ----------
    settings : Settings
     '''
    from androlyze.celery.celerysettings import settings
    return S3Storage(*settings.get_s3_settings())
