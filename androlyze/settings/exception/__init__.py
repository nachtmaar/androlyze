
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.error.WrapperException import WrapperException
from androlyze.loader.exception import CouldNotOpenFile

class ConfigError(WrapperException):
    ''' Base exception class for errors related to the config '''
    pass

class ConfigFileNotFoundError(ConfigError):
    ''' Exception for the case that a config file could not be opened '''

    def __init__(self, file_path, *args, **kwargs):
        '''
        Parameters
        ----------
        file_path : str
            The path to the config file.
        caused_by : Exception
        '''
        super(ConfigFileNotFoundError, self).__init__(*args, **kwargs)
        self.file_path = file_path

    def _msg(self):
        return "Could not open config file: %s" % self.file_path
