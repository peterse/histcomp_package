#BatchMake.txt
#Evan Peters 6/11/2015
#Python script to construct/edit batches of range files using an input .txt file

import json
import unittest
import sys, os
from optparse import OptionParser
import dctROOTv7 as dR

#To Do:
#Many append*, remove* statements
#Set up environment for batch lists:
batch_path = "~/batch_meta"
rfile_path = "~/rfile_meta"
rootfile_path = "~/histcomp_staging"
#Configure unittest - python2.6 is broken...

parser = OptionParser()
parser.add_option("-i", "--input",dest="input",help="Batch request file, .txt",type='string')
(options, args)=parser.parse_args()

#Class ExeLines
#Attributes
#exe_dct: dictionary of .txt commands and corresponding functions to run


#methods
#make_paths(): construct the directories and subdirectories for rfile meta and batch meta
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
class ExeLines:
	'''Functions for executing lines in input batch request file'''
	exe_lst = ["BATCHNAME", "APPEND", "REMOVE", "DELETE_BATCH", "DUMP_BATCH", "DUMP_ALL_BATCHES", "REMAKE"]
#Have a dct of corresponding methods that automatically constructs the output settings
	def __init__(self, input_dct, batch_path, rfile_path, rootfile_path):
		self.in_dct = input_dct
		#Confirm that environment is set up

		# # # # # # # # DIRECTORY AND FILE PATHS # # # # # # # # # # 
		self.batch_path = batch_path
		self.batches_dir = "batches"
		self.metameta_fname = "batchlog.json"
		self.rfile_meta_fname = "rfile_contents.json"
		self.rfile_path = rfile_path
		self.rfile_directory = "range_files"
		self.rootfile_path = rootfile_path
		self.all_paths = [self.rfile_path, self.batch_path, "%s/%s" % (self.batch_path, self.batches_dir), "%s/%s" % (self.rfile_path, self.rfile_directory), self.rootfile_path]
		self.all_files_path = {self.metameta_fname: self.batch_path, self.rfile_meta_fname: self.rfile_path}
		self.make_path_lst = []
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # 


		self.problems = []
		self.status_good = self.check_path_status()
		self.delete_done = False

		self.append_files = []
		self.remove_files = []
		self.delete_batches = []
		self.batch = None
		self.remake = False

		#range construction attrs
		self.construct_lst = []

		#Run the provided .txt script
		self.exe_dct = {"BATCHNAME": self.batchname, "APPEND": self.append_remove, "REMOVE": self.append_remove, "DELETE_BATCH": self.delete_batch, "DUMP_BATCH": self.dump_batch_all, "DUMP_ALL_BATCHES": self.dump_batch_all, "REMAKE": self.set_remake}
		if self.status_good:
			self.execute()
		else:
			print "Error executing BatchMake.py: %s" % ", ".join(self.problems)



	def check_path_status(self):
	#Make sure the environment is set up properly
		all_paths_good = all([self.check_path(path) for path in self.all_paths])
		all_files_checked = []
		for filename, path in self.all_files_path.iteritems():
			all_files_checked.append(self.check_exists(path, filename))
		all_files_good = all(all_files_checked)
		return all([all_files_good, all_paths_good])
		
	def check_path(self, path):
		try:
			with dR.cd(path):
				pass
		except:
			print "caught err", sys.exc_info()[1]
			self.make_path_lst.append(path)
			self.problems.append("Path %s does not exist" % path)
			return False
		else:
			return True

	def make_paths(self):
	#Construct the directory paths
		sorted_mkpth = sorted(self.make_path_lst, key = lambda s: len(s))
		print "Making directories at ", "; ".join(sorted_mkpth)
		for pathname in sorted_mkpth:
			#Construct the directory at path if it is not there
			(place, __, dr) = pathname.rpartition("/")
			with dR.cd(place):
				pwd = os.getcwd()
				if dr not in os.listdir(pwd):
					os.mkdir(dr)

	def check_exists(self, path, filename):
	#Check if meta at ~path/filename exists; if not, automatically construct it
		print filename
		try:
			with dR.cd(path):
				pwd = os.getcwd()
				if filename in os.listdir(pwd):
					return True
		#Fails if directory path doesn't exists
		except OSError:
			return False
		#If file wasn't present, automatically create the metafile
		else:
			print "Creating meta file at %s/%s" % (path, filename)
			with dR.cd(path):
				with open(filename, "w+") as file_handle:
					file_handle.write(json.dumps([]))
			return True

	def __syntax_check(self):
	#Check for weird inputs in the .txt file
		#Adding and Removing the same root file
		add_and_rem = []
		for app in self.append_files:
			if app in self.remove_files:
				add_and_rem.append(app)
		if any(add_and_rem):
			print "Error: You have requested to both append and remove the following files: %s; check your input for consistency and run again" % ", ".join(add_and_rem)
			sys.exit()
	
		#Deleting the batch file that is being created
		if self.batch in self.delete_batches:
			print "Warning: You have requested to delete the batch that you are creating; the commands you have entered will not execute and the batch will not be created"
			self.status_good = False

	def batchname(self, null, index):
		index = None
		self.batch = self.in_dct["BATCHNAME"][0]
		self.batch_file = "%s.json" % self.batch
	
	def append_remove(self, mode, index):
	#Stages appends/removes from a APPEND or REMOVE command
		
		if mode == "append":
			my_list = self.append_files
			file_dir = self.in_dct["APPEND"][index]
		elif mode == "remove":
			my_list = self.remove_files
			file_dir = self.in_dct["REMOVE"][index]
		
		#.root file option
		if ".root" in file_dir:
			my_list.append(file_dir)
		#Directory option: Get all root files in provided directory
		else:
			try:
				with dR.cd("%s" % file_dir):
					pass
			except:
				print "Error: Could not access directory %s; batch will not be created" % file_dir
				self.status_good = False
			else:
				with dR.cd("%s" % file_dir):
					pwd = os.getcwd()
					my_list += [i for i in os.listdir(pwd) if ".root" in i]

	def set_remake(self, null, null2):
		self.remake = self.in_dct["REMAKE"][0]

	#JSON methods
	def delete_batch(self, null, null2):
	#Remove batch .json file
		if self.delete_done:
			return
		self.delete_batches += self.in_dct["DELETE_BATCH"]
		with dR.cd("%s/%s" % (self.batch_path, self.batches_dir)):
			for rem_batch in self.delete_batches:
				try:
					os.remove(rem_batch+".json")
				except OSError:
					#The record was already deleted
					#print "caught err", sys.exc_info()[1]
					continue
		with dR.cd(self.batch_path):
			with open(self.metameta_fname, "r") as file_handle:
				batch_lst = json.load(file_handle)
			for rem_batch in self.delete_batches:
				try:
					batch_lst.remove(rem_batch)
				except:
					#The records were already deleted
					#print "caught err", sys.exc_info()[1]
					continue
			with open(self.metameta_fname, "w+") as file_handle:
				file_handle.write(json.dumps(batch_lst))
		self.delete_done = True	
		return

	def dump_batch_all(self, mode, null):
	#Print or write the contents of a single batch or a list of all batches
		if mode == "dump_all_batches":
			grabpath = self.batch_path
			grabfile = self.metameta_fname
		if mode == "dump_batch":
			grabpath = "%s/%s" % (self.batch_path, self.batches_dir)
			grabfile = self.batch_file

		with dR.cd(grabpath):
			with open(grabfile, "r") as file_handle:
				grab_lst = json.load(file_handle)

			grab_lst = json.dumps(grab_lst, sort_keys=True, indent=2)
			#If the user gave 'shell', the function prints;
			shell_true = (self.in_dct[mode.upper()][0] == "shell")
			if shell_true:
				print grab_lst
				return
		#If the user gave a file write to the given file in the pwd
		if not shell_true:
			with open(self.in_dct[mode.upper()][0], "w+") as write_out:
				write_out.write(grab_lst)
			return

	#Executing the proper functions
	def execute(self):
		#Execute the corresponding function in exe_dct
		for kw in self.in_dct:
			#Entries of the read_in dct are lists
			#Only execute over given entries; I have set defaults for some cmds eg REMAKE
			for i, lst in enumerate(self.in_dct[kw]):
				self.exe_dct[kw](kw.lower(), i)
		self.__syntax_check()
		if self.status_good:
			self.__write_out()
			self.__update_mm()
			self.__construct_ranges()

	def __write_out(self):
		#Construct batch meta

		with dR.cd("%s/%s" % (self.batch_path, self.batches_dir)):
			if self.remake:
				with open(self.batch_file, "w+") as file_handle:
					new_batch = json.dumps(self.append_files)
					file_handle.write(new_batch)
				return
			else:
				#if this batch exists, edit it
				try:
					file_handle = open(self.batch_file, "rw")
				#If the batch doesn't exist yet, create it using the remake option
				except IOError:
					self.remake = True
					self.__write_out()
					return
				else:
					#decoded is a loaded list of .root file names
					decoded = json.load(file_handle)
					file_handle.close()
					#Append APPEND files
					for app_file in self.append_files:
						if app_file not in decoded:
							decoded.append(app_file)
					#Remove REMOVE files
					for del_file in self.remove_files:
						try:
							decoded.remove(del_file)
						except:
							print "caught err", sys.exc_info()[1]
					updated_batch = json.dumps(decoded)
					with open(self.batch_file, "w+") as file_handle:
						file_handle.write(updated_batch)

	def __update_mm(self):
	#Update the batch metameta

		with dR.cd("%s" % self.batch_path):
			#The first time, metameta may not exist
			with open(self.metameta_fname, "r") as file_handle:
				mm_decoded = json.load(file_handle)

			#We must check for the presence of the current batch before we append
			if self.batch not in mm_decoded:
				mm_decoded.append(self.batch)
				with open(self.metameta_fname, "w+") as file_handle:
					file_handle.write(json.dumps(mm_decoded))

	def __construct_ranges(self):
	#Construct ranges for newly submitted .root files

		#Check which range files are already at rfile_path
		constructed_lst = []
		with dR.cd("%s/%s" % (self.rfile_path, self.rfile_directory)):
			pwd = os.getcwd()
			for rootfile in self.append_files:
				if rootfile in os.listdir(pwd):
					continue
				with dR.cd(self.rootfile_path):
					FT = dR.fileTools(rootfile, self.rfile_path, debug=True)
					FT.construct_all_ranges()
				constructed_lst.append(rootfile)
		#Append to the rangefile metadata
		if any(constructed_lst):
			with dR.cd(self.rfile_path):
				with open(self.rfile_meta_fname, "r") as file_handle:
					rfmeta = json.load(file_handle)
				for new in constructed_lst:
					rfmeta.append(new)
				with open(self.rfile_meta_fname, "w+") as file_handle:
					file_handle.write(json.dumps(rfmeta))
				
				

				
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

