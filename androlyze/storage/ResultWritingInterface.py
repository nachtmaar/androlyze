
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.model.script import ScriptUtil as ScriptUtil
from androlyze.model.script.CustomResultObjInterface import CustomResultObjInterface

class ResultWritingInterface:
    '''
    Interface for the writing of the analysis results.
    '''

    def store_result_for_apk(self, apk, script):
        ''' Store the `result` for the `apk` which has been analyzed with the `script`.

        Will overwrite already existing results of the `script` in the storage

        If a custom result object is used in `script` and it's not a `ResultObject`,
        str(custom res object) will be used for writing to disk.


        Parameters
        ----------
        apk: Apk
        script: AndroScript

        Raises
        ------
        StorageException

        Returns
        -------
        Dependent on the implementation
        '''
        raise NotImplementedError

    @staticmethod
    def get_custom_res_obj_representation(script):
        ''' Get the representation of the custom result object.
        This is the data repr. that shall stored '''
        cres = script.cres
        if isinstance(cres, CustomResultObjInterface):
            return cres.get_custom_result_obj_repr()
        elif ScriptUtil.is_result_object(cres):
            return cres.write_to_json()
        return str(cres)