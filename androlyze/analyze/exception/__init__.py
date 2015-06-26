
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.error.WrapperException import WrapperException

class AnalyzeError(WrapperException):
    ''' Base class for an analyze error '''
    pass

class AndroScriptError(AnalyzeError):
    ''' Exception for the case than an `AndroScript` causes an error '''

    def __init__(self, androscript, caused_by = None, additional_text = ''):
        '''
        Parameters
        ----------
        androscript : AndroScript
            The Script which caused the error
        caused_by : Exception, optional (default is None)
            The error that appeared.
        additional_text : str, optional (default is False)
        '''
        AnalyzeError.__init__(self, caused_by = caused_by)
        self.androscript = androscript
        self.additional_text = additional_text

    def _msg(self):
        return 'The script %s caused an error.%s' % (self.androscript, self.additional_text)

class DexError(AnalyzeError):
    ''' Exception for dex related stuff '''
    pass