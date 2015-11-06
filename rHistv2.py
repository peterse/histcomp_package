#v2: Accepts inputs passed via DQMHistComp.py
import dctROOTv6 as dR
import os, sys
import glob
from optparse import OptionParser
#load/set ROOT options if necessary
import ROOT as R
from ROOT import gDirectory
R.gROOT.Reset()

#Notes for review
#histograms for entire branches constructed using 0th leaf
#Sending histograms to directory named with date/time


#Instructions:
#Must have XRFX_range_files (eg) in same working directory
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

	def __init__(self, script=[], OUT_DIR=None, INPUT=None, db_suffix="XRFX", quiet=False, debug=False):	
	#db_suffix tells which set of range files will be used to set up master ranges

		#Public Attributes
		#file_organizer
		self.master_tree_dct = {}
		self.master_exp_dct = {}
		self.master_file_dct = {}
		self.master_N_channels_dct = {}
		#master_range_finder
		self.master_ranges = {}
		self.master_range_group = []


		#Private 
		self.auto_ranging = False
		self.global_quiet = quiet
		self.script = script
		self.master_ranges_found = False		
		#file_organizer

		#Debug variables
		self.debug = debug
		self.debug_length = 100000
		self.debug_br_num = 20
		
		#Parser Parameters		
		self.handle_list = []
		self.hout = None
		
		#Data management
		self.handle_list = []
		self.file_list = []

		
		#Range files to be read from
		self.rfiles = []

		#Data Description variables
		self.NUM_CHANNELS = 5000 #The threshold for constructing profile histograms 
		self.TEST = False
		if not self.debug:
			self.NFILES = int(raw_input("Enter the number of file sets you gave as input:\n"))
		else:
			self.NFILES = 4
		self.RANGE_CONSTRUCT = [False]*self.NFILES #Calls for SQL range file construction at the given fileset index
		self.FAST = True #Controls some functions that work faster for well-behaved root files
		
		#Read in files
		self.read_in()
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	
	def execute(self):
	#Executes methods consistent with user inputs
	
		#Prevent canvases from popping up		
		R.gROOT.SetBatch(True)  
		
		#Initialize ranges and filesets
		for i, data in enumerate(self.handle_list):
			self.file_organizer(i)
			self.range_organizer(i)
		#Construct master ranges
		self.master_range_finder(0)
		#Create histograms for each fileset
		with dR.cd(self.OUT_DIR):
			for i, data in enumerate(self.handle_list):
				self.hist_manager(i)

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def safe_print(self, string, quiet):
		if not quiet and not self.global_quiet:
			print string

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def read_in(self,  ):
	#Creates option parser, imports ROOT objects for queries
	
		parser = OptionParser()
		#nargs turns this option into a tuple of input files
		parser.add_option("--input",dest="input",help="Ordered input files, .root only",type='string', nargs=self.NFILES)
		parser.add_option("--range",dest = "rfiles", help = "Ordered range file inputs, .db only", type='string', nargs=self.NFILES)
		parser.add_option("--profile",dest = "profile", help = "Produce profile histograms for branches with N_subleafs > NUM_CHANNELS (Default %i)" % self.NUM_CHANNELS, default = self.NUM_CHANNELS)
		parser.add_option("--weight",dest = "wgt",help = "Use weights when drawing from the corresponding Rfile. Entry must be a list of bools of equal length to list of files. The TTree must have a weight branch.", default = [False]*self.NFILES, nargs=self.NFILES)
		parser.add_option("--outdir", dest = "outdir", help = "Output directory file", type ='string')

		#Assign options and args variables
		(self.options,self.args)=parser.parse_args()
		#Open input files into self.handle_list
		if self.NFILES == 1:
			self.file_list = [self.options.input]
			self.handle_list = [R.TFile.Open(self.options.input,'r')]
		else:
			for file_name in self.options.input:
				self.file_list.append(str(file_name))
				self.handle_list.append(R.TFile.Open(file_name,'r'))

		#Check for existence of given rfiles in the rfile input list
		if not self.options.rfiles:
			self.auto_ranging = True
			self.rfiles = [None] * self.NFILES
		else:
			for i, rfile in enumerate(self.options.rfiles):
				if rfile.lower() == "none":
					self.rfiles.append(None)
					continue
				#Setting up rfile list with inputs or None -> if None, FT[i] will grab sister_db 
				if rfile and not os.path.isfile(rfile):
					print "Warning at %s.readin(): The range file %s does not exist. fileTools() will automatically construct and use its sister_db" % (self.__class__.__name__, rfile)
					self.rfiles.append(None)
				else:
					self.rfiles.append(rfile)
		#Check and create the output directory OUT_DIR
		if self.options.outdir in os.listdir(os.getcwd()):
			print "Error at %s.readin(): The output directory already exists. Remove the directory or choose a different output name, then try again"
			sys.exit()
		self.OUT_DIR = self.options.outdir
		os.mkdir(self.OUT_DIR)
		#Set up NUM_CHANNELS for profile histograms
		self.NUM_CHANNELS = int(self.options.profile)


	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	def __file_checker(self, index, quiet=False):
	#Browses the input root file to check for proper formatting
		exp_dct = self.master_file_dct[index].exp_dct
		#! ! ! ! ! ! ! ! ! !
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
							self.safe_print("Error at file_organizer(%s): TTree %s Does not have a wgt branch" % \
							(index, tree.GetName()), quiet)	
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
		if self.options.wgt[index]:
			file_name += "_weighted"
		if self.rfiles[index]:
			suffix = self.master_file_dct[index].perm_db_suffix 
			#append rfile name if it wasn't an automated rfile
			if suffix not in self.rfiles[index]:
				rfile_name = self.rfiles[index].replace(".txt", "")
				file_name += "_%s" % rfile_name
			elif suffix in self.rfiles[index]:
				file_name += "_%s" % suffix
		file_name += ".root"
		return file_name

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def file_organizer(self, index, quiet=False):
		#Initializing relevant dictionaries and FileTools objects
		current_FT = dR.fileTools(self.file_list[index], fast_channel_count=self.FAST, debug=self.debug)
		self.master_file_dct[index] = current_FT
		self.master_tree_dct[index] = current_FT.tree_dct
		self.master_exp_dct[index] = current_FT.exp_dct
		self.master_N_channels_dct[index] = current_FT.N_channels_dct
		#Check the FT exp_dct for weights, etc.
		#self.__file_checker(index)

		#Initializing master ranges - first check if we need to construct a rangefile
		rfile_directory = current_FT.rfile_directory
		if not os.path.isdir(rfile_directory):
			print "Directory %s does not exist - constructing for future reference" % rfile_directory
			self.RANGE_CONSTRUCT[index] = True
		else:
			with dR.cd("%s" % rfile_directory):
				pwd = os.getcwd()
				#Check that the sister_db is missing and 'None' rfile was provided for this index
				if (current_FT.sister_db not in os.listdir(pwd)) and (not self.rfiles[index]):
					self.RANGE_CONSTRUCT[index] = True
				#If the sister_db is present, use it
				elif (current_FT.sister_db in os.listdir(pwd)) and (not self.rfiles[index]):
					self.rfiles[index] = current_FT.sister_db


	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def range_organizer(self, index, quiet=False):
	#Read and write ranges according to user setup
		
		current_DT = dR.dctTools(self.master_tree_dct[index])
		rfile_directory = self.master_file_dct[index].rfile_directory
		suffix = self.master_file_dct[index].perm_db_suffix
		#Construct ranges automatically in the sister range files directory
		if self.RANGE_CONSTRUCT[index]:
			db_out = self.master_file_dct[index].sister_db
			self.safe_print("file_organizer(%i) constructing range file %s" % (index, db_out), quiet)
			rfile_directory = self.master_file_dct[index].rfile_directory
			self.master_file_dct[index].construct_all_ranges()
			#Populating the current fileset's tree_dct with ranges from the correct db
			with dR.cd("%s" % rfile_directory):
				self.master_tree_dct[index] = current_DT.range_reader(db_out, append=True)
				self.rfiles[index] = db_out
		#If the rfile was autoconstructed, change to the proper directory
		else:
			if suffix in self.rfiles[index]:
				with dR.cd("%s" % rfile_directory):
					self.master_tree_dct[index] = current_DT.range_reader(self.rfiles[index], append=True)
			elif suffix not in self.rfiles[index]:
				self.master_tree_dct[index] = current_DT.range_reader(self.rfiles[index], append=True)
			self.safe_print("file_organizer(%i) reading range file %s" % (index, self.rfiles[index]), quiet )

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def master_range_finder(self, index, quiet=False):
	#Find all db files in the rfiles directory and compile ranges into best_ranges
		self.safe_print("master_range_finder(%i) combining ranges" % index, quiet)
		#Only needs run once - compiles best ranges assuming FT's share suffix (eg XRFX)
		if self.master_ranges_found:
			return
		DT_list = []
		rfile_directory = self.master_file_dct[index].rfile_directory
		suffix = self.master_file_dct[index].perm_db_suffix
		#Check if all of the range files were automated; if so, use the entire sister directory
		auto_ranged = filter(lambda db: suffix not in db, self.rfiles)
		if not any(auto_ranged):
			with dR.cd("%s" % rfile_directory):
				pwd = os.getcwd()
				self.master_range_group = ["%s/%s" % (rfile_directory, rfile) for rfile in os.listdir(pwd)]
				for db in os.listdir(pwd):
					DT_temp = dR.dctTools({})
					DT_temp.range_reader(str(db), append=False)
					DT_list.append(DT_temp)
		#If any range files were manually given, DO NOT draw best ranges from sister directory
		elif any(auto_ranged):
			for db in self.rfiles:
				DT_temp = dR.dctTools({})
				#If the rfile was auto-constructed, we must change directories
				if suffix in db:
					with dR.cd("%s" % rfile_directory):
						DT_temp.range_reader(str(db), append=False)
						DT_list.append(DT_temp)
						self.master_range_group.append("%s/%s" % (rfile_directory, db))
				else:
					DT_temp.range_reader(str(db), append=False)
					DT_list.append(DT_temp)
					self.master_range_group.append("%s" % db)
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
		for db in self.master_range_group:		
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
					if self.options.wgt[index]:	
						drawstring = "%s >> h1%s wgt * (%s)" % (br_name, string, br_name)
						tree.Draw(drawstring)
					elif not self.options.wgt[index]:
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
					if N_subleafs > self.NUM_CHANNELS and self.options.profile:
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
						if self.options.wgt[index]:
							string = "%s[%i] >> h1%s wgt * (%s[%i])" % (br_name, i, string, br_name, i)
							tree.Draw(string)
						elif not self.options.wgt[index]:
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

