
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import logging
import sys

from androlyze.Constants import PROJECT_NAME

LEVEL_NOLOG = logging.CRITICAL + 1
log = logging.getLogger(PROJECT_NAME)
log.setLevel(logging.INFO)

# formatter for logging to file
FILE_LOG_FORMAT_STR = "%(name)s %(levelname)s %(module)s.%(funcName)s:%(asctime)s: %(message)s"
# formatter for console logging (stderr)
STDERR_FORMAT_STR = "%(levelname)s: %(message)s"

def __get_log_steamhandler():
    formatter = logging.Formatter(STDERR_FORMAT_STR)
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.DEBUG)
    streamhandler.setFormatter(formatter)
    return streamhandler

streamhandler = __get_log_steamhandler()
log.addHandler(streamhandler)

def log_set_level(log_level):
    log.setLevel(log_level)

def redirect_to_file_handler(filename, loglevel):
    if filename is not None:
        handler_file = logging.FileHandler(filename)
        hff = logging.Formatter(FILE_LOG_FORMAT_STR)
        handler_file.setLevel(loglevel)
        handler_file.setFormatter(hff)
        log.addHandler(handler_file)
        clilog.addHandler(handler_file)

def disable_logger(logger):
    logger.setLevel(LEVEL_NOLOG)

def get_cli_streamhandler():
    FILE_LOG_FORMAT_STR = "%(message)s"
    clilog_formatter = logging.Formatter(FILE_LOG_FORMAT_STR)
    clilog_handler = logging.StreamHandler(sys.stdout)
    clilog_handler.setLevel(logging.INFO)
    clilog_handler.setFormatter(clilog_formatter)
    return clilog_handler


''' Logs to stdout '''
clilog = logging.getLogger('cli_info_logger')
clilog.setLevel(logging.INFO)
clilog.addHandler(get_cli_streamhandler())

def clilog_set_level(log_level):
    clilog.setLevel(log_level)

def disable_std_loggers():
    disable_logger(log)
    disable_logger(clilog)
