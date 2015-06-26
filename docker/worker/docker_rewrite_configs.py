#!/usr/bin/env python


# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

import sys


# DO not move this line under androlyze specific imports!
sys.path.append(".")

from androlyze.docker.dynamic_config import rewrite_configs

rewrite_configs()
