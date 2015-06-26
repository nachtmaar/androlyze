
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import itertools

from CliCommands import COMMANDS_ALL, COMMAND_QUERY, COMMAND_SYNC, \
    COMMAND_IMPORT, COMMAND_ANALYZE, COMMAND_EVAL, COMMAND_DELETE, SUBCOMMAND_QUERY_IMPORT, \
    SUBCOMMAND_QUERY_RESULT, SUBCOMMAND_DELETE_IMPORT, SUBCOMMAND_DELETE_RESULT
from androlyze import settings, ANALYZE_MODE_DISTRIBUTED, \
    ANALYZE_MODE_NON_PARALLEL, ANALYZE_MODE_PARALLEL, Constants
import androlyze
from androlyze.Constants import PROJECT_NAME
from androlyze.log.Log import log, clilog
from androlyze.model.analysis.result.StaticResultKeys import RESOBJ_SCRIPT_META, \
    RESOBJ_SCRIPT_META_NAME
from androlyze.settings import SECTION_DATABASE, KEY_DATABASE_IMPORT, \
    SECTION_FILE_SYSTEM, KEY_FILE_SYSTEM_WRITE_RESULTS_TO_FILE_SYSTEM, \
    KEY_FILE_SYSTEM_RESULT_DIR, PARALLELIZATION_MODE_DISTRIBUTED, \
    PARALLELIZATION_MODE_NON_PARALLEL
from androlyze.settings.Settings import Settings
from androlyze.storage.importdb.ImportQueryInterface import TABLE_APK_IMPORT_KEY_SIZE_APP_CODE
from androlyze.storage.resultdb import MongoUtil
from androlyze.util import Util, CLIUtil
from androlyze.util.CLIUtil import CLIError, cli_check_n_exec, \
    print_query_result_db
from androlyze.model.script import ScriptUtil


