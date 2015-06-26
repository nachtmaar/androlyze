
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script.AndroScript import AndroScript

# TODO: RENAME THE SCRIPT AND MODULE NAME!!
from androlyze.model.script.dblyze.DBLyze import DBLyze
from pprint import pprint

class ScriptTemplate(AndroScript):
    ''' Template for writing a custom `AndroScript` '''

    VERSION = "0.1"

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
        # TODO: CUSTOMIZE

        #categories
        CAT_FILES = "files"

        res = self.res

        res.register_keys([CAT_FILES])

        # files
        res.log(CAT_FILES, apk.get_files())

    def custom_result_object(self):
        '''
        Overwrite this method, if you want to use your own result logging framework/object,
        You can supply it here and access it via `self.cres`.

        E.g. you could return ("", "txt") for simply logging with a string to a .txt file.

        The str representation of it will be stored!


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
        super(ScriptTemplate, self).reset()

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
        ''' Create cross references '''
        return False

    def needs_dref(self):
        ''' Create data references '''
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

class Eval(DBLyze):

    # Evaluate ScripTemplate
    ON_SCRIPT = ScriptTemplate

    def _evaluate(self, storage):
        '''
        Evaluate the script results.

        Parameters
        ----------
        storage : RedundantStorage
        '''

        # Use either the AndroLyze query API:

        # iterate over the results (one result per APK = iteration)
        for ordered_dict in self.action_query_result_db():
            # do something else than just printing the dictionary
            #pprint(dict(ordered_dict))
            pass

        # Or perform a direct query on the mongodb API:

        # get the mongodb singleton
        mongodb = storage.result_db_storage
        for ordered_dict in mongodb.get_res_coll().find({"script meta.name" : "ScriptTemplate"}, {"apk meta" : 1}):
            pprint(dict(ordered_dict))

# testing code
if __name__ == '__main__':
    for res in AndroScript.test(ScriptTemplate, ["../../../../testenv/apks/a2dp.Vol.apk"]):
        print res
        print res.write_to_json()