#Eventually export this to TestPackage.py
def path_check():
#Check that batch_dir is set up, writable, etc.
	return

def file_check(*args):
#Each arg is a tuple of (file_name, ".suffix")
	for arg in args:
		if str(arg[1]) not in str(arg[0]):
			print "Error: Improper filetype: '%s' not provided" % (str(arg[1]))
			sys.exit()

def valid_command(parse_list):

	if len(parse_list) > 2:
		return False
	if parse_list[0].upper() not in ExeLines.exe_lst:
		return False
	return True

def read_in_dct(filename):
#Read in the file and send each line to a dictionary
	dct = {}
	#Only accepts .txt files
	file_check((filename, ".txt"))
	file_handle = open(filename,"r")
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
		#Create lists when a command is used many times
		current_cmd = line[0].upper()
		if current_cmd not in dct:
			dct[current_cmd] = [line[1]]
		else: 
			dct[current_cmd].append(line[1])	
	
	return dct


import unittest
import shutil
class TestBatchMake(unittest.TestCase):
	"""Barrage of tests for output management in the user's environment"""
	def __init__(self):
		#Determine that all files are here before testing
		test_files = ["batch_test.txt", "BatchMake.py"]
		testfiles_present = [(testfile in os.listdir()) for testfile in test_files]
		if not all(testfiles_present):
			print "Missing some test files for BatchMake.py: Make sure that %s are present" % ", ".join(test_files)
			sys.exit()

		self.testdct = read_in_dct("batch_test.txt")

	def setUp(self):
		os.mkdir("test_batch_dir")
		
	def test_catch_bad_path(self):
		ExeLines(self.testdct, "bad_path")
		#self.assertFalse(ExeLines.status_good)
	def tearDown(self):
		return

#Scripting /testing area
debug_input = "batch_test.txt"
mydct = read_in_dct(debug_input)
dR.dctTools(mydct).printer()
ExeLines(mydct, batch_path, rfile_path, rootfile_path)

#unittest.main()


