
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from collections import OrderedDict
import json

from androlyze.model.analysis.result.exception import KeyNotRegisteredError

class ResultObject(object):
    '''
    This class is intended to be used for a consistent storage of the analysis results.
    It's a wrapper around a dictionary and enables you to store any json serializable data types.
    For a more structured way of storing the results you can group them into different categories.

    Before you can log any data, you have to register the keys as well as the categories if you want to use them.
    The order in which you register the keys will be kept and used for JSON export.

    You don't have to register all keys iterative, just give a list of categories to create the structure at once.
    '''

    def __init__(self, apk = None):
        '''
        If no `apk` set, `self.description_dict` will not output infos about it!

        Parameters
        ----------
        apk: Apk, optional (default is None)
        '''
        self.__results = OrderedDict()
        self.__apk = apk

    def __str__(self):
        return str(self.description_dict())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.apk)

    def __eq__(self, other):
        return self.description_dict() == other.description_dict()

    def __ne__(self, other):
        return not self == other

    def get_apk(self):
        return self.__apk

    def set_apk(self, value):
        self.__apk = value

    def del_apk(self):
        del self.__apk

    def get_results(self):
        return self.__results

    def set_results(self, value):
        self.__results = value

    def del_results(self):
        del self.__results

    results = property(get_results, set_results, del_results, "OrderedDict : stores the results")
    apk = property(get_apk, set_apk, del_apk, "apk : the APK file for which the results will be collected ")

    ############################################################
    #---Container magic methods
    ############################################################

    def __len__(self):
        return len(self.results)

    def __getitem__(self, key):
        return self.results[key]

    def __setitem__(self, name, value):
        self.results[name] = value

    def __delitem__(self, key):
        del self.results[key]

    def __iter__(self):
        return iter(self.results)

    def __contains__(self, item):
        return item in self.results

    ############################################################
    #---Logging stuff
    ############################################################

    def register_keys(self, keys, *categories):
        ''' Register the `keys` under the given `categories` (will be set to None).

        Parameters
        ----------
        keys : list<str>
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.
        '''
        for key in keys:
            self.__log(key, None, self.__dict_assignment, *categories, register_key = True)

    def register_bool_keys(self, keys, *categories):
        ''' Register the `keys` under the given `categories` (will be set to False).

        Parameters
        ----------
        keys : list<str>
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.
        '''
        for key in keys:
            self.__log(key, False, self.__dict_assignment, *categories, register_key = True)

    def register_enum_keys(self, keys, *categories):
        ''' Register the `keys` under the given `categories` (will be set to []).

        Parameters
        ----------
        keys : list<str>
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.
        '''
        for key in keys:
            self.__log(key, [], self.__dict_assignment, *categories, register_key = True)

    def log(self, key, value, *categories):
        ''' Store the `value` for the given `key`.

        You can pass a list of categories to group the log entries.

        Parameters
        ----------
        key: object
        value: json serializable
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.

        Raises
        ------
        KeyNotRegisteredError
            If the key has not been registered first.
        '''
        self.__log(key, value, self.__dict_assignment, *categories)

    def log_true(self, key, *categories):
        '''
        Log a boolean value for the `key` under the given `categories`.

        Parameters
        ----------
        key: object
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.

        Raises
        ------
        KeyNotRegisteredError
            If the key has not been registered first.
        '''
        self.__log(key, True, self.__dict_assignment, *categories)

    def log_append_to_enum(self, key, value, *categories):
        ''' Append the `value` to the list under the given `key`.

        You can pass a list of categories to group the log entries.

        Parameters
        ----------
        key: object
        value: json serializable
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.

        Raises
        ------
        KeyNotRegisteredError
            If the key has not been registered first.
        '''
        self.__log(key, value, self.__dict_list_append, *categories)

    ############################################################
    #--Import/export stuff
    ############################################################

    def write_to_json(self):
        ''' Returns a json representation as str '''
        from androlyze.model.script import ScriptUtil
        return ScriptUtil.dict2json(self.description_dict())

    @staticmethod
    def load_from_json(json_str):
        ''' Load an `ResultObject` from json string.
        This works by cutting off the meta information.

        Don't forget to link it to the corresponding `Apk` class!

        Parameters
        ----------
        json_str : str

        Returns
        -------
        ResultObject
        '''
        from androlyze.model.analysis.result.StaticResultKeys import RESOBJ_APK_META
        res = ResultObject(None)
        res.results = json.loads(json_str, object_pairs_hook = OrderedDict)
        del res[RESOBJ_APK_META]
        return res

    def description_dict(self):
        ''' Returns a dict with meta information about the `Apk` added to the `ResultObject`.
        At least if `ResultObject` is linked to an `Apk` '''
        meta_dict = OrderedDict()

        # if linked to `Apk` print the meta information to
        if self.apk is not None:
            meta_dict = self.apk.meta_dict()
        meta_dict.update(self.results)
        return meta_dict

    ############################################################
    #---Private implementation
    ############################################################


    def __log(self, key, value, func, *categories, **kwargs):
        ''' Store the `value` for the given `key`.

        You can pass a list of categories to group the log entries.

        Parameters
        ----------
        key: object
        value: json serializable
        func: (dict, object, object)
            The function to use for logging.
        categories: object
            Can be used to group the results into different categories.
            The string representation will be used for the category name.

        Other Parameters
        ----------------
        register_key : bool, default is false
            If true, set a value for the key although the key has not been registered.
            Can be used to register the key.

        Raises
        ------
        KeyNotRegisteredError
            If the key has not been registered first and `register_keys` is false.
        ValueError
            If an empty category has been supplied.
        '''
        register_key = kwargs.get("register_key", False)

        if None in categories:
            raise ValueError("You supplied an empty category: %s" % ', '.join([str(x) for x in categories]))

        def log2(_dict, key, value, *sub_categories):
            cnt_categories = len(sub_categories)
            # category logging
            if cnt_categories >= 1:
                category = sub_categories[0]
                category_name = str(category)
                # create sub dictionary for category if not already present and shall be registered
                category_in_dict = category_name in _dict
                category_val_none = category_in_dict and _dict[category_name] is None
                # either already registered None to category or category not yet registered
                if category_val_none or not category_in_dict:
                    self.__check_n_set_value_for_key(_dict, category_name, OrderedDict(), self.__dict_assignment, register_key, *categories)

                sub_dict = _dict[category_name]

                if cnt_categories > 1:
                    # category not present, create it and run into recursion
                    # to check sub categories
                    log2(sub_dict, key, value, *sub_categories[1:])
                # reached last category, create entry
                elif cnt_categories == 1:
                    self.__check_n_set_value_for_key(sub_dict, key, value, func, register_key, *categories)
            # == 0, no category given, set value for key directly
            else:
                self.__check_n_set_value_for_key(_dict, key, value, func, register_key, *categories)

        log2(self, key, value, *categories)

    @staticmethod
    def __dict_assignment(_dict, key, val):
        _dict[key] = val

    @staticmethod
    def __dict_list_append(_dict, key, val):
        _dict[key].append(val)

    @staticmethod
    def __check_n_set_value_for_key(res_dict, key, value, func, register_key, *categories):
        ''' Check if the key is already present or shall be registered.
        In this case apply the `func` on the value, key and dictionary.
        Otherwise raise an Exception.

        Parameters
        ----------
        func: (dict, object, object)
            The function which shall be applied.

        Raises
        ------
        KeyNotRegisteredError
        '''
        if key in res_dict or register_key:
            func(res_dict, key, value)
        else:
            raise KeyNotRegisteredError(key, *categories)

if __name__ == '__main__':
    from androlyze.model.android.apk.FastApk import FastApk
    from datetime import datetime

    # we will link the `ResultObject` to an `Apk` to see it's meta information
    # but we don't need to link against any `Apk` !
    apk = FastApk("com.foo.bar", "1.0", "/", "some hash", datetime.utcnow(), tag ="exploitable")
    res = ResultObject(apk)

    res.register_bool_keys(["check1", "check2"])

    # register enumeration keys
    res.register_enum_keys(["activities", "content providers", "broadcast receivers", "services"], "components")

    # this shows how you can abstract categories, in this example into a tuple
    # the important point is that you need to unpack it with "*" !
    ROOT_CAT = ("apkinfo", "listings")
    res.register_keys(["files"], *ROOT_CAT)

    print res.write_to_json()

    # log
    res.log_true("check1")
    res.log_true("check2")

    # append to enumeration
    res.log_append_to_enum("activities", "activity1", "components")
    res.log_append_to_enum("activities", "activity2", "components")
    res.log_append_to_enum("activities", "activity3", "components")

    # or log whole structure
    res.log("files", ["file%s" % i for i in range(1, 10)], *ROOT_CAT)
    print res.write_to_json()
