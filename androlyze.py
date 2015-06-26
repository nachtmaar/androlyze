#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import datetime
import json
import logging
import sys

from androlyze import settings
from androlyze.Constants import *
import androlyze
from androlyze.log import clilog, disable_std_loggers, log_set_level, \
    clilog_set_level, redirect_to_file_handler
from androlyze.model.analysis.result.StaticResultKeys import *
from androlyze.settings import *
from androlyze.settings.exception import ConfigError
from androlyze.storage.exception import StorageException
from androlyze.util import Util
from androlyze.util.CLIUtil import CLIError
from run.Run import CliRunner



PROFILE = 0
DEBUG = 0

############################################################
#---CLI Commands
############################################################

# available commands
COMMAND = "command"
COMMAND_IMPORT = "import"
COMMAND_ANALYZE = "analyze"
COMMAND_QUERY = "query"
COMMAND_SYNC = "sync"
COMMAND_EVAL = "eval"

# available commands for query
SUBCOMMAND_QUERY_IMPORT = "import"
SUBCOMMAND_QUERY_RESULT = "result"

COMMAND_DELETE = "delete"
COMMANDS_ALL = (COMMAND_ANALYZE, COMMAND_EVAL, COMMAND_IMPORT,
                COMMAND_QUERY, COMMAND_SYNC,
                COMMAND_DELETE,)

# available commands for delete
SUBCOMMAND_DELETE_IMPORT = "import"
SUBCOMMAND_DELETE_RESULT = "result"

############################################################
# Symlink names                                            #
############################################################

# prefix for symlink programs
SYMLINK_PREFIX = "andro"

# symlink name for androlyze import
SYMLINK_IMPORT = SYMLINK_PREFIX + COMMAND_IMPORT

# symlink name for androlyze analyze
SYMLINK_ANALYZE = SYMLINK_PREFIX + COMMAND_ANALYZE

# symlink name for androlyze analyze
SYMLINK_EVAL = SYMLINK_PREFIX + COMMAND_EVAL

# symlink name for androlyze query
SYMLINK_QUERY = SYMLINK_PREFIX + COMMAND_QUERY

# symlink name for androlyze query
SYMLINK_DELETE = SYMLINK_PREFIX + COMMAND_DELETE

# symlink name for androlyze sync
SYMLINK_SYNC = SYMLINK_PREFIX + COMMAND_SYNC

############################################################
# Cli Default Settings                                     #
############################################################

CLI_DEFAULT_VERBOSITY = 3

def main(argv=None):

    program_version = "v%s" % PROJECT_VERSION
    program_version_message = '%%(prog)s %s' % program_version
    program_license = ""

    try:
        # try to detect commands through symlink calls first
        cmd = get_cmd_from_symlink_name(sys.argv[0])

        parser = __setup_parser(program_license, program_version_message, cmd)

        # process arguments
        args = parser.parse_args()

        # init logging
        verbosity = args.verbosity
        # must subtract default value from counted one
        if verbosity > CLI_DEFAULT_VERBOSITY:
            verbosity -= CLI_DEFAULT_VERBOSITY
        __init_logging(verbosity, args.quiet, args.vlog, parser)

        # config
        config_filename = args.config
        log.info("Using config file : %s", config_filename)

        r = CliRunner(config_filename, parser, args)
        # run action
        r.run_action(cmd)

        return 0
    except (ConfigError, IOError, StorageException, ValueError) as e:
        log.critical(e)
        return 1
    except KeyboardInterrupt:
        return 0
    except CLIError as e:
        clilog.warn(str(e))
        return 1
    except Exception, e:
        log.exception(e)
        return 2

############################################################
#---CLI Interface
############################################################

    ############################################################
    #---  Parser creation
    ############################################################

