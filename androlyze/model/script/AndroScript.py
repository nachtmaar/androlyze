
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from datetime import datetime

from androlyze.analyze.exception import AndroScriptError
from androlyze.log.Log import log
from androlyze.model.Resetable import Resetable
from androlyze.model.analysis.result.ResultObject import ResultObject
from androlyze.model.analysis.result.StaticResultKeys import *
from androlyze.model.script import ScriptUtil
from androlyze.storage.Constants import JSON_FILE_EXT
from androlyze.util.Util import timeit, sha256

class AndroScript(object, Resetable, Hashable):
    '''
    Base class for `androguard` scripts which offers a consistent way of logging the analysis results
    with the help of the :py:class:`~ResultObject`

    If you don't want json data as output you can use a different object for result logging.
    See :py:meth:`.AndroScript.custom_result_object`.

    Overwrite the `_analyze` function to write your custom script!
    Also set the options your script needs.

    See the methods prefixed with `needs`.

    Be sure to specify the script version with the `VERSION` variable!

    You can test your script with the `test` method.
    This helps to find errors and unregistered keys very fast.
    '''

    # Set your script version!
    VERSION = None

    def __init__(self):
        Hashable.__init__(self)

        self.__name = self.__class__.__name__

        self.reset()

    def __str__(self):
        if self.VERSION:
            return '%s %s' % (self.name, self.VERSION)
        return self.name

    def __repr__(self):
        return "%s" % (self.name)

    def __cmp__(self, other):
        if isinstance(other, AndroScript):
            return cmp(self.name, other.name)
        return 1

    def get_cres(self):
        return self.__cres

    def set_cres(self, value):
        self.__cres = value

    def del_cres(self):
        del self.__cres

    def get_res(self):
        return self.__res

    def set_res(self, value):
        self.__res = value

    def del_res(self):
        del self.__res

    def get_name(self):
        return self.__name

    def set_name(self, value):
        self.__name = value

    def del_name(self):
        del self.__name

    def get_file_name_ext(self):
        return self.__file_name_ext

    def set_file_name_ext(self, value):
        self.__file_name_ext = value

    def del_file_name_ext(self):
        del self.__file_name_ext

    file_name_ext = property(get_file_name_ext, set_file_name_ext, del_file_name_ext, "str, optional (default is `JSON_FILE_EXT`) : The file name extension.")
    res = property(get_res, set_res, del_res, "ResultObject : keeps the analysis results")
    cres = property(get_cres, set_cres, del_cres, "object, optional (default is None) : Custom result object for logging")
    name = property(get_name, set_name, del_name, "str : the name of the script (class name)")

    def analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        '''
        Analyze the given `EAndroApk` and return the `ResultObject`.

        Parameters
        ----------
        apk: EAndroApk
        dalvik_vm_format: DalvikVMFormat
            Parsed .dex file.
            Only available if `needs_dalvik_vm_format` returns True.
        vm_analysis: VMAnalysis
            Dex analyzer.
            Only available if `needs_vmanalysis` returns True.
        gvm_analysis : GVMAnalysis

        Other Parameters
        ----------------
        log_script_meta : bool, optional (default is True)
            Can be used to disable logging of script meta infos at all.
            Otherwise they will be logged only once.

        Returns
        -------
        ResultObject

        Raises
        ------
        NotImplementedError
            If `AndroScript.VERSION` not specified
        '''
        res = self.res
        log_script_meta = kwargs.get("log_script_meta", True)

        if log_script_meta:
            self._log_script_meta_before_act_run(res)

        # analyze and measure time
        time_s = timeit(self._analyze,
                        *((apk, dalvik_vm_format, vm_analysis, gvm_analysis) +  args),
                         **kwargs)

        if log_script_meta and self.create_script_stats():
            self._log_script_meta_after_act_run(res, time_s)

        return self.res

    ############################################################
    #---Implement these functions in a subclass
    ############################################################

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        '''
        Overwrite this function in apk subclass to build your own script!
        Use the `ResultObject` for logging.

        Parameters
        ----------
        apk: EAndroApk
        dalvik_vm_format: DalvikVMFormat
            Parsed .dex file.
            Only available if `needs_dalvik_vm_format` returns True.
        vm_analysis: VMAnalysis
            Dex analyzer.
            Only available if `needs_vmanalysis` returns True.
        gvm_analysis : GVMAnalysis
        '''
        raise NotImplementedError

    def custom_result_object(self):
        '''
        Overwrite this method, if you want to use your own result logging framework/object,
        You can supply it here and access it via `self.cres`.

        E.g. you could return ("", "txt") for simply logging with a string to a .txt file.

        The str representation of it will be stored!
        Automatically stores your data (str() of `self.cres`) in mongodb's gridfs.

        The `ResultObject` in `self.res` is still existing and internally used to log some meta information.

        Returns
        -------
        tuple<object, str>
            First argument is the result object you want to use,
            the second is the file name extension used for storage (without a leading point)
        '''
        raise NotImplementedError

    def reset(self):
        '''
        Reset the `AndroScript` so that it can be used for a new analysis.
        If you do a custom initialization in your script,
        you probably want do put the init code inside this method.

        Don't forget to call the super `reset` !
        '''
        # we need to (re)init the result object
        self.__res, self.__file_name_ext = ResultObject(None), JSON_FILE_EXT

        # custom result object
        try:
            self.__cres, self.__file_name_ext = self.custom_result_object()
        except NotImplementedError:
            self.__cres = None

    ############################################################
    #---Script requirements
    ############################################################

    def needs_dalvik_vm_format(self):
        ''' Gives access to the `DalvikVMFormat` object which is a parser for the classes.dex file '''
        return False

    def needs_vmanalysis(self):
        ''' Gives access to the `VMAnalysis` object which is a analyzer for the `DalvikVMFormat` object '''
        return False

    def needs_gvmanalysis(self):
        ''' Gives access to the `GVMAnalysis` object.
        Creates a graph which you can use for export (gexf etc) or do your custom stuff
        '''
        return False

    def needs_xref(self):
        ''' Create cross references. Automatically implies `needs_dalvik_vm_format`, `needs_vmanalysis` and `needs_gvmanalysis` '''
        return False

    def needs_dref(self):
        ''' Create data references. Automatically implies `needs_dalvik_vm_format`, `needs_vmanalysis` and `needs_gvmanalysis` '''
        return False

    ############################################################
    #---Options
    ############################################################

    def create_script_stats(self):
        ''' If true, create some script statistics and
        write them into the `ResultObject` '''
        return False

    def is_big_res(self):
        ''' Return true, if your result may exceed 16mb.
        This will store your data (str() of `self.cres`) in mongodb's gridfs.

        You don't need to return true, if you're using a different result object! (see :py:meth:`.custom_result_object`)
        This will be done automatically.
        '''
        return False

    ############################################################
    #---Testing stuff
    ############################################################

    @staticmethod
    def test(script, apk_paths):
        '''
        Use this function to develop and test your script.

        E.g. find unregistered keys and other errors.

        Parameters
        ----------
        script : type
            The reference to the script which shall be tested (not instantiated!)
        apk_paths : iterable<str>
            Paths to apks

        Examples
        --------
        >>> for res in AndroScript.test(ClassDetails, ["../../../testenv/apks/a2dp.Vol.apk"]):
        ...     # get result object
        ...     print res
        ...     # get json
        ...     print res.write_to_json()

        Returns
        -------
        list<ResultObject>
            The `ResultObject` for every analyzed apk
        '''
        # no circular import
        from androlyze.analyze.Analyzer import Analyzer

        res = []
        try:
            # init scripts to get options
            inst_script_list = ScriptUtil.instantiate_scripts([script])
            script_options = ScriptUtil.get_minimum_script_options(inst_script_list)

            script_list = [script]
            # options: storage, script_list, script_hashes, min_script_needs, apks_or_paths
            # but the analyzer needs the scripts uninitialized!
            ana = Analyzer(None, script_list, None, script_options, apk_paths)
            res = ana.analyze(test = True)
        except AndroScriptError as e:
            log.exception(e)

        return res

    ############################################################
    #---Script meta logging
    ############################################################

    def _log_script_meta_before_act_run(self, res, *args, **kwargs):
        ''' Log script meta infos before actual script run '''
        if self.VERSION is None:
            raise NotImplementedError("You need to define the version of your script!")

        res.register_keys([RESOBJ_SCRIPT_META_NAME, RESOBJ_SCRIPT_META_HASH, RESOBJ_SCRIPT_META_ANALYSIS_DATE, RESOBJ_SCRIPT_META_VERSION], RESOBJ_SCRIPT_META)
        res.log(RESOBJ_SCRIPT_META_NAME, self.name, RESOBJ_SCRIPT_META)
        res.log(self.KEY_HASH, self.hash, RESOBJ_SCRIPT_META)
        res.log(RESOBJ_SCRIPT_META_VERSION, self.VERSION, RESOBJ_SCRIPT_META)

        # add analysis date
        res.log(RESOBJ_SCRIPT_META_ANALYSIS_DATE, datetime.utcnow(), RESOBJ_SCRIPT_META)

    def _log_script_meta_after_act_run(self, res, time_s, *args, **kwargs):
        ''' Log script meta infos after actual script run '''
        # log time
        res.register_keys([RESOBJ_SCRIPT_META_TIME_SCRIPT], RESOBJ_SCRIPT_META)
        res.log(RESOBJ_SCRIPT_META_TIME_SCRIPT, time_s, RESOBJ_SCRIPT_META)

    ############################################################
    #---Other
    ############################################################

    def uses_custom_result_object(self):
        ''' Check if the script uses a custom result object for logging '''
        return self.cres is not None

    def add_apk_androguard_analyze_time(self, seconds):
        ''' Add the androguard analyze time to the `ResultObject`.
        This is also a good moment to calculate the complete time. '''
        if self.create_script_stats():
            res = self.res

            # log androguard open time
            res.register_keys([RESOBJ_SCRIPT_META_ANALYZE_TIME, RESOBJ_SCRIPT_META_TIME_TOTAL], RESOBJ_SCRIPT_META)
            res.log(RESOBJ_SCRIPT_META_ANALYZE_TIME, seconds, RESOBJ_SCRIPT_META)

            # log total time
            total_time = seconds + res[RESOBJ_SCRIPT_META][RESOBJ_SCRIPT_META_TIME_SCRIPT]
            res.log(RESOBJ_SCRIPT_META_TIME_TOTAL, total_time, RESOBJ_SCRIPT_META)

    def result_dict(self, gen_id = False):
        ''' Returns an `OrderedDict` holding information about the analyzed `Apk` as well as the script,
        as well as eventually user logged infos.

        Parameters
        ----------
        gen_id : bool, optional (default is False)
            Generate an id = sha256(apk hash + script name)
            and store it under the "_id" key.

        Returns
        -------
        OrderedDict
        '''
        res_dict = self.res.description_dict()
        if gen_id:
            res_dict[RESOBJ_ID] = self.gen_unique_id()
        return res_dict

    def gen_unique_id(self):
        ''' Generate an unique id = sha256(apk hash + script name) '''
        try:
            return sha256(self.res.apk.hash + self.name)
        except AttributeError:
            log.warn('Could not calculate unique id for %s', self)
            raise

    def get_file_name(self):
        ''' Get the file name used for storage '''
        apk = self.res.apk
        return '%s_%s_%s.%s' % (apk.package_name, apk.version_name, self.name, self.file_name_ext)

    @staticmethod
    def load_from_result_dict(res_dict, apk = None):
        '''
        Load an `AndroScript` from the `res_dict`.

        Parameters
        ----------
        res_dict : dict
            See `ResultObject.description_dict`
        apk : Apk, optional (default is None)
            Link to `ResultObject` to `apk`
        '''
        ascript = AndroScript()

        ascript.name = res_dict[RESOBJ_SCRIPT_META][RESOBJ_SCRIPT_META_NAME]
        ascript.hash = res_dict[RESOBJ_SCRIPT_META][RESOBJ_SCRIPT_META_HASH]
        result_object = ResultObject()
        result_object.results = res_dict
        ascript.res = result_object

        # link to apk
        ascript.res.apk = apk

        return ascript
