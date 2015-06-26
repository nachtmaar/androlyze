
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from androlyze.error.AndroLyzeLabError import AndroLyzeLabError


class WrapperException(AndroLyzeLabError):
    '''
    Exception for simulating the caused by behavior known from java.
    So that one knows why the exception has been reraised.

    Overwrite `_msg` in a subclass.

    Examples
    --------
    >>> try:
    ...     raise WrapperException(caused_by = ValueError("some error msg"))
    ... except Exception as e:
    ...     print e
    WrapperException:
        Caused by: ValueError: some error msg

    >>> # specify custom exception message
    ... try:
    ...     raise WrapperException(caused_by = ValueError("some error msg"), msg = "exception message")
    ... except Exception as e:
    ...     print e
    WrapperException: exception message
        Caused by: ValueError: some error msg

    >>> class WrapperExceptionSubclass(WrapperException):
    ...     def _msg(self):
    ...         return "Overwritten error message"
    ... try:
    ...     raise WrapperException(caused_by = WrapperExceptionSubclass(), msg = "exception message")
    ... except Exception as e:
    ...     print e
    WrapperException: exception message
        Caused by: WrapperExceptionSubclass: Overwritten error message

    >>> # shows all caused_by
    ... try:
    ...     raise WrapperException(caused_by = WrapperExceptionSubclass(caused_by = WrapperExceptionSubclass(), msg = "exception message"))
    ... except Exception as e:
    ...     print e
    WrapperException:
        Caused by: WrapperExceptionSubclass: exception message
        Caused by: WrapperExceptionSubclass: Overwritten error message
    '''


    def __init__(self, msg = None, caused_by = None):
        '''
        Parameters
        ----------
        caused_by: Exception, optional (default is None)
            Exception that caused this one to raise.
            If non given, no caused-by message will be appended.
        msg : str, optional (default is None)
            If given, use the `msg` instead of the result of `__str__`.
        '''
        super(WrapperException, self).__init__()
        self.caused_by = caused_by
        self.msg = msg

    def __str__(self):

        msg = None
        if self.msg is not None:
            msg = self.msg
        else:
            msg = self._msg()

        caused_by_msg = None
        if isinstance(self.caused_by, WrapperException):
            caused_by_msg = str(self.caused_by)
        else:
            caused_by_msg =  '%s: %s' % (self.caused_by.__class__.__name__, str(self.caused_by))

        base_msg = '%s: %s' % (self.__class__.__name__, msg)

        if self.caused_by is None:
            return base_msg
        return '%s\n\tCaused by: %s' % (base_msg, caused_by_msg)

    def _msg(self):
        ''' Overwrite this method in a subclass. It's supposed to hold the exception message '''
        return ""

