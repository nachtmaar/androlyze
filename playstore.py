#! /usr/bin/env python
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

'''
Little helper for the `google-play-crawler`
'''

import csv
from datetime import datetime
import json
import os
from os.path import abspath
import subprocess
import sys
import time
import traceback
from collections import OrderedDict


############################################################
# Edit !                                                   #
############################################################

GOOGLE_PLAY_CRAWLER_BIN_NAME = "googleplaycrawler.jar"
GOOGLE_PLAY_CRAWLER_CONF = os.path.abspath("conf/crawler.conf")

DL_ROOT_DIR = "playstore_dl/"
# time to sleep between starting next download
DL_SLEEP_TIME = 10

############################################################
# Don't touch                                              #
############################################################

BASE_EXEC = "java -jar {} --conf {}".format(abspath(GOOGLE_PLAY_CRAWLER_BIN_NAME), GOOGLE_PLAY_CRAWLER_CONF)

GET_PACKAGES = "{} list %s -s %s -n %s -o %s".format(BASE_EXEC)
APK_DOWNLOAD = "{} download %s".format(BASE_EXEC)
LIST_CATEGORIES = "{} categories".format(BASE_EXEC)

SUBCATEGORY_TOPSELLING_FREE = "apps_topselling_free"
SUBCATEGORY_TOPSELLING_NEW_FREE = "apps_topselling_new_free"

# otherwise googleplaycrawler says "oo many results requested.*"
MAX_CNT_GPC_LISTING = 100
# the maximal offset we can supply gpc
MAX_OFFSET_GPC_LISTING = 499

def print_help():
	prog_name = sys.argv[0]

	print """Usage: %s <list
                       |download_new_all_categories <number>
                       |download_top_all_categories <number>
                       |download <category> <subcategory> <number>
                       |download_pn <package_name>
                      >\n""" % prog_name

	print """The script relies on google-play-crawler.

Be sure you have done the following steps before using this script!
1) Get it from here: https://github.com/Akdeniz/google-play-crawler
and place this script inside the googleplay directory after it has been build.
2) Set email and password in crawler.conf
3) Get androidid via "java -jar googleplaycrawler.jar -f crawler.conf checkin" and set in in the config file
4) playstore.py benutzen ;)\n"""

	print "Example: %s download WEATHER apps_topselling_new_free 2" % prog_name
	print "Example: %s download_pn a2dp.Vol" % prog_name

	print "Example: %s list" % prog_name
	print "Example: %s download_new_all_categories 10" % prog_name
	print "Example: %s download_top_all_categories 10\n" % prog_name

	print """Possible subcategories are:
	apps_topselling_paid
	apps_topselling_free
	apps_topgrossing
	apps_topselling_new_paid
	apps_topselling_new_free"""
	sys.exit(1)

def get_cagetories():
	''' Returns a list of categories available on the PlayStore '''
	proc = subprocess.Popen(LIST_CATEGORIES, shell = True, stdout=subprocess.PIPE)
	csvr = csv.DictReader(proc.stdout, delimiter=";")
	return [row["ID"] for row in csvr]

def get_package_names(category, subcategory, number = 50):
	''' Get a set of package names for the given `category` and `subcategory` '''
	# gpc can only list `MAX_CNT_GPC_LISTING` items at once -> we have to divide it into n queries
	cnt_runs = number / MAX_CNT_GPC_LISTING + 1
	offset = 0
	package_names = []
	for _ in range(1, cnt_runs + 1):

		# no more items available, limited through play store
		if offset >= MAX_OFFSET_GPC_LISTING:
			break

		# download first items
		proc = subprocess.Popen(GET_PACKAGES % (category, subcategory, min(number, MAX_CNT_GPC_LISTING), offset), shell = True, stdout=subprocess.PIPE)
		csvr = csv.DictReader(proc.stdout, delimiter=";")
		package_names.extend([row["Package"] for row in csvr])

		# next query with new offset
		offset += MAX_CNT_GPC_LISTING
		if offset > MAX_OFFSET_GPC_LISTING:
			offset = MAX_OFFSET_GPC_LISTING

	return set(package_names)

def check_n_create_dl_dir(sub_dir = "."):
	''' Check if the download directory already exists.
	Otherwise create it.

	Parameters
	----------
	sub_dirs : str
		Subdirectory to create under the root download directory.
	'''
	dl_dir = os.path.join(DL_ROOT_DIR, sub_dir)

	try:
		# create dir structure if not existing
		if not os.path.exists(dl_dir):
			os.makedirs(dl_dir)
	except OSError:
		traceback.print_exception(*sys.exc_info())

def download_apks(package_name_list, dl_root_dir = "."):
	''' Download the .apk s for the given list of pacakge names to the specified `dl_dir` (default is `DL_ROOT_DIR`) '''
	print "Downloading: %s" % ', '.join(package_name_list)
	for pn in package_name_list:
		old_cwd = os.getcwd()
		check_n_create_dl_dir(dl_root_dir)
		dl_dir = os.path.join(DL_ROOT_DIR, dl_root_dir)
		try:
			while 1:
				# change do download dir
				os.chdir(dl_dir)
				dl = subprocess.Popen(APK_DOWNLOAD % pn, shell = True, stdout = None)
				# wait for process to finish
				dl.wait()

				if dl.returncode == 0:
					break
				else:
					sys.stderr.write("Could not download %s! Retrying ...")
		except:
			traceback.print_exception(*sys.exc_info())
		finally:
			# change back to old cwd
			os.chdir(old_cwd)
		# don't be too aggressive
		print "starting next dl in %ss" % DL_SLEEP_TIME
		time.sleep(DL_SLEEP_TIME)

def download_n_all_categories(subcategory, number):
	''' Download `number` of apks from `subcategory` '''
	filename = os.path.join(DL_ROOT_DIR, 'top_%d_%s_%s.json' % (number, subcategory, datetime.now()))
	apks_dict = OrderedDict()
	# create root dl dir first
	check_n_create_dl_dir()
	with open(filename, "w") as f:
		for category in get_cagetories():
			f.seek(0)
			print "Downloading the %s apks from category: %s" % (subcategory, category)
			package_names = get_package_names(category, subcategory, number)
			apks_dict[category] = list(package_names)
			json.dump(apks_dict, f, indent = 4)
			f.flush()
			# dl dir : subcategory/category/
			dl_dir = os.path.join(subcategory, category)
			download_apks(package_names, dl_dir)
			print "\n" * 5

if __name__ == "__main__":
	args = sys.argv

	if len(args) < 2:
		print_help()

	else:
		args = sys.argv[1:]
		cmd = args[0]

		if cmd == "download":
			if len(args) != 4:
				print_help()

			category, subcategory, number = args[1:]
			number = int(number)

			package_names = get_package_names(category, subcategory, number)
			print "packages: %s" % ', '.join(package_names)
			dl_dir = os.path.join(category, subcategory)
			download_apks(package_names, dl_dir)
		elif cmd == "list":
			print '\n'.join(get_cagetories())
		elif cmd == "download_pn":
			if len(args) != 2:
				print_help()
			package_name = args[1]
			download_apks([package_name])
		elif cmd in ("download_new_all_categories", "download_top_all_categories"):
			if len(args) != 2:
				print_help()

			number = args[1]
			number = int(number)

			if cmd == "download_new_all_categories":
				download_n_all_categories(SUBCATEGORY_TOPSELLING_NEW_FREE, number)
			elif cmd == "download_top_all_categories":
				download_n_all_categories(SUBCATEGORY_TOPSELLING_FREE, number)
		else:
			print "Unknown command!"
			print_help()