class AndroLyzeLabRunner(object):
    ''' Command-line interface runner '''

    def __init__(self, config_filename, import_db = None):
        '''
        Parameters
        ----------
        config_filename : str, optional (default is `settings.CONFIG_PATH`)
            The path to the config to load.
        import_db : str, optional (default is read from config file)
            Path to the import db.
        '''
        # type: Settings
        if config_filename is None:
            config_filename = settings.CONFIG_PATH

        # create settings variable
        self.__settings = Settings(config_filename, default_path = settings.DEFAULTS_PATH)

        log.debug("config file settings: %s\n\tCLI options may overwrite them!", self.__settings)

        # load and set androguard path from configs
        Util.set_androguard_path(self.settings)

        # type: str
        import_db = self._get_import_db(import_db = import_db)
        #self.args.import_database
        log.info("Using import database: %s", import_db)

        # load a few other settings
        self.__storage = self._create_storage(import_db)

    def get_settings(self):
        return self.__settings

    def get_storage(self):
        return self.__storage

    def set_settings(self, value):
        self.__settings = value

    def set_storage(self, value):
        self.__storage = value

    def del_settings(self):
        del self.__settings

    def del_storage(self):
        del self.__storage

    settings = property(get_settings, set_settings, del_settings, "Settings")
    storage = property(get_storage, set_storage, del_storage, "RedundantStorage")

    def get_apks_or_paths_from_cli(self, **kwargs):
        ''' Returns either list<str> (paths to apks) or list<Apk> if taken from import database.
        Returns as second component if list is of type `Apk` or not.

        For additional keyword-arguments see :py:meth:`.ImportStorageInterface.get_imported_apks`.
        '''
        from androlyze.loader.ApkImporter import ApkImporter

        args = self.args

        # apk paths supplied ?
        apk_paths = None
        try:
            apk_paths = args.apks
        except AttributeError:
            pass

        filter_args = CLIUtil.get_filter_options_from_cli(args)
        hashes, package_names, tags = filter_args
        res = None

        if apk_paths is not None:
            # list<str>
            res = ApkImporter.get_apks_from_list_or_dir(apk_paths)
        else:
            # list<Apk>
            res = self.storage.get_imported_apks(hashes, package_names, tags, **kwargs)

        return res, apk_paths is None

    def _get_import_db(self, import_db = None):
        ''' Get the import database from settings if not alreay supplied.

        Parameters
        ----------
        import_db : str, optional (default is read from config file)
            Path to the import db.
        Returns
        -------
        str
        '''
        if not import_db:
            return self.settings[SECTION_DATABASE, KEY_DATABASE_IMPORT]
        return import_db

    def create_storage(self):
        ''' Same as :py:method:`AndroLyzeLabRunner._create_storage` but import db name read from config file '''
        return self._create_storage(self._get_import_db())

    def _create_storage(self, import_db, custom_mongodb_name = None):
        '''
        Create the storage object.

        Be sure the `settings` already has been initialized.

        Parameters
        ----------
        import_db : str
            The path to the import database.
        custom_mongodb_name : str, optional (default is None)
            Use `custom_mongodb_name` as database name instead of the value from config file.
        '''
        settings = self.settings

        # load after androguard path has been set
        from androlyze.storage.apk import ApkStorageFactory
        from androlyze.storage.RedundantStorage import RedundantStorage

        # If not enabled pass None to Analyzer and don't store in the file sys at all
        STORAGE_DIR = None
        if  settings.get_bool((SECTION_FILE_SYSTEM, KEY_FILE_SYSTEM_WRITE_RESULTS_TO_FILE_SYSTEM)):
            STORAGE_DIR = settings[(SECTION_FILE_SYSTEM, KEY_FILE_SYSTEM_RESULT_DIR)]

        # get mongodb specific stuff
        mongodb_name = custom_mongodb_name

        # read mongodb settings from config
        _mongodb_name, mongodb_ip, mongodb_port, mongodb_username, mongodb_passwd, mongodb_use_ssl, mongodb_ca_cert = settings.get_mongodb_settings()
        # take from config if not suppliad
        if mongodb_name is None:
            mongodb_name = _mongodb_name

        return RedundantStorage(import_db, STORAGE_DIR,
                                # db connection
                                mongodb_name, mongodb_ip, mongodb_port,
                                # auth
                                result_db_username = mongodb_username, result_db_passwd = mongodb_passwd,
                                # ssl
                                result_db_use_ssl=mongodb_use_ssl, ssl_ca_cert=mongodb_ca_cert,
                                #create storage only on demand from the config
                                distributed_apk_storage_factory = lambda: ApkStorageFactory.get_apk_storage(settings)
                                )

    def run_action(self, cmd):
        ''' Run an action specified by `cmd`(see COMMAND_ prefixed variables) '''

        parser = self.parser
        args = self.args

        # check which command has been used
        if cmd is None:

            # no command specified through program name -> get it from argparser
            cmd = args.command
            
        if cmd in COMMANDS_ALL:
            hashes, package_names, tags = CLIUtil.get_filter_options_from_cli(args)
            yes = args.yes

            if cmd == COMMAND_QUERY:
                self.action_query(hashes, package_names, tags, yes)

            # dblyze -> do the analysis results evaluation            
            elif cmd == COMMAND_EVAL:
                dblyze_scripts = ScriptUtil.import_scripts(args.scripts, clazz_name = "Eval")
                for dblyze_script in dblyze_scripts:
                    dblyze_script().evaluate(self.storage)
                
            # sync from result db to file sys
            elif cmd == COMMAND_SYNC:
                total_entries = androlyze.action_sync_fs(self.storage, lambda _ : False)

                CLIUtil.cli_check_n_exec(androlyze.action_sync_fs,
                                         prompt_prefix = "Will download %d entries from result database!" % total_entries,
                                         circumvent_check = args.yes,
                                         args = (self.storage, lambda _ : True)
                                         )
            else:
                # print welcome message
                clilog.info("Welcome to %s!\n" % PROJECT_NAME)

                # import command
                if cmd == COMMAND_IMPORT:
                    apks_or_paths, _ = self.get_apks_or_paths_from_cli()
                    tag = args.tag
                    copy2disk, copy2db, update, concurrency = args.copy_disk, args.copy_db, args.update, args.concurrency
                    if not update:
                        log.warn('''--update not supplied.
No update of already present apks in database will be done!''')
                    androlyze.action_import_apks(self.storage, apks_or_paths, copy2disk, copy2db, update, tag, concurrency = concurrency)
                # analyze command
                elif cmd == COMMAND_ANALYZE:
                    # androguard path has to be set before
                    from androlyze import action_analyze

                    # sort apks ?
                    get_apks_kwargs = {}
                    no_sort_by_code_size = args.no_sort_code_size
                    if not no_sort_by_code_size:
                        # sort apks by app code size for better scheduling
                        get_apks_kwargs = dict(order_by = TABLE_APK_IMPORT_KEY_SIZE_APP_CODE, ascending = False)
                    apks_or_paths, _ = self.get_apks_or_paths_from_cli(**get_apks_kwargs)

                    # debug infos
                    if not no_sort_by_code_size and not args.apks:
                        apks_or_paths, _it = itertools.tee(apks_or_paths)
                        clilog.info('Using Code Size Scheduling for faster analysis!')
                        log.debug('\n'.join(('%s: %s' % (x.package_name, x.size_app_code) for x in _it)))

                    scripts = args.scripts
                    parallel_mode, concurrency, send_id = self.__load_parallel_settings()

                    # get analysis mode
                    analyze_mode = None
                    if parallel_mode == PARALLELIZATION_MODE_DISTRIBUTED:
                        analyze_mode = ANALYZE_MODE_DISTRIBUTED
                    elif parallel_mode == PARALLELIZATION_MODE_NON_PARALLEL:
                        analyze_mode = ANALYZE_MODE_NON_PARALLEL
                    else:
                        analyze_mode = ANALYZE_MODE_PARALLEL
                    action_analyze(self.storage, scripts, apks_or_paths,
                                   mode = analyze_mode, concurrency = concurrency,
                                   serialize_apks = not send_id)
                # delete command
                elif cmd == COMMAND_DELETE:
                    self.action_delete(parser, hashes, package_names, tags, yes)

                clilog.info("done")

    def __load_parallel_settings(self):
        ''' Load parallelization settings from run or config file.
        Cli settings override config settings!

        Returns
        -------
        parallel_mode, concurrency
            For `parallel_mode` see values `settings.PARALLELIZATION_MODE_` ...
        '''
        args = self.args
        # no default value with argparser defined because we want to check if value is specified
        parallel_mode = args.parallelization_mode
        concurrency = args.concurrency

        # only load not specified values from settings file
        if concurrency is None:
            concurrency = self.settings.get_int((settings.SECTION_PARALLELIZATION, settings.KEY_PARALLELIZATION_CONCURRENCY), default = None)

        # config provides only fallback value
        if parallel_mode is None:
            parallel_mode = self.settings[(settings.SECTION_PARALLELIZATION, settings.KEY_PARALLELIZATION_MODE)]

        send_id = args.send_id

        return parallel_mode, concurrency, send_id