def __create_subparsers(parser, parents):
    '''
    Create the subparsers for the available commands.

    Parameters
    ----------
    parser : argparse.ArgumentParser
    parents : list<ArgumentParser>
        The root parsers from which to take the arguments.
    '''
    subparser = parser.add_subparsers(dest=COMMAND, help="Available commands")
    # import command
    import_parser = subparser.add_parser(COMMAND_IMPORT, conflict_handler='resolve',
                                         parents=parents, add_help=True, help="Import APKs")
    # analyze command
    analyze_parser = subparser.add_parser(COMMAND_ANALYZE, conflict_handler='resolve',
                                          parents=parents, add_help=True,
                                          help="Analyze APKs (from database, specified via package names or from file and/or directory)")
    # query command
    query_parser = subparser.add_parser(COMMAND_QUERY, conflict_handler='resolve',
                                        parents=parents, add_help=True, help="Query a database [default: %s]" % CONFIG_PATH)
    # delete command
    delete_parser = subparser.add_parser(COMMAND_DELETE, conflict_handler='resolve',
                                         parents=parents, add_help=True, help="Delete from the import database or imported apks")

    sync_parser = subparser.add_parser(COMMAND_SYNC, conflict_handler='resolve',
                                       parents = parents, add_help = True, help = "Sync from database to file system")
    
    dblyze_parser = subparser.add_parser(COMMAND_EVAL, conflict_handler='resolve',
                                       parents = parents, add_help = True, help = "Run scripts on the database")

    return analyze_parser, import_parser, query_parser, delete_parser, sync_parser, dblyze_parser

    ############################################################
    #---  Parser setup
    ############################################################

    ############################################################
    #---  Parser setup analyze
    ############################################################

def __setup_analyze_parser(analyze_parser):
    analyze_parser.add_argument("scripts", nargs="*", default = settings.get_default_scripts(), help="The scripts to use for the security audit. If nothing given, use defaults read from %s" % settings.SCRIPT_SETTINGS_PATH)
    fme = __setup_filter_me_group(analyze_parser)

    fme.add_argument("--apks", nargs="+", help='''The apk files or directories (with .apk files).
Apk files and directories can also be mixed. If non given, use the imported apks.
Will not import the apks into the import database!''')
    __add_hashes_filter_option(fme)
    __add_package_names_filter_option(fme)
    __add_tags_filter_option(fme)

    p = analyze_parser.add_argument_group("Parallelization parameters")
    pme = p.add_mutually_exclusive_group()
    pme.add_argument("-pm", "--parallelization-mode", type=str, choices = (PARALLELIZATION_MODE_PARALLEL, PARALLELIZATION_MODE_DISTRIBUTED, PARALLELIZATION_MODE_NON_PARALLEL), help = "Choose the parallelization mode. If none supplied, default value from config file will be used!")
    p.add_argument("--no-sort-code-size", "-nscs", action="store_true", help = "By default sort apks by code size (descending) -> Analyze bigger code first. Use this switch to disable this behavior")
    p.add_argument("--concurrency", type = int, help = "Number of workers to spawn. Only for parallel mode")
    p.add_argument("-si", "--send-id", action = "store_true", help = "Send id of apk file rather than actual file. Needs import with -cdb first! ")

    ############################################################
    #---  Parser setup import
    ############################################################

def __setup_dblyze_parser(dblyze_parser):
    dblyze_parser.add_argument("scripts", nargs="*", help="Scripts for the db analysis")

def __setup_import_parser(import_parser):
    ac = import_parser.add_argument_group("apk copying")
    ac.add_argument("-cd", "--copy-disk", action="store_true", help="Import the .apk file(s) to the storage dir defined in the config file.")
    ac.add_argument("-cdb", "--copy-db", action="store_true", help="Import the .apk file(s) into the database. Optional for the distributed analysis!")

    # import has apks as positional argument
    import_parser.add_argument(dest="apks", nargs="+", help='''The apk files or directories (with .apk files).
Apk files and directories can also be mixed.''')
    import_parser.add_argument("-t", "--tag", help="Tag the apks")
    import_parser.add_argument("-u", "--update", action="store_true", help="Update already imported apks")
    import_parser.add_argument("--concurrency", type = int, help="Number of processes")

    ############################################################
    #---  Parser setup sync
    ############################################################

