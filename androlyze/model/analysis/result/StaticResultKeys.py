
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Holds the keys used to generated the static structure of the analysis results.

All keys are prefixed with `RESOBJ_`.

'''

from androlyze.model.Hashable import Hashable

# keys for script meta infos
RESOBJ_SCRIPT_META = "script meta"
RESOBJ_SCRIPT_META_NAME = "name"
RESOBJ_SCRIPT_META_VERSION = "version"

# additional meta infos for script
RESOBJ_SCRIPT_META_ANALYSIS_DATE = "analysis date"
RESOBJ_SCRIPT_META_HASH = "sha256"
RESOBJ_SCRIPT_META_TIME_TOTAL = "time total"
RESOBJ_SCRIPT_META_TIME_SCRIPT = "time script"
RESOBJ_SCRIPT_META_ANALYZE_TIME = "time androguard open"

RESOBJ_APK_META = "apk meta"
RESOBJ_APK_META_PACKAGE_NAME = "package name"
RESOBJ_APK_META_VERSION_NAME = "version name"
RESOBJ_APK_META_IMPORT_DATE = "import date"
RESOBJ_APK_META_BUILD_DATE = "build_date"
RESOBJ_APK_META_TAG = "tag"
RESOBJ_APK_META_PATH = "path"
RESOBJ_APK_META_HASH = Hashable.KEY_HASH

# monbodb's id field
RESOBJ_ID = "_id"
