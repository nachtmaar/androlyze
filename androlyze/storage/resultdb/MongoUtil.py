
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Utility functions for mongodb.
'''

from androlyze.log.Log import log
from androlyze.model.script.ScriptUtil import dict2json
from androlyze.storage import Util
from gridfs.grid_file import GridOutCursor
from pymongo.cursor import Cursor

# in operator
MONGODB_IN_OPERATOR = "$in"

############################################################
#---MongoDB key escaping
############################################################

def escape_key(k):
    '''
    Escape key `k` so that in conforms to mongodb's key restrictions.

    See Also
    --------
    http://docs.mongodb.org/manual/faq/developers/#dollar-sign-operator-escaping
    '''
    replaced_key = k
    DOT = '.'
    DOT_REPL = '_'

    DOLLAR = '$'
    DOLLAR_REPL = '_$'

    # replace dot
    if DOT in k:
        replaced_key = k.replace(DOT, DOT_REPL)

    # replace starting dollar
    if k.startswith(DOLLAR):
        replaced_key = k.replace(DOLLAR, DOLLAR_REPL, 1)

    return replaced_key

def escape_keys(_dict):
    ''' Escape the keys in the `_dict` so that the `_dict` can be inserted into mongodb.

    Will do a deepcopy of the `dict`!
    So escaping isn't in-place!

    Parameters
    ----------
    _dict : dict

    Returns
    -------
    dict
    '''
    return Util.escape_dict(_dict, escape_key, escape_keys = True, escape_values = False)


############################################################
#---MongoDB query builder helper functions
############################################################

def get_attr_str(key, attr, gridfs = False):
    ''' Get the attribute string depending on `gridfs`'''
    from androlyze.storage.resultdb.ResultDatabaseStorage import GRIDFS_FILES_METADATA

    BASE = '%s.%s' % (key, attr)
    if gridfs:
        return '%s.%s' % (GRIDFS_FILES_METADATA, BASE)
    return BASE

def build_apk_meta_where(kwargs, gridfs = False):
    ''' Create where clause from `kwargs` for apk meta key '''
    from androlyze.model.analysis.result.StaticResultKeys import RESOBJ_APK_META, \
        RESOBJ_APK_META_PACKAGE_NAME, RESOBJ_APK_META_HASH, \
        RESOBJ_APK_META_VERSION_NAME, RESOBJ_APK_META_TAG

    wheres = []
    # get from kwargs
    # apk stuff
    package_name = kwargs.get("package_name", None)
    apk_hash = kwargs.get("apk_hash", None)
    version_name = kwargs.get("version_name", None)
    tag = kwargs.get("tag", None)

    def apk_meta_attr(attr):
        return get_attr_str(RESOBJ_APK_META, attr, gridfs)

    if package_name is not None:
        wheres += [(apk_meta_attr(RESOBJ_APK_META_PACKAGE_NAME), package_name)]
    if apk_hash is not None:
        wheres += [(apk_meta_attr(RESOBJ_APK_META_HASH), apk_hash)]
    if version_name is not None:
        wheres += [(apk_meta_attr(RESOBJ_APK_META_VERSION_NAME), version_name)]
    if tag is not None:
        wheres += [(apk_meta_attr(RESOBJ_APK_META_TAG), tag)]

    return wheres

def build_script_meta_where(kwargs, gridfs = False):
    ''' Create where clause from `kwargs` for script meta key '''
    from androlyze.model.analysis.result.StaticResultKeys import RESOBJ_SCRIPT_META, \
        RESOBJ_SCRIPT_META_HASH, RESOBJ_SCRIPT_META_NAME, RESOBJ_SCRIPT_META_VERSION

    wheres = []
    # get from kwargs
    # script stuff
    script_hash = kwargs.get("script_hash", None)
    script_name = kwargs.get("script_name", None)
    script_version = kwargs.get("script_version", None)

    def apk_meta_attr(attr):
        return get_attr_str(RESOBJ_SCRIPT_META, attr, gridfs)

    if script_hash is not None:
        wheres += [(apk_meta_attr(RESOBJ_SCRIPT_META_HASH), script_hash)]
    if script_name is not None:
        wheres += [(apk_meta_attr(RESOBJ_SCRIPT_META_NAME), script_name)]
    if script_version is not None:
        wheres += [(apk_meta_attr(RESOBJ_SCRIPT_META_VERSION), script_version)]

    return wheres


def build_checks_filter(
                        checks_non_empty_list = None, checks_empty_list = None,
                        checks_true = None, checks_false = None,
                        checks_not_null = None, checks_null = None,
                        conjunction = 'or'
                        ):
    '''
    Helper function to easily check if some value has been set.
    E.g. == [],!= [], != null, == null, == true, == false.

    Parameters
    ----------
    checks_non_empty_list : iterable<str>, optional (default is ())
        Check the keys against a non empty list.
    checks_empty_list : iterable<str>, optional (default is ())
        Check the keys against an empty list.
    checks_true : iterable<str>, optional (default is ())
        Check if the values of the given keys are true.
    checks_false : iterable<str>, optional (default is ())
        Check if the values of the given keys are false.
    checks_not_null : iterable<str>, optional (default is ())
        Check if the values of the given keys are null (python None).
    checks_null : iterable<str>, optional (default is ())
        Check if the values of the given keys are not null (python None).
    conjunction : str, optional (default is 'or')
        Choose between 'or' and 'and'.
        Specifies how to to link the filter arguments.

    Examples
    --------
    >>> print build_checks_filter(checks_non_empty_list = ['logged.enum'], checks_true = ['logged.bool'])
    {'$or': [{'logged.enum': {'$ne': []}}, {'logged.bool': True}]}
    >>> print build_checks_filter(checks_empty_list = ["foo"])
    {'foo': []}

    Returns
    -------
    dict
        Dictionary describing the checks.
        Can be used for mongodb.
    '''

    if checks_empty_list is None:
        checks_empty_list = ()
    if checks_non_empty_list is None:
        checks_non_empty_list = ()
    if checks_false is None:
        checks_false = ()
    if checks_true is None:
        checks_true = ()
    if checks_null is None:
        checks_null = ()
    if checks_not_null is None:
        checks_not_null = ()

    filters = []

    def gen_not_equal(key, val):
        ''' Generate not equals clause for mongodb '''
        OPERATOR_NON_EQ = '$ne'
        return {key : {OPERATOR_NON_EQ : val}}

    def gen_equal(key, val):
        ''' Generate equals clause for mongodb '''
        return {key : val}

    # check for non empty list
    for key in checks_non_empty_list:
        filters.append( gen_not_equal(key, []) )

    # check for empty list
    for key in checks_empty_list:
        filters.append( gen_equal(key, []) )

    # check for True
    for key in checks_true:
        filters.append( gen_equal(key, True) )

    # check for False
    for key in checks_false:
        filters.append( gen_equal(key, False) )

    # checks for null
    for key in checks_null:
        filters.append( gen_equal(key, None) )

    # checks for not null
    for key in checks_not_null:
        filters.append( gen_not_equal(key, None) )

    cnt_filters = len(filters)
    if  cnt_filters > 0:
        if cnt_filters > 1:
            # apply conjunction (n-digit operator, n > 1)
            if conjunction.lower() == 'or':
                return {'$or' : filters}
            return {'$and' : filters}
        else:
            # return dictionary with values and keys from dicts in filters
            res = {}
            for fdict in filters:
                res.update(fdict)
            return res

    return {}


############################################################
#---Results
############################################################

def split_result_ids(results):
    '''
    Split the id's into non-gridfs and gridfs id's.

    Parameters
    ----------
    results : iterable<tuple<str, bool>>
            First component is the id of the entry
            and the second a boolean indication if the result has been stored in gridfs.
            See e.g. output of :py:method:`.ResultDatabaseStorage.store_result_for_apk`

    Returns
    -------
    tuple<list<str>, list<str>>
        First component holds the non-gridfs id's, the second the gridfs id's
    '''
    non_gridfs_ids = map(lambda x : x[0], filter(lambda x :x[1] is False, results))
    gridfs_ids = map(lambda x : x[0], filter(lambda x : x[1] is True, results))

    return non_gridfs_ids, gridfs_ids

def format_query_result_db(res_cursor, distict_generator = False, count = False, raw = False, html = False):
    '''
    Format the results from the result db (mongodb).

    Parameters
    ----------
    res_cursor : gridfs.grid_file.GridOutCursor or generator<object> or pymongo.cursor.Cursor
        First if non_document and non_document_raw.
        Second if distinct values wanted.
        Thirst otherwise.
    distict_generator : bool, optional (default is False)
        Res is generator<object> created from the distinct(...) method of mongodb.
        If generaor<dict>, convert each dict to json.
        Otherwise just print.
    count : bool, optional (default is False)
        Only print count, not results
    raw : bool, optional (default is False)
        Print raw data from gridfs
        Otherwise print json.
        If `raw` will not be converted to html!
    html : bool, optional (default is False)
        Format as html.

    Returns
    -------
    str
    '''
    from pymongo.errors import PyMongoError
    from androlyze.ui.util import HtmlUtil

    # if html enabled convert to table view if `json2html` is present
    # otherwise use pygmentize
    json_convert = lambda json : json
    if html:
        try:
            from json2html import json2html
            json_convert = lambda j : json2html.convert(json = j)
        except ImportError:
            from pygments import highlight
            from pygments.formatters import HtmlFormatter
            from pygments.lexers import get_lexer_by_name
            
            json_convert = lambda json: highlight(json, get_lexer_by_name('json'), HtmlFormatter())

    # collect results as list<str>
    resl = []

    def anl(text):
        ''' Append a newline '''
        # dont format raw data as html
        return '%s\n' % text if not html or raw else HtmlUtil.newline(HtmlUtil.prefy(text))

    try:
        # return count
        if count:
            cnt = 0
            
            if is_pymongo_cursor(res_cursor):
                cnt = res_cursor.count()
            elif distict_generator:
                cnt = len(list(res_cursor))
            
            return '%d' % cnt
        
        else:
            if distict_generator:
                for r in sorted(res_cursor):
                    if isinstance(r, dict):
                        r = dict2json(res_cursor)
                        resl.append(r)
                    elif isinstance(r, (str, unicode)):
                        resl.append(r)
            else:
                for i, res in enumerate(res_cursor, 1):
                    delimiter = '/* %d */' % i
                    text = HtmlUtil.newline(delimiter) if html else delimiter
                    if html: text = HtmlUtil.redify(text)
                    resl.append(text)
                    # return raw data
                    if raw:
                        # gridfs.grid_file.GridOut
                        for gridout_obj in res:
                            resl.append(gridout_obj)
                    # return json
                    else:
                        j = dict2json(res)
                        # convert json (if enabled)
                        j = json_convert(j)
                        resl.append(j)
        # return result by joining single strings
        return ''.join([anl(res_str) for res_str in resl])
    except PyMongoError as e:
        log.exception(e)

############################################################
#---Cursor stuff
############################################################

def is_pymongo_cursor(cursor):
    ''' Check if `cursor` is a mongodb cursor '''
    return isinstance(cursor, (GridOutCursor, Cursor))

if __name__ == '__main__':
    print build_checks_filter(checks_empty_list = ["foo"])
    from collections import OrderedDict
    test = OrderedDict([('script meta', OrderedDict([('name', 'CodePermissions'), ('sha256', None), ('analysis date', 'time'), ('version', '0.1')])), ('code permissions', ('code', OrderedDict([('BLUETOOTH', [{'La2dp.Vol.service$1.onReceive': ''}])])))])
    escaped = escape_keys(test)
    import json
    print json.dumps(escaped, indent = 4)
