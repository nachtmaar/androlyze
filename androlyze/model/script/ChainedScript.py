
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys

from androlyze.log.Log import log
from androlyze.model.script.AndroScript import AndroScript
from androlyze.util import Util
from androlyze.analyze.exception import AndroScriptError

CAT_ROOT = "ChainedScript"
CAT_SCRIPTS = "scripts"
CAT_SUCCESSFUL = "successful"
CAT_FAILURES = "failures"

class ChainedScript(AndroScript):
    ''' This script can be used to chain multiple `AndroScript`s together.
    This means that all scripts will run but you only get one result file.

    This allows you to split your scripts into smaller modules and combine them as you need.

    This works by supplying the `AndroScript`s
    which shall be chained via the `chain_scripts` method.

    See Also
    --------
    SampleChainScript : An example how to chain several scripts
    '''

    def __init__(self, androscripts = None, root_categories = (), name = None,
                   log_chained_script_meta_infos = True, continue_on_script_failure = True,
                   log_script_failure_exception = False, **kwargs):
        '''
        Parameters
        ----------
        androscripts : list<type<AndroScript>>, optional (default is [])
            List of references to the classes of the scripts to use (uninstantiated classes)
        root_categories : tuple<str>, optional (default is ())
            Categories under which you want to store the results of the scripts.
            Empty tuple means no category at all
        name : str, optional (default is class name)
            If given set the name of the created class.
        log_chained_script_meta_infos : bool, optional (default is False)
            Will be passed to the `ChainedScript` subclass.
            Meaning no meta information will be created from it (related to the chained scripts)
        continue_on_script_failure : bool, optional (default is True)
        log_script_failure_exception : bool, optional (default is False)


        Raises
        ------
        AndroScriptError
            If an error happened while setting the scripts.
        '''

        if androscripts is None:
            androscripts = []

        self.__androscripts = androscripts
        self.__root_categories = root_categories
        self.__log_chained_script_meta_infos = log_chained_script_meta_infos
        self.__continue_on_script_failure = continue_on_script_failure
        self.__log_script_failure_exception = log_script_failure_exception

        # call after instance variables have been set up because super also calls reset()
        super(ChainedScript, self).__init__()

        self.name = name or self.__class__.__name__

        # set scripts
        self.set_androscripts(self.__androscripts)

        # call after scripts have been initialized!
        self.reset()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%s)' % (self.name, self.chain_scripts())

    def get_androscripts(self):
        return self.__androscripts

    def set_androscripts(self, value):
        '''
        Raises
        ------
        AndroScriptError
            If an error happened while setting the scripts.
        '''
        for script in value:
            # script not initialized
            if isinstance(script, type):
                raise AndroScriptError(script, caused_by = None, additional_text = "The scripts needs to be initialized!")

        self.__androscripts = value

    def del_androscripts(self):
        del self.__androscripts

    androscripts = property(get_androscripts, set_androscripts, del_androscripts, "list<AndroScript> : List of scripts that will run")

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        ''' Analyze by running all `AndroScript`s '''

        # log script meta ?
        log_script_meta = kwargs.get("log_script_meta", True)
        # may be disabled! check!
        if not self.log_chained_script_meta_infos():
            log_script_meta = False

        # don't log script meta infos in chained scripts inside this `ChainedScript`
        kwargs["log_script_meta"] = False

        if log_script_meta:
            # log meta infos
            self._log_chained_script_meta()

        # collect results from scripts
        collected_results = self.res

        # run over scripts
        for ascript in self.chain_scripts():
            script_result = None
            chained_script_name = self.try_get_chained_script_name(ascript)
            try:
                # analyze with script
                script_result = ascript.analyze(apk, dalvik_vm_format, vm_analysis, gvm_analysis,
                                                *args, **kwargs)

                # store results under given categories
                categories = self.root_categories()
                if len(categories) > 0:
                    # run over dict and log items
                    for key, val in script_result.results.items():
                        collected_results.register_keys([key], *categories)
                        collected_results.log(key, val, *categories)

                else:
                    # simply update dict
                    collected_results.results.update(script_result.results)

                if log_script_meta:
                    # log successful run
                    collected_results.log_append_to_enum(CAT_SUCCESSFUL, chained_script_name, CAT_ROOT)

            except Exception as e:
                if log_script_meta:
                    # the value that will be logged for the script failure
                    failure_log_val = chained_script_name

                    # if exception shall be logged, create dict with name as key and exception as value
                    if self.log_script_failure_exception():
                        # exception message
                        exc_msg = Util.format_exception(sys.exc_info(), as_string = False)
                        failure_log_val = {failure_log_val : exc_msg}

                    # log that script encountered an error
                    collected_results.log_append_to_enum(CAT_FAILURES, failure_log_val, CAT_ROOT)

                if not self.continue_on_script_failure():
                    # reraise exception if the analysis shall be stopped
                    # after a script encountered an error
                    raise
                else:
                    log.warn('''%s: The script "%s" on apk: %s caused an error! But the other scripts will still run! Have a look at the options of `ChainedScript` for exception traceback writing!
\tError: %s''' % (self.__class__.__name__, ascript, apk.short_description(), e))

    def _log_chained_script_meta(self):
        ''' Log all scripts that are chained through this class
        and register the structure to log successful and unsuccessful scripts
        '''
        res = self.res

        # register and log all chained scripts
        res.register_keys([CAT_SCRIPTS], CAT_ROOT)
        res.log(CAT_SCRIPTS, [self.try_get_chained_script_name(s) for s in self.chain_scripts()], CAT_ROOT)

        # register structure for successful and failed scripts
        res.register_enum_keys([CAT_SUCCESSFUL, CAT_FAILURES], CAT_ROOT)

    @staticmethod
    def __remove_unnecessary_values(_dict):
        ''' Removes chained script meta information from the dictionary `_dict` '''
        try:
            del _dict[CAT_ROOT]
        except KeyError:
            pass

    @staticmethod
    def is_chained_script(script):
        ''' Check if the `script` is a `ChainedScript` '''
        return isinstance(script, ChainedScript)

    @staticmethod
    def try_get_chained_script_name(script):
        ''' If `script` is a `ChainedScript`, use the repression instead of the script name '''
        return repr(script) if ChainedScript.is_chained_script(script) else script.name

    def reset(self):
        super(ChainedScript, self).reset()

        for ascript in self.chain_scripts():
            ascript.reset()

    ############################################################
    #---ChainedScript options
    # Specify the options in your subclass as needed
    ############################################################

    def root_categories(self):
        ''' Return a tuple<str> under which you want to store the results of the scripts.
        Empty tuple means no category at all'''
        if self.__root_categories is not None:
            return self.__root_categories
        return ()

    def chain_scripts(self):
        '''
        Use this method to specify which scripts shall be chained together.

        Be careful to only return a reference to the class (`type`).
        So do not instantiate them!

        Returns
        -------
        androscripts : list<AndroScript>
            List of scripts to use (instantiated classes)
        '''
        if self.__androscripts:
            return self.__androscripts

        raise NotImplementedError

    def log_chained_script_meta_infos(self):
        ''' By default some information will be logged.
        Like e.g. the scripts used, which ran successful and which failed.
        '''
        return self.__log_chained_script_meta_infos

    def continue_on_script_failure(self):
        ''' Specify if the analysis shall continue if a script encounters an error '''
        return self.__continue_on_script_failure

    def log_script_failure_exception(self):
        ''' If true, write the exception into the result file.
        Only usable if `log_chained_script_meta_infos` returns True.
        '''
        return self.__log_script_failure_exception

    ############################################################
    #---Options
    # Determine needed options by querying
    # which options the scripts need
    ############################################################

    def needs_dalvik_vm_format(self):
        return any([s.needs_dalvik_vm_format() for s in self.chain_scripts()])

    def needs_vmanalysis(self):
        return any([s.needs_vmanalysis() for s in self.chain_scripts()])

    def needs_gvmanalysis(self):
        return any([s.needs_gvmanalysis() for s in self.chain_scripts()])

    def needs_xref(self):
        return any([s.needs_xref() for s in self.chain_scripts()])

    def needs_dref(self):
        return any([s.needs_dref() for s in self.chain_scripts()])