def __setup_sync_parser(sync_parser, parents=[]):
    pass

    ############################################################
    #---  Parser setup delete
    ############################################################

def __setup_delete_parser(delete_parser, parents=[]):
    dsp = delete_parser.add_subparsers(dest=COMMAND_DELETE, help="Set the source from which you want to delete. Either from import or result storage.")

    del_import_parser = dsp.add_parser(SUBCOMMAND_DELETE_IMPORT, parents=parents, help="Delete from import storage.")
    del_import_parser.add_argument("-da", "--delete-apk", action="store_true", help="Delete the .apk from the storage root dir. But only if it's located there.")

    fme = __add_all_filter_options(del_import_parser, required=True)
    __setup_shared_args_db(fme)

    del_res_parser = dsp.add_parser(SUBCOMMAND_DELETE_RESULT, parents=parents, help="Delete from result storage.")
    __setup_shared_args_db(del_res_parser)

    # add filter options
    __setup_result_db_filter_args(del_res_parser)
    del_res_parser.add_argument("-nd", "--non-document", action="store_true", help="Signalize that the data is not a normal document. Meaning that it's not json data")

def __setup_shared_args_db(del_parser):
    del_parser.add_argument("--all", action="store_true", help="Select whole database.")

    ############################################################
    #---  Parser setup shared args
    ############################################################

def __setup_filter_me_group(parser, required=False):
    f = parser.add_argument_group("filter")
    return f.add_mutually_exclusive_group(required=required)

def __add_all_filter_options(parser, required=False):
    ''' Add filter options to the `parser`.
    Filering can be done via hashes, package-names and tags.
    But only one can be used.
    '''
    fme = __setup_filter_me_group(parser, required)
    __add_hashes_filter_option(fme)
    __add_package_names_filter_option(fme)
    __add_tags_filter_option(fme)

    return fme

def __add_hashes_filter_option(parser):
    parser.add_argument("--hashes", nargs="+", help="The hash of the apk from which you want to retrieve information. If hash(es) are supplied, given package names will be ignored !")

def __add_package_names_filter_option(parser):
    parser.add_argument("--package-names", nargs="+", help="The package names of the apks from which you want to retrieve information.")

def __add_tags_filter_option(parser):
    parser.add_argument("--tags", nargs="+", help="Only show infos for apks with specified tag(s)")

def  __setup_result_db_filter_args(parser):
    cfg = parser.add_argument_group("custom filtering", "Do your own filtering!")
    cfg.add_argument("--where", nargs='+', help="Specify additional filter criteria. Every entry is a pair of a key and a matching value seperated through whitespace")
    cfg.add_argument("--where-dict", type=json.loads, help="Specify a custom dict to pass to mongodb's find. Input has to be valid json!")

    apk = parser.add_argument_group("filter apk meta", "Filter based on apk")
    apk.add_argument("-pn", "--package-name", help="Filter by apk package name")
    apk.add_argument("--hash", help="Filter by apk hash (sha256)")
    apk.add_argument("-vn", "--version-name", help="Filter by apk version name")
    apk.add_argument("-t", "--tag", help="Filter by tag")

    script = parser.add_argument_group("filter script meta", "Filter based on script")
    script.add_argument("-sh", "--script-hash", help="Filter by script hash (sha256)")
    script.add_argument("-sn", "--script-name", help="Filter by sript name")
    script.add_argument("-sv", "--script-version", help="Filter by script version")


