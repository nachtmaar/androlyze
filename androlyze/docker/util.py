
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import os

from androlyze.log.Log import clilog

def run(command):
    clilog.info(">>> %s", command)
    return os.system(command)
