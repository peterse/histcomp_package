#E Peters Gabe Nowak 3/11/2015
#DQMHistComp: Full analysis package for rescaling histograms, creating profiles, and comparing 

import dctROOTv7 as dR
from optparse import OptionParser
from BatchMake import TxtParser as BM_TxtParser
import json
import os, sys
import shutil
#load/set ROOT options if necessary
import ROOT as R
from ROOT import gDirectory
R.gROOT.Reset()

#To Do:
#Set up environment for batch lists:
batch_path = "~/batch_meta"
rfile_path = "~/rfile_meta"
rootfile_path = "~/histcomp_staging"

#Comparator() Notes for review
#histograms for entire branches constructed using 0th leaf
#Sending histograms to directory named with date/time
#Can different range files be constructed for the same root file? What sort of features vary in range file construction?
#	-When do we overwrite vs create new?
#Providing a 'Channel' branch name for profiling in Comparator


#Reads in the following options:
#--input: SetOptions.txt formatted file

#------------------------------------------------------------------------------------
parser = OptionParser()
parser.add_option("-i", "--input",dest="input",help="Ordered input files, .root only",type='string')
(options, args) = parser.parse_args()

#------------------------------------------------------------------------------------

class Options:
	"""Class of parsed options, to be passed to rHist Comparator"""
	exe_lst = ["INPUT", "RANGEFILE", "USE_INPUT_RANGE", "PROFILE", "PROFILE_N_CHANNELS", "WEIGHT_BRANCH", "PUBLISH", "OUT_DIR"]

	def __init__(self, input_dct, batch_path, rfile_path, rootfile_path, quiet=False):
		self.in_dct = input_dct
		self.exe_dct = {"INPUT": self.input_root, "RANGEFILE": self.set_rfile, "USE_INPUT_RANGE": self.set_rfile, "PROFILE": self.set_profile, "PROFILE_N_CHANNELS": self.set_profile, "WEIGHT_BRANCH": self.set_weight, "PUBLISH": self.set_publish, "OUT_DIR": self.set_output}

		# # # # # # # # DIRECTORY AND FILE PATHS # # # # # # # # # # 
		self.batch_path = batch_path
		self.batches_dir = "batches"
		self.metameta_fname = "batchlog.json"
		self.rfile_meta_fname = "rfile_contents.json"
		self.rfile_path = rfile_path
		self.rfile_directory = "range_files"
		self.rootfile_path = rootfile_path
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
		self.all_paths = [self.rfile_path, self.batch_path, "%s/%s" % (self.batch_path, self.batches_dir), "%s/%s" % (self.rfile_path, self.rfile_directory), self.rootfile_path]
		self.all_files_path = {self.metameta_fname: self.batch_path, self.rfile_meta_fname: self.rfile_path}

		self.make_path_lst = []
		self.queue_construct = []

		#Input objects (and defaults)
		self.input_files = []
		self.rfiles = []
		self.profile = False
		self.profile_n_channels = 0
		self.use_input_range = True
		self.weight = False
		self.weight_branch = None
		self.publish = False
		self.out_path = os.getcwd()
		self.out_dir = ""

		#Status, debug
		self.quiet = quiet
		self.debug = True
		self.problems = []
		self.status_index = 0
		self.status_good = self.check_path_status
		
		self.ping_status()
		self.execute()
		self.printOptions()

		#Privat attributes
		self.opt_dct = {}

	def ping_status(self):
		if not self.status_good:
			print "Errors executing DQMHistComp.py:\n%s" % "\n".join(self.problems)
			sys.exit()			

	def execute(self):
	#Execute the corresponding function in exe_dct
		for kw in self.in_dct:
			#Entries of the read_in dct are lists, with entries for every cmd call
			#Only execute over given entries; I have set defaults for some cmds eg REMAKE
			for i, lst in enumerate(self.in_dct[kw]):
				self.exe_dct[kw](kw.lower(), i)
		self.__syntax_check()
		self.ping_status()
		self.__cleanup()

	def printOptions(self):
	#Print the verbose batches and input files to shell
		if self.quiet:
			return
		print "\n INPUT ROOT FILES:"
		for fle in self.input_files:
			print "  ", str(fle)
		input_range_str = "WILL" if self.use_input_range else "WILL NOT"
		print "  These files %s contribute to the histogram ranges" % input_range_str
		print "\n HISTOGRAM RANGING FILES:"
		for fle in self.rfiles:
			print "  ", str(fle)
		if self.profile:
			print "\n PROFILE OPTIONS:"
			print "  Profiling branches with over %i channels" % self.profile_n_channels

		print "\nOUTPUT LOCATIONS:"
		print "Output path: %s/%s" % (self.out_path, self.out_dir)
	
	def check_path_status(self):
	#Make sure the environment is set up properly
		#First check at init: check builtin paths and files
		if self.status_index == 0:
			all_paths_good = all([self.check_path(path) for path in self.all_paths])
			all_files_checked = []
			for filename, path in self.all_files_path.iteritems():
				all_files_checked.append(self.check_exists(path, filename))
			all_files_good = all(all_files_checked)
			self.status_index += 1
			return all([all_files_good, all_paths_good])
		#Second check after exe: check paths provided by user
		if self.status_index == 1:
			return		
		
	def check_path(self, path):
		try:
			with dR.cd(path):
				pass
		except:
			print "caught err", sys.exc_info()[1]
			self.make_path_lst.append(path)
			self.problems.append("Directory %s does not exist" % path)
			return False
		else:
			return True

	def input_root(self, null, index):
	#Get all root inputs, or root files in input directories
		target_lst = self.input_files
		file_dir = self.in_dct["INPUT"][index]

		#.root file option
		if ".root" in file_dir:
			with dR.cd(self.rootfile_path):
				pwd = os.getcwd()
				if file_dir not in os.listdir(pwd):
					self.problems.append("File %s/%s does not exist" % (self.rootfile_path, file_dir))
					self.status_good = False
				else:
					target_lst.append(file_dir)
		#Directory option: Get all root files in provided directory
		else:
			try:
				with dR.cd("%s" % file_dir):
					pass
			except:
				print "DQMHistComp Error: Could not access directory %s; confirm directory name and try again" % file_dir
				self.status_good = False
			else:
				with dR.cd("%s" % file_dir):
					pwd = os.getcwd()
					target_lst += [i for i in os.listdir(pwd) if ".root" in i]
		return

	def set_rfile(self, mode, index, file_batch = None):
	#Get all range file inputs from either .root file or a given batch

		if mode == "rangefile":
			target_lst = self.rfiles
			#For using provided Rangefiles
			if file_batch == None:
				file_batch = self.in_dct["RANGEFILE"][index]

			#Single .root file option 
			if ".root" in file_batch:
				#Check batches repository for previous ranges
				with dR.cd(self.batch_path):
					with open(self.metameta_fname) as file_handle:
						batch_lst = json.load(file_handle)
					if file_batch in batch_lst:
						target_lst.append(file_batch)
						return
				#Otherwise, check the rootfile path and prompt for construction
				with dR.cd(self.rootfile_path):
					pwd = os.getcwd()
					if file_batch in os.listdir(pwd):
						self.queue_construct.append(file_batch)
						target_lst.append(file_batch)
						return
					else:
						err_str = "DQMHistCompError: RANGEFILE %s/%s does not exist and could not be found in batch repository. Check that this file exists and place it in the rootfile path before continuing" 
						self.problems.append(err_str % (self.rootfile_path, file_batch))
						self.status_good = False
						return
		
			#Batch option: Unpackage batch info from batch_meta
			else:
				batchfile = file_batch + ".json"
				with dR.cd(self.batch_path):
					with open(self.metameta_fname) as file_handle:
						batch_lst = json.load(file_handle)
					#Check meta for existance of batch
					if file_batch not in batch_lst:
						err_str = "DQMHistComp Error: Batch %s could not be found. Create this batch with BatchMake.py, or choose another batch before continuing" % file_batch
						self.problems.append(err_str)
						self.status_good = False
						return
				#Load the .root file contents of the batch to the master list
				with dR.cd("%s/%s" % (self.batch_path, self.batches_dir)):
					print batchfile
					with open(batchfile) as file_handle:
						batch_contents = json.load(file_handle)
				target_lst += [i for i in batch_contents]
				return
		#Choose to use the input files in the ranging process
		elif mode == "use_input_range":
			if self.in_dct["USE_INPUT_RANGE"][0].lower() != "true":
				self.use_input_range = False
				return
			#Just run the above methods over all the input files
			else:
				self.use_input_range = True
				for i, file_dir in enumerate(self.in_dct["INPUT"]):
					self.set_rfile("rangefile", i, file_batch=self.in_dct["INPUT"][i])
				return

	def set_profile(self, mode, null):
		if mode == "profile":
			bool_str = self.in_dct["PROFILE"][0]
			if bool_str.lower() == "true":
				self.profile = True
			elif bool_str.lower() == "false":
				self.profile = False
			else:
				err_str = "DQMHistCompError: PROFILE takes 'True' or 'False' - provide a boolean before continuing"
				self.problems.append(err_str)
				self.status_good = False
				return
		elif mode == "profile_n_channels":
			try:
				n_channels = int(self.in_dct["PROFILE_N_CHANNELS"][0])
			except:
				err_str = "DQMHistComp Error: PROFILE_N_CHANNELS was not provided an integer"
				self.problems.append(err_str)
				self.status_good = False
				return
			else:
				self.profile_n_channels = n_channels

	def set_weight(self, null, null2):
		print "Weights not currently supported - try again soon!"
		#Pass error handling (nonexistent branch etc) to Comparator()
		return

	def set_publish(self, null, null2):
		return

	def set_output(self, null, null2):
		out_path = self.in_dct["OUT_DIR"][0]
		(path, __, directory) = out_path.rpartition("/")
		#If the user provided path/directory
		if not path:
			#If the user provided directory, assume path is pwd
			path = os.getcwd()
		try:
			with dR.cd(path):
				pass
		except:
			err_str = "DQMHistComp Error: OUT_DIR path %s does not exist. Create this path or choose another before continuing"
			self.problems.append(err_str % path)
			self.status_good = False	
		else:		
			with dR.cd(path):
				pwd = os.getcwd()
				print pwd
				if directory in os.listdir(pwd):
					err_str = "DQMHistComp Error: OUT_DIR directory %s already exists at %s. Choose a different directory name before continuing"
					self.problems.append(err_str % (directory, path))
					self.status_good = False				
					return
				else:
					os.mkdir(directory)
					self.out_path = path
					self.out_dir = directory
					return

	def __syntax_check(self):
	#Check for weird .txt inputs after constructing input objects
		#not use_input_range, but the input file IS in batch...
		use_notuse = []
		for use in self.input_files:
			#Check if use_input_range is false AND the root files are in rfiles
			if use in self.rfiles and (not self.use_input_range):
				use_notuse.append(use)
		if any(use_notuse):
			self.problems.append("DQMHistComp Error: You have requested to both use and not use the following rootfile ranges: %s; check your input for consistency and run again" % ", ".join(use_notuse))
			self.status_good = False

		#profile w/o profile_n_channels, vice versa
		if self.profile and (not self.profile_n_channels):
			print "ping!"
			self.problems.append("DQMHistComp Error: 'PROFILE' requires 'PROFILE_N_CHANNELS' to set the threshold number of branch channels for profiling a branch")
			self.status_good = False

		return
		

	def __construct_ranges(self):
	#Construct ranges for newly submitted .root files
		constructed_lst = []
		#Check which range files are already at rfile_path
		for rootfile in self.queue_construct:
			with dR.cd(self.rootfile_path):
				FT = dR.fileTools(rootfile, self.rfile_path, debug=self.debug)
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
	def __cleanup(self):
	#Some general, nonessential housekeeping

		#Remove redundant .root files in the constructed lists
		self.rfiles = list(set(self.rfiles))
		self.input_files = list(set(self.input_files))
	
	def __enter__(self):
	#Configure 'with' environment to reference "MY_OPTIONS" attrs
		pass
	def __exit__(self):
		self.__construct_optdct()
	def __construct_optdct(self):
		pass
	#Creates a dictionary of the options you chose 


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

