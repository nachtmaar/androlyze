
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.storage.ResultWritingInterface import ResultWritingInterface

class ResultStorageInterface(ResultWritingInterface):
    ''' Interface for the result storage '''

    def get_results(self,
                    include_fields = None, exclude_fields = None,
                    where = None, distinct_key = None,
                    n = None, sort = True, latest = False,
                    non_document = False, non_document_raw = False,
                    remove_id_field = True,
                    **kwargs):
        '''
        Get results from the database.

        Parameters
        ----------
        include_fields : list<str>, optional (default is [])
            List of fields to include in the result.
            Mutually exclusive with `exclude_fields`.
        exclude_fields : list<str>, optional (default is [])
            List of fields to exclude from the result.
            Mutually exclusive with `include_fields`.
        where : dict, optional (default is {})
            A filter.
        distinct_key : str, optional (default is None)
            If given, list the distinct values for the `distinct_key.
        sort : bool, optional (default is True)
            If true sort by analysis date.
        latest : bool, optional (default is False)
            Get the result of the latest script run.
            Will only return one result.
        n : int, optional (default is None)
            Number of results to return.
            None means no limit.
        non_document : bool, optional (default is False)
            Get custom data from mongodb's gridfs.
        non_document_raw : bool, optional (default is False)
            Get the raw data from the database. Otherwise meta infos will be returned.
            Only interesting if `non_document`.
        remove_id_field : bool, optional (default is True)
            Will remove the `_id` field by default.

        Other Parameters
        ----------------
        package_name : str, optional (default is None)
        apk_hash : str, optional (default is None)
        version_name : str, optional (default is None)
        tag : str, optional (default is None)

        script_hash : str, optional (default is None)
        script_name : str, optional (default is None)
        script_version : str, optional (default is None)

        Notes
        -----
        If any of the other parameters is None it won't be used for filtering.

        Returns
        -------
        gridfs.grid_file.GridOutCursor
            If non_document and non_document_raw.
        pymongo.cursor.Cursor
            Otherwise
        generator<object>
            If `distinct_key`

        Raises
        ------
        DatabaseLoadException
        '''
        raise NotImplementedError

    def get_results_for_ids(self, ids, non_document = False, non_document_raw = False):
        '''
        Get the results for the specified `ids`.

        Parameters
        ----------
        ids : iterable<str>
            The ids to fetch the results for.
        non_document : bool, optional (default is False)
            If `non_document` fetch results from gridfs.
        non_document_raw : bool, optional (default is False)
            Get the raw data from the database. Otherwise meta infos will be returned.
            Only interesting if `non_document`.
            Means return `GridOutCursor` instead of fetching from metdata from files collection.

        Returns
        -------
        gridfs.grid_file.GridOutCursor
            If `non_document`.
        pymongo.cursor.Cursor
            Otherwise

        Raises
        ------
        DatabaseLoadException
        '''
        raise NotImplementedError

    def delete_results(self,
                       where = None, non_document = False, **kwargs):
        '''
        Delete some results from the database.

        Parameters
        ----------
        where : dict, optional (default is {})
            A filter.
        non_document : bool, optional (default is False)
            Remove from gridfs.

        Other Parameters
        ----------------
        package_name : str, optional (default is None)
        apk_hash : str, optional (default is None)
        version_name : str, optional (default is None)
        tag : str, optional (default is None)

        script_hash : str, optional (default is None)
        script_name : str, optional (default is None)
        script_version : str, optional (default is None)

        Notes
        -----
        If any of the other parameters is None it won't be used for filtering.
        They may will also overwrite the other ones.

        Returns
        -------
        int
            Number of documents which have been removed.
        '''
        raise NotImplementedError

    def erase_whole_db(self):
        '''
        Use to drop collections and recreate them.
        '''
        raise NotImplementedError