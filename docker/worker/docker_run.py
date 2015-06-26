#!/usr/bin/env python


# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys


# DO not move this line under androlyze specific imports!
sys.path.append(".")

from androlyze.docker.start_worker import start_workers

start_workers()