#rHistAnalysis() methods and attributes

#Parameters
#db_suffix - this determines which directory of .db files will contribute to histogram best ranges

#Attributes
#master_file_dct = dictionary of fileTools instances indexed by fileset
#master_tree_dct = dictionary of {tree_name:br_name:leaf:... } with None at bottom, indexed by fileset
#master_exp_dct = dictionary of Rfile structure dictionaries, indexed by fileset
#master_N_channels_dct= dictionary parallel to master_tree_dct, with N_channels at bottom
#master_ranges = dictionary of branches from ALL rfiles parsed, with most extreme ranges from each
#master_range_group = list of all rfiles used in creating the master ranges

class Comparator:

	def __init__(self, opt_inst, quiet=False, debug=False):	
	#References paths and directories from opt_inst of class Options

		self.opt_inst = opt_inst
		#Public Attributes
		#file_organizer
		self.master_tree_dct = {}
		self.master_exp_dct = {}
		self.master_file_dct = {}
		self.master_N_channels_dct = {}
		#master_range_finder
		self.master_ranges = {}
		
		#Private 
		self.global_quiet = quiet
		self.master_ranges_found = False		
		#file_organizer

		#Debug variables
		self.debug = debug
		self.debug_length = 100000
		self.debug_br_num = 20
		
		#Parser Parameters	
		self.hout = None
		self.write_status_good = True
		
		#Data management
		self.file_list = []
		#Range files to be read from; pass paths from input class
		self.rfiles = []
		self.rfile_path = self.opt_inst.rfile_path
		self.rfile_directory = self.opt_inst.rfile_directory

		#Data Description variables
		self.TEST = False
		self.FAST = True #Controls some functions that work faster for well-behaved root files
		
		#Read in files
		self.read_in()
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	
	def execute(self):
	#Executes methods consistent with user inputs
	
		#Prevent canvases from popping up		
		R.gROOT.SetBatch(True)  
		
		#Initialize ranges and filesets
		for i, fname in enumerate(self.file_list):
			self.file_organizer(i)
			self.range_organizer(i)
		#Construct master ranges
		self.master_range_finder()
		#Create histograms for each fileset
		with dR.cd(self.OUT_DIR):
			for i, fname in enumerate(self.file_list):
				self.hist_manager(i)

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def safe_print(self, string, quiet):
		if not quiet and not self.global_quiet:
			print string

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def read_in(self):
	#imports attrs from the options class you pass it
			
		self.file_list = self.opt_inst.input_files
		#Initialize rfiles with '.db' sister db's of .root files
		self.rfiles = [dR.fileTools.get_rfile_name(rootname) for rootname in self.opt_inst.rfiles]
		self.NFILES = len(self.opt_inst.input_files)
		self.OUT_DIR = "%s/%s" % (self.opt_inst.out_path, self.opt_inst.out_dir)
		self.PROFILE = self.opt_inst.profile
		#Weights not supported right now
		self.WEIGHTS = self.opt_inst.WEIGHT
		if self.PROFILE:
			self.NUM_CHANNELS = self.opt_inst.profile_n_channels
		

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	#! ! ! ! ! ! ! ! ! ! BROKEN	! ! ! ! ! ! ! ! ! ! 
	def __file_checker(self, index, quiet=False):
	#Browses the input root file to check for proper formatting
		exp_dct = self.master_file_dct[index].exp_dct

		main = self.handle_list[index]
		#If weights are enabled, the current input tree needs a weight branch
		if self.options.wgt[index]:
			for key in main.GetListOfKeys():
				folder = main.Get(key.GetName())
			for key in folder.GetListOfKeys():
				tree = folder.Get(key.GetName())
				#Weight branches are either named 'wgt' or weight
				if str(type(tree)) == "<class 'ROOT.TTree'>":
					for name in ["wgt", "weight"]:
						if name not in tree.GetListOfBranches():
							self.safe_print("Error at file_organizer(%s): TTree %s Does not have a wgt branch" % (index, tree.GetName()), quiet)	
							sys.exit()
							return
							
		#All tests passed, continue on
		return main

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def __Hname_creator(self, index):
	#Given a file set, creates an appropriate .root filename with output histograms
		
		file_name = str(self.file_list[index])
		file_name = file_name.replace(".root", "_")	
		file_name += "histograms"
		#if self.options.wgt[index]:
		#	file_name += "_weighted"
		file_name += ".root"
		return file_name

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def file_organizer(self, index, quiet=False):
		#Initializing relevant dictionaries and FileTools objects
		current_FT = dR.fileTools(self.file_list[index], self.rfile_path, fast_channel_count=self.FAST, debug=self.debug)
		self.master_file_dct[index] = current_FT
		self.master_tree_dct[index] = current_FT.tree_dct
		self.master_exp_dct[index] = current_FT.exp_dct
		self.master_N_channels_dct[index] = current_FT.N_channels_dct
		#Check the FT exp_dct for weights, etc.
		#self.__file_checker(index)

		#Initializing master ranges - first check if we need to construct a rangefile
		#Ignore where FT thinks the rfiles are - this code previously populated self.rfiles with sister db's

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def range_organizer(self, index, quiet=False):
	#Read and write ranges to the fileTools inst according to user setup
		
		current_DT = dR.dctTools(self.master_tree_dct[index])
		sister_db = self.master_file_dct[index].sister_db
		#Read in range files to populate master_tree_dct
		with dR.cd("%s/%s" % (self.rfile_path, self.rfile_directory)):
			self.master_tree_dct[index] = current_DT.range_reader(sister_db, append=True)
		self.safe_print("file_organizer(%i) reading range file %s" % (index, sister_db), quiet )

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def master_range_finder(self, quiet=False):
	#Find all db files in the rfiles directory and compile ranges into best_ranges
		self.safe_print("master_range_finder() combining ranges", quiet)
		#Only needs run once - compiles best ranges from the passed rfiles list
		if self.master_ranges_found:
			return
		DT_list = []
		#Get the rfiles from the repository
		with dR.cd("%s/%s" % (self.rfile_path, self.rfile_directory)):
			#Set up dctTools for ranges in provided rfiles
			for db in self.rfiles:
				DT_temp = dR.dctTools({})
				DT_temp.range_reader(str(db), append=False)
				DT_list.append(DT_temp)

		master_DT = dR.dctTools({})
		self.master_ranges = master_DT.get_best_ranges(*DT_list)
		self.master_ranges_found = True

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def hist_manager(self, index, quiet=False):
	#Create a batch of histograms for the fileset at index
		#Handling output file
		hout_name = self.__Hname_creator(index)
		if self.debug:
			self.hout = R.TFile("test%s.root" % index,"RECREATE")
		else:
			self.hout = R.TFile(hout_name, "RECREATE")
		self.safe_print("Writing to %s" % self.hout, quiet)

		#Give an update of the master ranges being used
		self.safe_print("Runnning hist_manager(%s)" % index, quiet)
		self.safe_print("  Using ranges combined from the following files:", quiet)
		for db in self.rfiles:		
			self.safe_print("    %s" % db, quiet)

		#Write out histograms given in the file
		for name, hist_handle in self.master_file_dct[index].hist_dct:
			hist_handle.Write()
		for i_tree, tree_name in enumerate(self.master_tree_dct[index]):
			tree = self.master_file_dct[index].tree_handle_dct[tree_name]
			for br_num, br_name in enumerate(self.master_tree_dct[index][tree_name]):
				if self.debug and br_num > self.debug_br_num:
					print "Truncating after %i branches" % self.debug_br_num
					break
				N_subleafs = self.master_N_channels_dct[index][tree_name][br_name]
				#For Leafs with no subleafs
				if N_subleafs == 1:
					string = "(100, %s, %s)" % \
					(self.master_ranges[br_name][0][0], self.master_ranges[br_name][0][1])
					#Setting weights
					# # # # # # # #broken # # # # # # # #
					if self.WEIGHTS:	
						drawstring = "%s >> h1%s wgt * (%s)" % (br_name, string, br_name)
						tree.Draw(drawstring)
					# # # # # # # # # # # # # # # #
					else:
						drawstring = "%s >> h1%s" % (br_name, string)
						tree.Draw(drawstring)
					htemp = R.gPad.GetPrimitive("h1")

					#Currently naming based on which TTree is being checked
					htemp.SetName("TTree%i:%s" % (i_tree+1, br_name))
					htemp.SetTitle("TTree%i:%s" % (i_tree+1, br_name))
					#Checking for empty histrogram
					integral = htemp.Integral()
					if integral == 0:
						self.safe_print("histogram_manager(%s) Warning: %s is empty, may need regeneration" % (index, br_name), quiet)
						continue
					else:
						if i_tree == 0:
							self.hout.mkdir(br_name)
						self.hout.cd(br_name)
						htemp.Write()
						self.safe_print("File %s:TTree %s: TBranch %s was written" % \
						(index, i_tree, br_name), quiet)
									
				#Profile for specific Leafs with self.NUM_CHANNELS Channels
				elif N_subleafs > 1:
					if i_tree == 0:
						self.hout.mkdir(br_name)
					self.hout.cd(br_name)
					if N_subleafs > self.NUM_CHANNELS and self.PROFILE:
						#Relies on a branch named channel
						if "channel" in tree.GetListOfBranches():
							string = "%s:channel>> h1(%s, 0, %s)" % (br_name, N_subleafs, N_subleafs)
							tree.Draw(string,"","profs")
							profile = R.gPad.GetPrimitive("h1")
							profile.SetName("TTree%i:%s Profile" % (i_tree,br_name))
							profile.SetTitle("%s Profile" % br_name)
							profile.Write()
						else:
							print "Warning at histogram_manager(%s) TTree %s TBranch %s: 'channel' branch not provided - profile will not be drawn" % (index, i_tree, br_name)
					
					#Construct subleaf histograms (over all trees, etc)
					for i in xrange(N_subleafs):
						n_s = "TTree%i:%s[%i]" % (i_tree, br_name, i)
						string = "(100, %s, %s)" % (self.master_ranges[br_name][i][0], self.master_ranges[br_name][i][1])
						# # # # # # # #broken # # # # # # # #
						if self.WEIGHTS:
							string = "%s[%i] >> h1%s wgt * (%s[%i])" % (br_name, i, string, br_name, i)
							tree.Draw(string)
						else:
							drawstring = "%s[%i] >> h1%s" % (br_name, i, string)
							tree.Draw(drawstring)
							htemp = R.gPad.GetPrimitive("h1")
						integral = htemp.Integral()
						if integral == 0:
							self.safe_print("histogram_manager(%s) Warning: %s[%i] is empty, may need regeneration" % (index, br_name, i), quiet)
							continue
						else:
							htemp.SetName(n_s)
							htemp.SetTitle(n_s)
							integral = htemp.Integral()
							htemp.Write()
							self.safe_print("File %s:TTree %s: Subleaf %s[%i] was written" % \
							(index, i_tree, br_name, i), quiet)	
						#DEBUG
						if self.debug and i > 20:
							break	
		self.hout.Close()	
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 






parse_class = BM_TxtParser(Options)
input_dct = parse_class.read_in_dct(options.input)
dR.dctTools(input_dct).printer()
#------------------------------------------------------------------------------------
#Instatiate OptionsClass
try:
	shutil.rmtree("test_output")
except:
	pass
my_options = Options(input_dct, batch_path, rfile_path, rootfile_path)
#Comparator(my_options, debug=True).execute()

	

