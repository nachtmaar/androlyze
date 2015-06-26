
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import collections
from copy import deepcopy
from os.path import join


def get_apk_path(package_name, version_name, _hash):
    '''
    Returns the sub path structure by supplying all arguments needed for it.

    The structure is:
    ...
    |-> package
      |-> version
        |-> sha256

    Parameters
    ----------
    package_name : str
        Package name of the apk.
        Unique apk identifier (at least in the store)
    version_name : str
        Version name
    _hash : str
        The hash of the apk.

    Returns
    -------
    str: path
    '''
    return join(package_name, version_name, _hash)

def get_apk_path_incl_filename(apk):
    '''
    Returns the sub path structure by supplying all arguments needed for it.

    The structure is:
    ...
    |-> package
      |-> version
        |-> sha256

    Parameters
    ----------
    apk : Apk

    Returns
    -------
    str: path
    '''
    return join(get_apk_path(apk.package_name, apk.version_name, apk.hash), apk.get_apk_filename_from_manifest())


def escape_dict(_dict, escape_fct, escape_keys = True, escape_values = False):
    ''' Escape the keys and/or values  in the `_dict` with `escape_fct`.

    Will do a deepcopy of the `dict`!
    So escaping isn't in-place!

    Parameters
    ----------
    _dict : dict
    escape_fct : object -> object
        Escape function for key or value
    escape_keys : bool, optional (default is True)
        Apply `escape_fct` on keys
    escape_values : bool, optional (default is False)
        Apply `escape_fct` on values.

    Returns
    -------
    dict
    '''
    replaced = deepcopy(_dict)

    def escape_keys2(dicts):
        ''' Does in-place breadth-first escaping of keys that hold a dict.

        Parameters
        ----------
        dicts : list<dict>
        '''
        for _dict in dicts:
            breadth_dicts = []
            for key, val in _dict.items():
                # delete old key
                # shouldn't cause any troubles because we're running over a new list (items())
                del _dict[key]
                # store value under new key
                key_cpy, val_cpy = key, val
                if escape_keys:
                    key_cpy = escape_fct(key)
                if escape_values:
                    val_cpy = escape_fct(val)
                _dict[key_cpy] = val_cpy

                # check if value is dict -> escape
                # iterable structures despite strings may contain dict's too
                def check_n_append_dict(elm):
                    # dict found
                    if isinstance(elm, dict):
                        breadth_dicts.append(elm)
                    # check iterable structure
                    elif not isinstance(elm, (str, unicode)) and isinstance(elm, collections.Iterable):
                        for elm2 in elm:
                            check_n_append_dict(elm2)

                check_n_append_dict(val)


            escape_keys2(breadth_dicts)

    # replace in-place
    escape_keys2([replaced])

    return replaced