class CliRunner(AndroLyzeLabRunner):
    ''' AndroLyzeLabRunner for run-usage '''

    def __init__(self, config_filename, parser, args, **kwargs):
        '''
        `kwargs` are directly passed to `AndroLyzeLabRunner`.

        Parameters
        ----------
        config_filename : str, optional (default is `settings.CONFIG_PATH`)
            The path to the config to load.
        parser : argparse.ArgumentParser
            run parser
        args
            parsed arguments from `ArgumentParser`
        '''

        self.__args = args
        self.__parser = parser
        super(CliRunner, self).__init__(config_filename, import_db = self.args.import_database,  **kwargs)

    def get_args(self):
        return self.__args

    def get_parser(self):
        return self.__parser

    def set_args(self, value):
        self.__args = value

    def set_parser(self, value):
        self.__parser = value

    def del_args(self):
        del self.__args

    def del_parser(self):
        del self.__parser

    args = property(get_args, set_args, del_args, "parsed arguments from `ArgumentParser")
    parser = property(get_parser, set_parser, del_parser, "argparse.ArgumentParser : run parser")

    ############################################################
    #---Actions
    ############################################################

    def action_query(self, hashes, package_names, tags, yes):
        ''' Query the database '''
        args = self.args
        parser = self.parser

        # check on which database to query
        # get from argparser
        query_dst = args.query_dst
        if query_dst == SUBCOMMAND_QUERY_IMPORT:
            clilog.info('\n'.join(androlyze.action_query_import_db(self.storage, args.query_import_cmd, hashes, package_names, tags)))
        elif query_dst == SUBCOMMAND_QUERY_RESULT:
            kwargs = CLIUtil.get_result_db_filter_args_from_argparser(args)
            if args.show_id:
                kwargs["remove_id_field"] = not args.show_id

            distinct_key = None
            if args.distinct is not None:
                distinct_key = args.distinct
            # get distinct values for script name
            elif args.list_ran_scripts:
                distinct_key = MongoUtil.get_attr_str(RESOBJ_SCRIPT_META, RESOBJ_SCRIPT_META_NAME, args.non_document)

            no_args_supplied = len(kwargs) == 0 and not args.latest and not args.count and distinct_key is None
            whole_db = args.all
            raw = args.raw

            # update with basic result query options
            kwargs.update(CLIUtil.get_basic_result_query_options(args))

            kwargs.update(dict(include_fields=args.include_fields, exclude_fields=args.exclude_fields, non_document_raw=raw, distinct_key = distinct_key))

            if no_args_supplied and not whole_db:
                raise CLIError('Not enough arguments supplied!\nIf you want to dump the whole db, use the --all switch!', parser)

            res = cli_check_n_exec(
                androlyze.action_query_result_db,
                prompt_prefix='Will print whole results db!',
                circumvent_check=not no_args_supplied or yes,
                args=(self.storage, CLIUtil.get_checks_from_cli(args)),
                kwargs=kwargs)

            # log results
            print_query_result_db(res, distict_generator=distinct_key is not None, count=args.count, raw=raw, interactive = not args.not_interactive)

    def action_delete(self, parser, hashes, package_names, tags, yes):
        ''' Delete from the database specified by `parser` args '''

        args = self.args
        whole_db = args.all
        db = args.delete

        if whole_db:
            cli_check_n_exec(prompt_prefix="Do you really want to delete the whole database?", func=lambda:True, circumvent_check=not whole_db)
        # place after run check!
        circumvent_check = yes or whole_db

        # import db
        if db == SUBCOMMAND_DELETE_IMPORT:
            cli_check_n_exec(androlyze.action_delete_apks_import, circumvent_check=circumvent_check, args=(self.storage, args.delete_apk, hashes, package_names, tags, whole_db))
        # res db
        elif db == SUBCOMMAND_DELETE_RESULT:
            kwargs = CLIUtil.get_result_db_filter_args_from_argparser(args)

            if not kwargs and not whole_db:
                raise CLIError('You did not supply any filter argument!\nIf you want to delete the whole db, use the --all switch!', parser)

            kwargs["whole_db"] = whole_db
            # delete from res db
            n = cli_check_n_exec(androlyze.action_delete_apks_res, circumvent_check = circumvent_check, args=(self.storage,), kwargs=kwargs)
            if not whole_db:
                clilog.info("Deleted %s file/document(s) !" % n)
