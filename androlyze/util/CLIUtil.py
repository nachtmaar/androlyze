
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Utility for command-line interface
'''

import sys

from androlyze.log.Log import log, clilog
from androlyze.model.script.ScriptUtil import dict2json
from androlyze.error.AndroLyzeLabError import AndroLyzeLabError


def cli_check_n_exec(func, prompt_prefix = "", circumvent_check = False, args=(), kwargs={}):
    ''' Check if the user really want's to continue and exec `func`.
    Otherwise quit the program with exit code 1 and log some message.

    Returns the result of the `func` or None.
    '''

    BASE_PROMPT = 'Continue and execute? (y/n): '
    prompt = "%s\n\t\t%s" % (prompt_prefix, BASE_PROMPT) if prompt_prefix else BASE_PROMPT
    if circumvent_check or raw_input(prompt).lower() == 'y':
        return func(*args, **kwargs)
    else:
        log.critical("aborted ...")
        sys.exit(1)

class CLIError(AndroLyzeLabError):
    '''Generic exception to raise and log different fatal errors and print the help menu afterwards'''

    def __init__(self, msg, argparser=None):
        super(CLIError).__init__(type(self))
        help_msg = '%s\n' % argparser.format_help() if argparser else ''
        self.msg = "%sError: %s" % (help_msg, msg)

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg

def print_query_result_db(res, distict_generator = False, count = False, raw = False, interactive = True):
    '''
    Print the results from the result db (mongodb).

    Parameters
    ----------
    count : bool, optional (default is False)
        Only print count, not results
    distict_generator : bool, optional (default is False)
        Res is generator<object> created from the distinct(...) method of mongodb.
        If generaor<dict>, convert each dict to json.
        Otherwise just print.
    raw : bool, optional (default is False)
        Print raw data from gridfs
        Otherwise print json.
    res : gridfs.grid_file.GridOutCursor or generator<object> or pymongo.cursor.Cursor
        First if non_document and non_document_raw.
        Second if disctinct values wanted.
        Thirst otherwise.
        The results to print
    interactive: bool, optional (default is True)
        Iterate interactive through the result cursor
    '''
    from pymongo.errors import PyMongoError

    try:
        # print count
        if count:
            cnt = 0
            # res is list
            if distict_generator:
                cnt = len(res)
            # res is cursor
            else:
                cnt = res.count()
            clilog.info(cnt)
        else:
            if distict_generator:
                for r in sorted(res):
                    if isinstance(r, dict):
                        r = dict2json(res)
                    clilog.info(r)
            else:
                for i, res in enumerate(res, 1):
                    # interactive result view
                    if i != 1 and interactive and raw_input('Press any key to view next result or abort with "no" !)').lower() == 'no':
                        break
                    sys.stderr.write('/* {} */\n'.format(i))
                    # print raw data
                    if raw:
                        # gridfs.grid_file.GridOut
                        for gridout_obj in res:
                            clilog.info(gridout_obj)
                    # print json
                    else:
                        clilog.info(dict2json(res))

    except PyMongoError as e:
        log.exception(e)

############################################################
#---CLI option parsing and translation
############################################################

def get_checks_from_cli(args):
    ''' Get the checks from run and prepare the dictionary for the "checks" argument of :py:method:`androlyze.action_query_result_db` '''
    return {
            "checks_non_empty_list" : args.checks_non_empty_list,
            "checks_empty_list" : args.checks_empty_list,
            "checks_true" : args.checks_true,
            "checks_false" : args.checks_false,
            "checks_not_null" : args.checks_not_null,
            "checks_null" : args.checks_null,
            "conjunction" : args.conjunction
            }

def get_basic_result_query_options(args):
    ''' Get basic result query optionsfor result db from run and build kwargs for :py:meth:`.ResultDatabaseStorage.get_results`.
    Also see :py:method:`.androlyze.setup_basic_result_query_options` for the setup of the options
    '''

    kwargs = {}
    if args.limit is not None:
        kwargs['n'] = args.limit
    if args.latest:
        kwargs['latest'] = True,
    if args.sort:
        kwargs['sort'] = True

    return kwargs

def get_filter_options_from_cli(args):
    ''' Get the filter options from run. Not all or even none may be specified '''
    hashes, package_names, tags = 3 * [None]
    # try to get from argumentparser
    # but not all arguments have these attributes
    try:
        hashes = args.hashes
    except AttributeError:
        pass
    try:
        package_names = args.package_names
    except AttributeError:
        pass
    try:
        tags = args.tags
        # we don't want an empty list
        if len(tags) == 0:
            tags = None
    except (AttributeError, TypeError):
        pass
    return hashes, package_names, tags

def get_result_db_filter_args_from_argparser(args):
    ''' Get filter args for result db from run and build kwargs for :py:meth:`.ResultDatabaseStorage.get_results` '''
    kwargs = {}

    for key, val in [

            # apk stuff
            ("package_name", args.package_name),
            ("apk_hash", args.hash),
            ("version_name", args.version_name),
            ("tag", args.tag),

            # script stuff
            ("script_name", args.script_name),
            ("script_hash", args.script_hash),
            ("script_version", args.script_version)
        ]:
        if val is not None:
            kwargs[key] = val

    if args.where is not None:
        kwargs["where"] = dict(zip(args.where[0::2], args.where[1::2]))
    if args.where_dict is not None:
        if not "where" in kwargs:
            kwargs["where"] = {}
        kwargs["where"].update(args.where_dict)
    if args.non_document:
        kwargs["non_document"] = args.non_document
    try:
        if args.list_ran_scripts:
            kwargs["list_ran_scripts"] = args.non_document
    except AttributeError:
        pass

    return kwargs