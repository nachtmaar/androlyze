
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze import action_query_result_db
from androlyze.error import AndroLyzeLabError
from androlyze.log.Log import clilog


class DBLyze(object):
    ''' This is the base class for all `DBLyze` scripts.
    It gives direct access to the `RedundantStorage` object.
    Therefore direct access to the result backend.
    
    Sublcasses are intended for the evaluation part of the analysis.
    
    See :py:method:`.SharedPreferences`
    '''

    # Set the script type here on which the evaluation shall be performed!
    ON_SCRIPT = None    
    
    def __init__(self):
        '''
        Attributes
        ----------
        script_name : str
            The name of the script which shall be evaluated
        version: str
            The version of the script which shall be evaluated
        storage : RedundantStorage
            The storage object, containing the result backend access.
        '''
        if self.ON_SCRIPT is None:
            raise AndroLyzeLabError("You have to set the 'ON_SCRIPT' variable in your DBLyze script!")
        
        self.script_name = self.ON_SCRIPT.__name__
        self.version = self.ON_SCRIPT.VERSION
        self.storage = None
        
    def evaluate(self, storage, *args, **kwargs):
        self.storage = storage
        clilog.info("evaluating '%s' version: %s", self.script_name, self.version)
        return self._evaluate(storage, *args, **kwargs)
    
    def _evaluate(self, storage):    
        ''' Implement this method to perform the evaluation on the result backend '''
        raise NotImplementedError
    
    def action_query_result_db(self, *args, **kwargs):
        ''' Specialized version of :py:method:`androlyze.action_query_result_db` which sets the script version and name automatically '''
        kwargs.update({'script_name' : self.script_name, 'script_version' : self.version})
        return action_query_result_db(self.storage, *args, **kwargs)
    