def __setup_shared_arguments(program_version_message, active_parsers):
    ''' Add shared arguments to the parsers '''
    for p in active_parsers:

        # database
        db = p.add_argument_group("database")
        db.add_argument("-idb", "--import-database", help="You can supply a custom import database [default: %s]" % CONFIG_PATH)
        db.add_argument("-rdb", "--result-database-name", help="You can supply a custom result database name. [default: %s]" % CONFIG_PATH)

        # config
        p.add_argument("-c", "--config", default = settings.CONFIG_PATH, help="Load a custom config file [default: %(default)s].")

        # logging stuff
        log = p.add_argument_group('logging')
        log.add_argument("-q", "--quiet", action="store_true", default=False, help="Be quiet and do not log anything to stdout")
        log.add_argument("-v", "--verbose", dest="verbosity", action="count", default=CLI_DEFAULT_VERBOSITY, help='''
        Set verbosity [default: %(default)s],  1 -> CRITICAL, 2 -> ERROR, 3 -> WARN, 4 -> INFO, 5 -> DEBUG''')
        log.add_argument("-vl", "--verbose-log", dest="vlog", help="Log stdout and stderr to file")
        p.add_argument('-V', '--version', action='version', version=program_version_message)

        p.add_argument("--yes", "-y", action="store_true", help="Autoconfirm question(s) on the command-line interface.")

    ############################################################
    #---  Parser setup query
    ############################################################

def __setup_query_parser(query_parser, parents=[]):
    query_dst_subparser = query_parser.add_subparsers(dest="query_dst", help="Select the database you want to query")
    query_import_parser = query_dst_subparser.add_parser(SUBCOMMAND_QUERY_IMPORT, conflict_handler='resolve', parents=parents, help="Query the import database")
    query_results_parser = query_dst_subparser.add_parser(SUBCOMMAND_QUERY_RESULT, conflict_handler='resolve', parents=parents, help="Query the result database")

    __setup_shared_args_db(query_import_parser)
    __setup_shared_args_db(query_results_parser)

    return query_import_parser, query_results_parser

def __setup_basic_result_query_options(parser):
    bg = parser.add_argument_group("basic result query options")

    bg.add_argument("-l", "--latest", action="store_true", help="Get the latest document.")
    bg.add_argument("--limit", type=int, help="Limit number of results. Will not influence --count!")
    bg.add_argument("-s", "--sort", action="store_true", help="Sort by analysis date (descending)")

    return bg

def __setup_query_result_parser(query_res_parser):
    __setup_basic_result_query_options(query_res_parser)

    pg = query_res_parser.add_argument_group("projection", "Project on keys")
    pgme = pg.add_mutually_exclusive_group()
    pgme.add_argument("-if", "--include-fields", nargs='+', help="The fields to include in the output document.")
    pgme.add_argument("-ef", "--exclude-fields", nargs='+', help="The fields to exclude in the output document.")

    nd = query_res_parser.add_argument_group("non-document options", "Options for data stored in gridfs")
    nd.add_argument("-nd", "--non-document", action="store_true", help="Signalize that the data is not a normal document. Meaning that it's not json data")
    nd.add_argument("-r", "--raw", action="store_true", help="Get raw data of non-document. Otherwise meta data will be returned")

    __setup_result_db_filter_args(query_res_parser)
    ig = query_res_parser.add_argument_group("id field")
    ig.add_argument("-si", "--show-id", action="store_true", help="Include _id field in output")
    ig.add_argument("-ni", "--not-interactive", action="store_true", help="No interactive results view (all results at once)")

    dme = query_res_parser.add_argument_group()
    dme.add_argument("--count", action="store_true", help="Will print the number of matching documents (not the limited ones !) ")
    dme.add_argument("-d", "--distinct", help = "Get the distict values for the given key.")
    dme.add_argument("-lrs", "--list-ran-scripts", action = "store_true", help = """Get the scripts which have been run on the apk.
Also apply a filter for the apks! Otherwise distinct values will be related to the whole db!""")

    cg = query_res_parser.add_argument_group("checks", "Also supply another filter argument! Otherwise filtering won't work!")
    cg.add_argument("--checks-non-empty-list", help = "Check the keys against a non empty list.", nargs = '*',)
    cg.add_argument("--checks-empty-list", help = "Check the keys against an empty list.", nargs = '*',)
    cg.add_argument("--checks-true", help = "Check if the values of the given keys are true.", nargs = '*',)
    cg.add_argument("--checks-false", help = " Check if the values of the given keys are false.", nargs = '*',)
    cg.add_argument("--checks-not-null", help = "Check if the values of the given keys are null (python None).", nargs = '*',)
    cg.add_argument("--checks-null", help = "Check if the values of the given keys are not null (python None).", nargs = '*',)
    cg.add_argument("--conjunction", default = 'or', help = "Choose between 'or' and 'and'. Specifies how to to link the checks together [default: %(default)s]")

