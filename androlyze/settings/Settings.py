
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import ConfigParser
from os.path import abspath, expanduser
import sys

from androlyze.settings.exception import ConfigFileNotFoundError, ConfigError

class Settings(object):
    ''' This class is a wrapper around a `ConfigParser` to retrieve and write settings in a more convenient way.

    For (over)writing settings, be sure to use the with construct! Otherwise the file handle will not be closed.

    Examples
    --------
    >>> # just for doctest passing tests (file needs to exist)
    >>> f = open("test.conf", "w")
    >>> f.close()

    >>> # the entries
    >>> entry = ("SectionName", "Option1")
    >>> entry2 = ("SectionName", "Option2")
    >>> entry3 = ("SectionName2", "Option1")

    >>> # If you want to write some settings use the with construct to close the file after writing!
    >>> s = None
    >>> try:
    ...     with Settings("test.conf") as s:
    ...         s[entry] = "value1"
    ...         s[entry2] = "value2"
    ...         s[entry3] = "value1"
    ... except ConfigFileNotFoundError as e:
    ...     pass
    ... finally:
    ...     print s
    Settings: SectionName : [('option1', 'value1'), ('option2', 'value2')], SectionName2 : [('option1', 'value1')]

    >>> # read settings
    >>> try:
    ...     print s[entry]
    ...     print len(s)
    ...     print entry in s
    ...     for section, items in s:
    ...         print '%s : %s' % (section, items)
    ... except ConfigFileNotFoundError:
    ...     pass
    value1
    3
    True
    SectionName : [('option1', 'value1'), ('option2', 'value2')]
    SectionName2 : [('option1', 'value1')]
    '''

    def __init__(self, config_path, default_path = None, *args, **kwargs):
        '''
        The file under `config_path` has to exists (at least if no `default_path` has been given).

        Parameters
        ----------
        config_path : str
            The path to the config file
        default_path : str, optional (default is None).
            The path to the config file with default values.
            None means don't load default values.

        Raises
        ------
        ConfigFileNotFoundError
            If the config file could not be opened.
        '''
        super(Settings, self).__init__()
        self.__config_parser = ConfigParser.ConfigParser(*args, **kwargs)
        self.__config_path = config_path
        # file pointer for writing
        self.__fp_write = None

        # try to open the config files
        try:
            if default_path is not None:
                with open(default_path, "r") as fp:
                    self.__config_parser.readfp(fp)

            try:
                with open(config_path, "r") as fp:
                    self.__config_parser.readfp(fp)
            except IOError:
                # only throw exception that config has not been found if no default config specified
                if default_path is None:
                    raise

        except (IOError,ConfigParser.Error) as e:
                raise ConfigFileNotFoundError(abspath(config_path), e), None, sys.exc_info()[2]

    def __str__(self):
        return 'Settings: %s' % '\n\t'.join(('%s : %s' % (section, key_val_list) for section, key_val_list in self))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.__config_path)

    def get_config_parser(self):
        return self.__config_parser

    def set_config_parser(self, value):
        self.__config_parser = value

    def del_config_parser(self):
        del self.__config_parser

    config_parser = property(get_config_parser, set_config_parser, del_config_parser, "ConfigParser : the parser for the config file")

    ############################################################
    #---With support
    ############################################################

    def __enter__(self):
        try:
            # open file
            self.__fp_write = open(self.__config_path, "w")
            return self
        except IOError as e:
            raise ConfigFileNotFoundError(abspath(self.__config_path), e), None, sys.exc_info()[2]

    def __exit__(self, _type, value, traceback):
        try:
            self.__config_parser.write(self.__fp_write)
        except IOError as e:
            raise ConfigFileNotFoundError(abspath(self.__config_path), e), None, sys.exc_info()[2]
        finally:
            # close file pointer
            self.__fp_write.close()

    ############################################################
    #---Container magic methods
    ############################################################

    def __len__(self):
        ''' Count number of entries for each section and sum it up '''
        return sum((len(items) for _, items in self))

    def __getitem__(self, key, default = 'default_val'):
        '''
        Get an value from a section and option.

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option
        default : str, optional (default is 'default_val')
            If not found, return the `default` value.
            If value is the default, an exception will be raised.
            You can also use None as a default value.

        Raises
        ------
        ConfigError
            If `default` not customized.
        '''
        section, option = key
        try:
            return self.config_parser.get(section, option)
        except ConfigParser.Error as e:
            # no default value given
            if default == 'default_val':
                raise ConfigError('%s: %s' % (e, self.__config_path)), None, sys.exc_info()[2]
            return default

    def __setitem__(self, key, value):
        '''
        Set a value for a section and option.

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option

        Raises
        ------
        ConfigError
        '''
        try:
            section, option = key
            cp = self.config_parser
            # create section if not already present
            if not cp.has_section(section):
                cp.add_section(section)
            self.config_parser.set(section, option, value)
        except ConfigParser.Error as e:
            raise ConfigError(e), None, sys.exc_info()[2]

    def __delitem__(self, key):
        '''Delete the option from the section but not the section!.

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option

        Raises
        ------
        ConfigError
        '''
        section, option = key
        try:
            self.config_parser.remove_option(section, option)
        except ConfigParser.Error as e:
            raise ConfigError(e), None, sys.exc_info()[2]

    def __iter__(self):
        ''' Get a generator over the settings.

        Returns
        -------
        generator<tuple<str, list< tuple<str, str> >>>
             Generator over settings with the section as first entry and list of tuples with option and value as second.

        Raises
        ------
        ConfigError
        '''

        cp = self.config_parser
        try:
            section = cp.sections()
            for s in section:
                yield s, cp.items(s)
        except ConfigParser.Error as e:
            raise ConfigError(e), None, sys.exc_info()[2]

    def __contains__(self, item):
        ''' Check if the section has the specified option.

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option
        '''
        try:
            return self[item]
        except (ConfigParser.Error, KeyError):
            return False
        return True

    ############################################################
    #--Other return types
    ############################################################

    def get_int(self, key, **kwargs):
        '''
        Get an int value from a section and option.

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option

        Other Parameters
        ----------------
        default : str, optional (default is 'default_val')
            If not found, return the `default` value.
            If value is the default, an exception will be raised.
            You can also use None as a default value.

        Raises
        ------
        ConfigError
            If `default` not customized.
        '''
        res = self.__getitem__(key, **kwargs)
        # probably default value
        if res is None:
            return res
        return int(res.strip())

    def get_bool(self, key, **kwargs):
        '''
        Get an boolean value from a section and option.

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option

        Other Parameters
        ----------------
        default : str, optional (default is 'default_val')
            If not found, return the `default` value.
            If value is the default, an exception will be raised.
            You can also use None as a default value.

        Raises
        ------
        ConfigError
            If `default` not customized.
        '''
        res = self.__getitem__(key, **kwargs)
        if isinstance(res, str):
            return res.lower().strip() in ('true', 'y', 'yes')
        # probably default value
        return res

    def get_list(self, key, **kwargs):
        '''
        Get an list value from a section and option.
        Values have to be comma separated (without " or ').

        Parameters
        ----------
        key : tuple<str, str>
             First argument is the section and the second the option

        Other Parameters
        ----------------
        default : str, optional (default is 'default_val')
            If not found, return the `default` value.
            If value is the default, an exception will be raised.
            You can also use None as a default value.

        Raises
        ------
        ConfigError
            If `default` not customized.
        '''
        res = self.__getitem__(key, **kwargs)
        if isinstance(res, str):
            # split into values and return list
            return map(lambda x : x.strip(), res.split(","))

        # probably default value
        return res

    ############################################################
    #---AndroLyzeLab specific
    ############################################################

    def get_mongodb_settings(self):
        ''' Get mongodb settings.
        Username and password are set to None if not given '''
        import androlyze.settings as s
        mongodb_name = self[(s.SECTION_RESULT_DB, s.KEY_RESULT_DB_NAME)]

        mongodb_ip = self[(s.SECTION_RESULT_DB, s.KEY_RESULT_DB_IP)]
        mongodb_port = self.get_int((s.SECTION_RESULT_DB, s.KEY_RESULT_DB_PORT))
        mongodb_username = self.__getitem__((s.SECTION_RESULT_DB, s.KEY_RESULT_DB_AUTH_USERNAME), default = None)
        mongodb_passwd = self.__getitem__((s.SECTION_RESULT_DB, s.KEY_RESULT_DB_AUTH_PASSWD), default = None)
        mongodb_use_ssl = self.get_bool((s.SECTION_RESULT_DB, s.KEY_RESULT_DB_USE_SSL))
        mongodb_ca_cert = self[(s.SECTION_RESULT_DB, s.KEY_RESULT_DB_CA_CERT)]

        return mongodb_name, mongodb_ip, mongodb_port, mongodb_username, mongodb_passwd, mongodb_use_ssl, mongodb_ca_cert
    
    def get_s3_settings(self):
        ''' Get S3 settings '''
        import androlyze.settings as s
        aws_access_key_id = self[(s.SECTION_S3_STORAGE, s.KEY_S3_STORAGE_AWS_ACCESS_KEY_ID)]
        aws_secret_access_key = self[(s.SECTION_S3_STORAGE, s.KEY_S3_STORAGE_AWS_SECRET_ACCESS_KEY)]
        aws_apk_bucket = self[(s.SECTION_S3_STORAGE, s.KEY_S3_STORAGE_AWS_APK_BUCKET)]
        aws_s3_host = self.__getitem__((s.SECTION_S3_STORAGE, s.KEY_S3_STORAGE_AWS_HOST_URL), default = None)

        return aws_access_key_id, aws_secret_access_key, aws_apk_bucket, aws_s3_host
    
    def get_apk_storage_engine(self):
        ''' Get the apk storage engine. See keys settings.APK_STORAGE_ENGINE_* '''
        import androlyze.settings as s
        return self[(s.SECTION_APK_DISTRIBUTED_STORAGE, s.KEY_APK_STORAGE_ENGINE)]

    def get_celery_broker_ssl_opts(self):
        ''' Create dictionary which can be directly passed to `BROKER_USE_SSL` celery config '''
        from androlyze.settings import SECTION_BROKER, KEY_BROKER_USE_SSL,\
            KEY_BROKER_SSL_CA_CERT, KEY_BROKER_SSL_CLIENT_AUTH,\
            KEY_BROKER_SSL_CLIENT_KEYFILE, KEY_BROKER_SSL_CLIENT_CERT
        import ssl as s

        ssl = {}
        if self.get_bool((SECTION_BROKER, KEY_BROKER_USE_SSL)):
            ssl['ca_certs'] = expanduser(self[(SECTION_BROKER, KEY_BROKER_SSL_CA_CERT)])
            ssl['cert_reqs'] = s.CERT_NONE

            # client authentication
            if self.get_bool((SECTION_BROKER, KEY_BROKER_SSL_CLIENT_AUTH)):

                ssl['keyfile'] = expanduser(self[(SECTION_BROKER, KEY_BROKER_SSL_CLIENT_KEYFILE)])
                ssl['certfile'] = expanduser(self[(SECTION_BROKER, KEY_BROKER_SSL_CLIENT_CERT)])
                ssl['cert_reqs'] = s.CERT_REQUIRED

        return ssl

    def script_hash_validation_enabled(self):
        # prevent import error
        from androlyze.settings import SECTION_ANALYSIS, KEY_ANALYSIS_SCRIPT_HASH_VALIDATION
        return self[(SECTION_ANALYSIS, KEY_ANALYSIS_SCRIPT_HASH_VALIDATION)]
    
    
