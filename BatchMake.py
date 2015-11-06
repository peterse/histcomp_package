#BatchMake.txt
#Evan Peters 6/11/2015
#Python script to construct/edit batches of range files using an input .txt file

import json
import unittest
import sys, os
from optparse import OptionParser
import dctROOTv6 as dR

#To Do:
#Many append*, remove* statements
#Set up environment for batch lists:
batch_dir = "~/batch_meta"


parser = OptionParser()
parser.add_option("-i", "--input",dest="input",help="Batch request file, .txt",type='string')
(options, args)=parser.parse_args()

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class ExeLines:
'''Functions for executing lines in input batch request file'''
	exe_dct = {"BATCHNAME": self.batchname, "APPEND": self.append_remove("append"), "REMOVE": self.append_remove("remove"), "DELETE_BATCH": self.delete(), "DUMP_BATCH", "DUMP_ALL_BATCHES", "REMAKE": self.set_remake()}
#Have a dct of corresponding methods that automatically constructs the output settings
	def __init__(self, input_dct):
		self.in_dct = input_dct
		self.append_files = []
		self.remove_files = []
		self.batch = None
		self.remake = False

	def batchname(self):
		self.batch = self.in_dct["BATCHNAME"]
	
	def append_remove(self, mode):
	#Stages appends/removes from a APPEND or REMOVE command
		if mode == "append":
			my_list = self.append_files
			file_dir = self.in_dct["APPEND"]
		elif mode == "remove":
			my_list = self.remove_files
			file_dir = self.in_dct["REMOVE"]
		
		#.root file option
		if ".root" in file_dir:
			my_list.append(file_dir)
		#Directory option: Get all root files in provided directory
		else:
			try:
				with dR.cd("%s" % file_dir):
					pwd = os.getcwd()
					my_list += [i for i in os.listdir() if ".root" in i]
			except:
				print "Error: Could not access directory %s" % file_dir
				sys.exit()

	def set_remake(self):
		return
	#JSON methods
	def delete(self):
		return
	def delete_batch(self):
		return
	def dump_batch_all(self):
		return

	#Executing the proper functions
	def execute(self):
		#Execute the corresponding function in exe_dct
		for kw in self.input_dct:
			exe_dct[kw]
		self.__write_out()

	def __write_out():
		#Construct batch meta
		if self.remake:
			file_handle = open("%s/batches", "recreate")
			new_batch = json.dumps(self.append_files)
			file_handle.write(new_batch)
			file_handle.close()
			return
		else:
			file_handle = open("%s/batches", "rw")
			decoded = json.load(file_handle)
			for filename in decode
			#Append batch_content
		
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

#Eventually export this to TestPackage.py
def path_check():
#Check that batch_dir is set up, writable, etc.
	return

def file_check(*args):
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




