#!/usr/bin/env python
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Intelligent apk updater,
downloading only the ones that need to be updated.
Due to this we have to query the database for existing versions
and then check the internet for the current one.
'''

import sys
import time
from playstore import download_apks
from playversion import get_apk_version
import androlyze

def get_outdated(import_db_name, packages):
	''' Query the `import_db_name` to get the imported versions
	and return the outdated ones.

	Returns
	-------
	generator<str>
	'''
	from androlyze.storage.RedundantStorage import RedundantStorage
	storage = RedundantStorage(import_db_name, "")

	for pn in packages:
		print "checking %s" % pn
		db_versions = androlyze.action_query_import_db(storage, androlyze.COMMAND_QUERY_VERSIONS, package_names = [pn.strip()])	
		if not get_apk_version(pn) in db_versions:
			yield pn

def update_packages(import_db_name, package_names):
	''' Update all `package_names`.

	Query the `import_db_name` to get the imported versions
	and check wether a new one is available and download it.

	Parameters
	----------
	import_db_name : str
	package_names : iterable<str>
	'''	
	updated = 0
	for pn in package_names:
		pns = [pn]
		for outdated_pn in get_outdated(import_db_name, pns):
			print "Updating %s ... " % outdated_pn
			download_apks(pns)
			updated += 1
	return updated

def controlled_update_packages(import_db_name, package_names, DLS_PER_INTERVAL = sys.maxint, SLEEP_TIME = 0):
	''' Same as `update_packages` but try
	to be not so aggressive with downloading (at least if specified via parameters)

	Parameters
	----------
	import_db_name : str
	package_names : iterable<str>
	DLS_PER_INTERVAL : int, optional (default is sys.maxint)
		Controls how much updates will be tried until to sleep ``SLEEP_TIME`
	SLEEP_TIME : int, optional (default is 0)
		Sleep `SLEEP_TIME`
	'''

	TOTAL_LENGTH = len(package_names)

	# try only to update DLS_PER_INTERVAL apks (at most)
	for x in xrange(0, TOTAL_LENGTH, DLS_PER_INTERVAL):
		day_package_names = package_names[x:x+DLS_PER_INTERVAL]

		cnt_updated = 0
		# check 10 if they need to get updated and do it
		n = 10
		for i in xrange(0, len(day_package_names), n):
			cnt_updated += update_packages(import_db_name, day_package_names[i:i+n])

		print "Updated %s/%s" % (cnt_updated, len(day_package_names))

		# pause for some time
		print "sleeping for %s seconds" % SLEEP_TIME
		time.sleep(SLEEP_TIME)

if __name__ == '__main__':
	from argparse import ArgumentParser
	parser = ArgumentParser(description = "Reads the package names from stdin. So use e.g. ./androquery package-names| <call to this script>")

	parser.add_argument(dest = "import_db_name", help ="The import database to query for imported versions")
	cd = parser.add_argument_group("controlled donwloading")
	cd.add_argument("--dls-per-step", "-dps", dest = "dls_per_step", type = int, default = sys.maxint, help ="Specifies how much updated will be tried, until to sleep some time [default: %(default)s]")
	cd.add_argument("--sleep-time", "-st", dest = "sleep_time", type = int, default = 0, help ="Specify how long to sleep until to update the next packages [default: %(default)s]")
	args = parser.parse_args()

	# xargs adds newline
	print controlled_update_packages(args.import_db_name, [x.strip() for x in list(sys.stdin)], args.dls_per_step, args.sleep_time)
	