#------------------------------------------------------------------------------------
class OptionsClass:
	"""Set of methods and default options to be edited externally and used as inputs into Comparator"""
	def __init__(self):
		#Public attributes

		#Default Settings
		self.SUFFIX = None
		self.NFILES = 0
		self.PROFILE = False
		self.PROFILE_N_CHANNELS = 0
		self.WEIGHT = False
		self.RANGE_FIdLES = None

		#Privat attributes
		self.opt_dct = {}

	def setProfileTrue(self):
		self.PROFILE = True
	def setProfileFalse(self):
		self.PROFILE = False
	def setWeightTrue(self):
		self.WEIGHT = True
	def setWeightFalse(self):
		self.WEIGHT = False
	def setRangeFiles(self):
		return
	def __enter__(self):
	#Configure 'with' environment to reference "MY_OPTIONS" attrs
		pass
	def __exit__(self):
		self.__construct_optdct()
	def __construct_optdct(self):
		pass
	#Creates a dictionary of the options you chose 


#__dict__, __setitem__, __getitem__, etc?

#------------------------------------------------------------------------------------

		
#Debugging
script = []

#Testing path_manager
if 1 in script:
	pwd = os.getcwd()
	with dR.cd("%s/path_test" % pwd):
		print os.getcwd()
	print os.getcwd()
	
if 2 in script:
	Comparator().execute()






