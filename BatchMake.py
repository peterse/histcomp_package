#BatchMake.txt
#Evan Peters 6/11/2015
#Python script to construct/edit batches of range files using an input .txt file

import json
import unittest
import sys
from optparse import OptionParser
import dctROOTv6 as dR

parser = OptionParser()
parser.add_option("-i", "--input",dest="input",help="Batch request file, .txt",type='string')
(options, args)=parser.parse_args()

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class ExeLines:
'''Functions for executing lines in input batch request file'''
	exe_dct = {"BATCHNAME": self.batchname, "APPEND", "REMOVE", "DELETE_BATCH", "DUMP_BATCH", "DUMP_ALL_BATCHES", "REMAKE"}
#Have a dct of corresponding methods that automatically constructs the output settings
	def batchname(self):
		self.out = 


#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 



def file_check(self, *args):
#Each arg is a tuple of (file_name, ".suffix")
	for arg in args:
		if str(arg[1]) not in str(arg[0]):
			print "Error at %s: Improper filetype: '%s' not provided" % (func, str(arg[1]))
			sys.exit()

def valid_command(parse_list):

	if len(parse_list) > 2:
		return False
	if parse_list[0].upper() not in ExeLines.exe_dct:
		return False
	return True

def read_in_dct(filename):
#Read in the file and send each line to a dictionary
	dct = {}


	#Only accepts .txt files
	file_check((options.input, ".txt"))
	file_handle = open(options.input,"r")
	file_handle.seek(0)
	for raw_line in file_handle.readlines():
		line  = raw_line.split()
		#Skip comment lines and blank lines
		try:
			if line[0][0] == '#':
				continue
		except:
			continue
		if not valid_command(line):
			print "Error at read in: '%s' is not a valid command" % raw_line
			sys.exit()
		dct[line[0].upper] = line[1]
	return dct

def execute_dct(dct):
	for key, command in dct.iteritems():
		if key == "BATCHNAME""
			continue
"APPEND", "REMOVE", "DELETE_BATCH", "DUMP_BATCH", "DUMP_ALL_BATCHES", "REMAKE"
		
read_in_dct(options.input)




