
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.analyze import AnalyzeUtil
from androlyze.analyze.AnalyzeUtil import apk_gen, open_apk
from androlyze.analyze.BaseAnalyzer import BaseAnalyzer
from androlyze.log.Log import log, clilog
from androlyze.storage.exception import StorageException
from androlyze.model.script import ScriptUtil

class Analyzer(BaseAnalyzer):
    ''' Non-parallel analyzer '''

    def __init__(self, storage, script_list, script_hashes, *args, **kwargs):
        ''' See :py:method`.BaseAnalyzer.__init__` for details on the first attributes '''
        super(Analyzer, self).__init__(storage, script_list, script_hashes, *args, **kwargs)

        # instantiate scripts
        self.script_list = sorted(ScriptUtil.instantiate_scripts(script_list, script_hashes = script_hashes))

    def _analyze(self, test = False):
        '''
        Start the analysis and store the results in the predefined place.

        Parameters
        ----------
        test : bool, optional (default is False)
            Use for testing. Will not store any result !

        Returns
        -------
        int
            Number of analyzed apks
        list<ResultObject>
            List of the results (only if `test`)
        '''
        androscripts = self.script_list

        # collect results for test mode
        test_results = []

        # get minimum options for all scripts -> boost performance
        # use only as much options as needed!

        # run over apks
        for apk_path, _apk, _ in apk_gen(self.apks_or_paths):

            eandro_apk = open_apk(apk_path, apk=_apk)

            # if is None error happened and has been logged
            # otherwise proceed with analysis
            if eandro_apk is not None:

                # tuple<FastApk, AndroScript>
                res = AnalyzeUtil.analyze_apk(eandro_apk, androscripts, self.min_script_needs, reset_scripts = True)

                if res:
                    # unpack results
                    fastapk, script_results = res

                    # store results if not in test mode
                    if not test:
                        for script in script_results:

                            try:
                                storage_result = AnalyzeUtil.store_script_res(self.storage, script, fastapk)
                                # keep storage results
                                self.add_storage_result(storage_result)
                            except StorageException as e:
                                log.warn(e)
                    else:
                        # deliver result object in testing mode
                        test_results += [s.res for s in script_results]

                    clilog.info("analyzed %s", fastapk.short_description())

                # increment counter, no lock needed, nobody else is writing to this value
                self.cnt_analyzed_apks.value += 1

        if test:
            return test_results

        return self.cnt_analyzed_apks.value
