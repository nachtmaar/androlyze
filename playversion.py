#!/usr/bin/python
# coding=utf-8

# encoding: utf-8

__author__ = "Lars Baumgärtner "
__email__ = "lbaumgaertner at informatik.uni-marburg.de"

import httplib, urllib, simplejson, sys, getopt, string
from sgmllib import SGMLParser

class SwVersionLister(SGMLParser):
    inside_div_element = 0
    softwareVersion = 0
    swversion = None
    def reset(self):                              
        SGMLParser.reset(self)
        self.versions = []

    def start_div(self, attrs):    	
    	self.inside_div_element = 1
        for k,v in attrs:
        	if k == 'itemprop':
        		if v == 'softwareVersion':
        			self.softwareVersion = 1

    def handle_data(self, data):
    	if self.softwareVersion == 1:
    		self.swversion = string.strip(data)
    		self.softwareVersion = 0
    def end_div(self):       	
        self.inside_div_element = 0

class MyOpener(urllib.FancyURLopener):
	version = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0"

def get_apk_version(package_name):
	''' Returns the version of the `package_name` in the play store '''
	urllib._urlopener = MyOpener()

	response = urllib.urlopen("https://play.google.com/store/apps/details?id=%s" % package_name)	
	
	data = response.read()
	parser = SwVersionLister()
	parser.feed(data)
	version = parser.swversion
	return version