def __setup_query_import_parser(query_import_parser, parents=[]):
    query_import_subparser = query_import_parser.add_subparsers(dest="query_import_cmd", help="Available query commands for import db")

    # has hash as optional argument
    infos_parser = query_import_subparser.add_parser(androlyze.COMMAND_QUERY_INFOS, parents=parents, help="List apks (short description)")
    all_infos_parser = query_import_subparser.add_parser(androlyze.COMMAND_QUERY_INFOS_ALL, parents=parents, help="List apks (detailed description)")
    versions_parser = query_import_subparser.add_parser(androlyze.COMMAND_QUERY_VERSIONS, parents=parents, help="List versions")
    paths_parser = query_import_subparser.add_parser(androlyze.COMMAND_QUERY_PATHS, parents=parents, help="List paths")

    # filter via hashes and tags
    package_names_parser = query_import_subparser.add_parser(androlyze.COMMAND_QUERY_PACKAGE_NAMES, parents=parents, help="List package names")
    fme = __setup_filter_me_group(package_names_parser)
    __add_hashes_filter_option(fme)
    __add_tags_filter_option(fme)

    # filter via package names and tags
    hashes_parser = query_import_subparser.add_parser(androlyze.COMMAND_QUERY_HASHES, parents=parents, help="List hashes of apks")
    fme = __setup_filter_me_group(hashes_parser)
    __add_package_names_filter_option(fme)
    __add_tags_filter_option(fme)

    # all filters enabled
    for p in infos_parser, all_infos_parser, versions_parser, paths_parser:
        __add_all_filter_options(p)

        ############################################################
        #---  Root parser setup
        ############################################################

def __setup_parser(program_license, program_version_message, cmd=None):
    '''
    Set up the argument parser.

    Parameters
    ----------
    program_license : str
    program_version_message : str
    cmd : str, optional (default is None)
        For the available commands see the variables prefixed with "COMMAND".
        If a command is given, the available arguments for this command will be added to the root parser
        instead of creating a subparser for every command.
        This is needed to get the symlink programs to work.

    Returns
    -------
    argparse.ArgumentParser
    '''

    # application called via symlink
    symlink_call = True if cmd is not None else False

    shared_args_parser = ArgumentParser(add_help=False)
    __setup_shared_arguments(program_version_message, [shared_args_parser])

    # configure root parser
    parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter,
                            parents=[shared_args_parser], conflict_handler='resolve')

    # if no symlink given, add the available commands as subparsers
    analyze_parser, import_parser, query_parser, del_parser, sync_parser, dblyze_parser = 6 * [None]
    if not symlink_call:
        analyze_parser, import_parser, query_parser, del_parser, sync_parser, dblyze_parser = __create_subparsers(parser, parents=[shared_args_parser])

    # otherwise set the respective parser as root parser
    if symlink_call:
        if cmd == COMMAND_ANALYZE:
            analyze_parser = parser
        elif cmd == COMMAND_IMPORT:
            import_parser = parser
        elif cmd == COMMAND_QUERY:
            query_parser = parser
        elif cmd == COMMAND_DELETE:
            del_parser = parser
        elif cmd == COMMAND_SYNC:
            sync_parser = parser
        elif cmd == COMMAND_EVAL:
            dblyze_parser = parser

    # setup subparsers
    if analyze_parser is not None:
        __setup_analyze_parser(analyze_parser)
    if import_parser is not None:
        __setup_import_parser(import_parser)
    if del_parser is not None:
        __setup_delete_parser(del_parser)
    if sync_parser is not None:
        __setup_sync_parser(sync_parser)
    if dblyze_parser is not None:
        __setup_dblyze_parser(dblyze_parser)

    if query_parser is not None:
        query_import_parser, query_results_parser = __setup_query_parser(query_parser)

        __setup_query_import_parser(query_import_parser)
        __setup_query_result_parser(query_results_parser)

    return parser

