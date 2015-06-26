
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

class CustomResultObjInterface:
    ''' Interface that defines for custom result objects how their results will be stored '''

    def get_custom_result_obj_repr(self):
        ''' Return the data that shall be stored '''
        raise NotImplementedError