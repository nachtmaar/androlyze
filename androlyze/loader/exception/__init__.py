
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Loader exceptions
'''

from androlyze.error.WrapperException import WrapperException
from androlyze.model.android.Constants import MANIFEST_FILENAME
from androlyze.error.AndroLyzeLabError import AndroLyzeLabError

############################################################
#---Apk
############################################################

class ApkImportError(WrapperException):
    ''' Base class for import errors '''
    pass

class CouldNotOpenFile(ApkImportError):

    def __init__(self, file_path, caused_by = None):
        '''
        Parameters
        ----------
        file_path : str
            The path to the file that could not be opened.
        caused_by : Exception
        '''
        super(CouldNotOpenFile, self).__init__(caused_by = caused_by)
        self.file_path = file_path

    def _msg(self):
        return 'Could not open file: %s' % self.file_path

class CouldNotOpenApk(CouldNotOpenFile):

    def _msg(self):
        return 'Could not open apk file: %s' % self.file_path


class CouldNotOpenManifest(CouldNotOpenFile):

    def _msg(self):
        return 'Could not open %s from file: %s' % (MANIFEST_FILENAME, self.file_path)

############################################################
#---AndroScript
############################################################

class NoAndroScriptSubclass(AndroLyzeLabError):

    def __init__(self, class_name):
        Exception.__init__(self)
        self._class_name = class_name

    def __str__(self):
        from androlyze.model.script import AndroScript
        return "%s is no subclass of %s !" % (self._class_name, AndroScript.__name__)

class ModuleClassNameException(AndroLyzeLabError):
    ''' Exception for the case that the module does not have the specified class '''

    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name

    def __str__(self):
        return 'The module "%s" does not have the specified class "%s"!' % (self.module_name, self.class_name)

class ModuleNotSameClassNameException(ModuleClassNameException):
    ''' Exception for the case that the module has a different name than the class '''

    def __str__(self):
        return super(ModuleNotSameClassNameException, self).__str__() + ' The module name has to equal the class name !'