############################################################
#--- CLI Helpers
############################################################

def get_cmd_from_symlink_name(symlink_name):
    ''' Return the appropriate cmd for the `symlink_name` '''
    cmd = None
    if symlink_name.endswith(SYMLINK_ANALYZE):
        cmd = COMMAND_ANALYZE
    elif symlink_name.endswith(SYMLINK_EVAL):
        cmd = COMMAND_EVAL
    elif symlink_name.endswith(SYMLINK_IMPORT):
        cmd = COMMAND_IMPORT
    elif symlink_name.endswith(SYMLINK_QUERY):
        cmd = COMMAND_QUERY
    elif symlink_name.endswith(SYMLINK_DELETE):
        cmd = COMMAND_DELETE
    elif symlink_name.endswith(SYMLINK_SYNC):
        cmd = COMMAND_SYNC

    return cmd


############################################################
# Logging                                                  #
############################################################

def __init_logging(verbosity=CLI_DEFAULT_VERBOSITY, quiet=False, vlog=None, argparser=None):
    '''
    Use to configure logging, do a few checks and load the filters.

    Parameters
    ----------
    verbosity: int, optional (default is `CLI_DEFAULT_VERBOSITY`)
        the verbosity level ( 1 <= v <= 6, 1 -> CRITICAL, 2 -> ERROR, 3 -> WARN, 4 -> INFO, 5 -> DEBUG)
    quiet: bool, optional (default is False)
        if nothing shall be logged (does not affect file logging)
    vlog: str, optional (default is None and disables logging to file)
        filename of the logging file
    argparser: ArgumentParser, optional (default is None)

    Raises
    ------
    CLIError
    '''
    if verbosity < 1 or verbosity > 5:
        raise CLIError('Verbosity has to be 1 <= v <= 5, is: %d' % verbosity, argparser)
    __configure_logging(quiet, verbosity, vlog)

def __configure_logging(quiet, verbosity, logger_filename):
    '''
    Configure the logging.

    If quiet, the logger will only log with the specified verbosity level to file (if given).

    If not quiet, the verbosity will be forwarded to the logger

    Parameters
    ----------
    quiet: boolean
        if nothing shall be logged (does not affect file logging)
    verbosity: int
        the verbosity level
    logger_filename: str
        filename of the logging file
    '''
    LOG_LEVEL = logging.CRITICAL
    if verbosity is not None:
        if verbosity == 2:
            LOG_LEVEL = logging.ERROR
        elif verbosity == 3:
            LOG_LEVEL = logging.WARN
        elif verbosity == 4:
            LOG_LEVEL = logging.INFO
        elif verbosity >= 5:
            LOG_LEVEL = logging.DEBUG

    if quiet:
        disable_std_loggers()
    else:
        log_set_level(LOG_LEVEL)
        clilog_set_level(logging.INFO)

    # write to file with specified log level
    redirect_to_file_handler(logger_filename, LOG_LEVEL)

if __name__ == "__main__":
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'androlyze.Main_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    time, ret_code = Util.timeit(main)
    log.warn('Took %s (h/m/s)\n' % datetime.timedelta(seconds=round(time)))

    if DEBUG:
        with open("time.txt", "a") as f:
            f.write('%s : %s\n' % (datetime.datetime.now(), datetime.timedelta(seconds=round(time))))

    sys.exit()

