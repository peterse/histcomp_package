#v6 Adding directory/output management, checkers, and some tests
#v5 Incorporated Gabe's text-to-sql function
#v4 Reworking __explorer into iterative function instead of recursive - Getting stack overflow...
#v3 fileTools now supports 'modes' according to input type
#v2 Chose faster of the methods in range_construct
#dctROOT: a library of methods for converting ROOT directories and their contents into Python dictionaries
#Evan Peters and Gabe Nowak 02102015

import sys, os
from optparse import OptionParser
import array
import time #for timing
#print sys.version
import copy

import collections
import sqlite3 as sq3
#load/set ROOT options if necessary
import ROOT as R
from ROOT import gDirectory
R.gROOT.Reset()


#NOTES FOR REVIEW


#Operating Notes
#construct_all_ranges automatically overwrites sister_db's if it finds them 
#range_reader runs in two modes - either creation or appending to an FT dict



#choose the correct datatype for declaring SQL columns (float vs. real)
#need to test __tree_find() on a multi-tree file
#__init_tree_dct sets bottom layer to None


#Error in pyROOT(?) - allows GetLeaf() method on custom branch and returns a null poiter


#dctTools() 'DT'

#Public Methods

#printer()
#prints the dictionary in a tier-format for easy reading in shell



# init_best_ranges(class<other dctTools instances>*) - combines other instantiations' dcts that have been populated with rfile leaf channels using range_reader

#range_reader(db_name.db, append=True)
#Two modes:
#	append: Populates DT.dct with ranges assuming DT initialized with dctTools(FT.tree_dct)
#	append=False: Initializes a dct parallel to FT.tree_dct, with ranges at the bottom


class dctTools():
	"""Tools associated with analysis of an input dictionary"""
	def __init__(self, dct):	
		
		self.__name__ = "dctTools(%s)" % str(id(dct))
		#Public attributes
		self.dct = dct 

		
		#range_reader params
		self.columns = ["br_name", "leaf_num", "min", "max"]
		self.ntiers = 0
		self.tier_list = []
		self.temp_list = [0]
		#init_best_ranges params
		self.DT_cls_list = []
		self.ranges_read = False
		self.best_ranges = False
		
		
	#IN PROGRESS
	def tiers(self, dct=None):
		if dct == None:
			dct = self.dct
		for key, val in dct.iteritems():
			if isinstance(val, dict):
				#print val
				self.ntiers += 1
				self.tiers(val)
				print self.ntiers
			else:
				break

		self.temp_list.append(self.ntiers)
		if self.ntiers == 0:
			print self.temp_list
			self.tier_list.append(max(self.temp_list))
		return self.tier_list
		
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def printer(self, obj=None, started=False, trim=True):
	#Prints a dictionary's contents, with some formatting for readability
		if not started:
			self.spacing = 0
			obj = self.dct

		if type(obj) in [dict, collections.OrderedDict]:
			self.spacing += 2
			for count, key in enumerate(obj):
				try:
					obj[key].iteritems()
				#Print out lines for bottom layer of dct
				except:
					if count > 20 and trim:
						print "".join([" "]*self.spacing),"...printout trimmed"
						break
					print "".join([" "]*self.spacing),"%s: %s" % (key, obj[key])

				else:
					print "".join([" "]*self.spacing), key
					self.printer(obj[key], started=True, trim=trim)
					self.spacing -= 2
		else:
			return
			
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 			
	def range_reader(self, db_name, append=True):
	#Unpack ranges from a .db into file_ranges dct
	#If append, it will be populated with ranges according to present branches
	#	-eg use this option with dctTools(FT.tree_dct).range_reader("db_name.db")
	#Otherwise, range_reader returns a fully populated dictionary
		self.__file_check(self.range_reader, (db_name, ".db"))
		con = sq3.connect("%s" % db_name)
		c = con.cursor()	
		#Get variable number of trees from sqlite master table
		file_ranges = {}
		for tree in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"):
			tree_name = str(tree[0])
			file_ranges[tree_name] = {}
		#We now have access to the individual tables	
			
		if append == False:
			#Need to initialize an output dictionary using unique branchnames
			for tree_name in file_ranges:
				for br_name in set(c.execute("SELECT br_name FROM %s" % tree_name)):
					file_ranges[tree_name][str(br_name[0])] = {}
			for tree_name in file_ranges:
				for row in c.execute("SELECT * FROM %s" % tree_name):
					#						br			leafnum			min		max
					file_ranges[tree_name][str(row[0])][int(row[1])] = [row[2], row[3]]
			
			#Running in append mode will construct the dictionary for the instantiation to use
			self.ranges_read = True
			self.dct = dict(file_ranges)
			return self.dct

		#Append will populate a dictionary of structure {tree_name:{br_name:{leafnum: ...} } }
		elif append == True:
			for tree_name in file_ranges:
				for row in c.execute("SELECT * FROM %s" % tree_name):
					self.dct[tree_name][str(row[0])][int(row[1])] = [row[2], row[3]]
			self.ranges_read = True
			return self.dct

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def get_best_ranges(self, *args):
	#Either creates a dictionary of most extreme ranges for trees in current dct
	#Or creates a dictionary of most extreme ranges for trees for all instances in *args
		if self.dct:
			None #Here, we're overwriting instances of dctTools() - generally not a problem
			#print "Warning at %s.init_best_ranges: overwriting instance dictionary" %(self.__class__.__name__)
		#Constructing ranges at the "tree level"
		if not any(args):
			self.temp = {}
			for i, (tree_name, branches) in enumerate(self.dct.iteritems()):
				#The easiest way to initialize the ranges dct copies branches of the first tree
				if i == 0:
					self.temp = copy.deepcopy(branches)
					for br_name, channels in branches.iteritems():
						for leaf_num in channels:
							#The bottom of temp is a running list of extrema
							try:
								self.temp[br_name][leaf_num] = [[], []]
							except TypeError:	
								print self.dct[tree_name]
								print self.temp
							self.temp[br_name][leaf_num][0].append(self.dct[tree_name][br_name][leaf_num][0])
							self.temp[br_name][leaf_num][1].append(self.dct[tree_name][br_name][leaf_num][1])
				#Once intialized, populating with remaining trees 
				elif i>0:
					for br_name, channels in branches.iteritems():
						#Here, we continue to initialize temp
						if br_name not in self.temp.keys():
							self.temp[br_name] ={}
							for leaf_num in channels:
								self.temp[br_name][leaf_num] = [[], []]
						for leaf_num in channels:
							#The bottom of temp is a running list of extrema
							self.temp[br_name][leaf_num][0].append(self.dct[tree_name][br_name][leaf_num][0])
							self.temp[br_name][leaf_num][1].append(self.dct[tree_name][br_name][leaf_num][1])					
					
			#Find best extrema from remaining trees
			for br_name in self.temp:
				for leaf_num, minmax in self.temp[br_name].iteritems():
					self.temp[br_name][leaf_num] = [min(minmax[0]), max(minmax[1])] 
			self.dct = self.temp
			self.best_ranges = True
			return self.temp

		#Constructing ranges at the "file level"
		elif any(args):
			#We will populate dct with the best ranges of each input instance
			for i, inst in enumerate(args):
				#Does not corrupt input instances
				inst = copy.deepcopy(inst)
				#dct will be wiped to be populated with best ranges of rfiles

				if inst.ranges_read == False:
					print "Warning at %s.init_best_ranges(%s): instance ranges have not been initialized. Continuing to next instance." % (self.__name__, inst.__name__)
					continue
				#Need access to best ranges of input obj
				if not inst.best_ranges:
					inst.get_best_ranges()
				obj_range_dct = inst.dct
				#Initialize the best ranges to dummy dct i at tree level
				self.dct[i] = inst.dct.copy()

			#Now find the very best ranges among the dictionary of best ranges
			self.get_best_ranges()
			return self.dct
		
					
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def __file_check(self, method, *args):
	#each arg is a tuple of (file_name, ".suffix")
		func = method.__name__
		for arg in args:
			if str(arg[1]) not in str(arg[0]):
				print "Error at %s: Improper filetype: '%s' not provided"\
				    % (func, str(arg[1]))
				sys.exit()		
		
#--------------------------------------------------------------------------------------------
#fileTools()

#Automatically checks sister_db upon instantiation; reconstructs if discrepancies found


#Parameters
# fast_channel_count - If true, assumes N_channels_dct entries are consistent over all ROOT events
#get_leafs - dictates whether exp_dct displays leafs within branches
#db_suffix - this determines the unique 'family' of rangefiles that will be created from the given root file

#Attributes
#tree_dct - dictionary of rfile heiarchy from the trees down; None at bottom level
#exp_dct - dictionary of rfile structure
#N_channels_dct - dictionary parallel to tree_dct; leaf length at bottom level
#hist_dct - a dictionary of histograms pulled from the rfile = {hist_name: hist_handle}
#tree_handle_dct - a dictionary of {tree_name: tree_handle ...}

#Methods
#construct_all_ranges(string<output database name.db>) - writes .db files of ranges of leafs in rfile

class fileTools():
	"""Methods associated with constructing dictionaries in parallel to a ROOT file and analyzing them"""

	def __init__(self, file_name, get_leafs=False, fast_channel_count=True, db_suffix="XRFX", debug=True):
		self.tiers = 0
		self.file_name = str(file_name)
		self.status_good = True
		#Private general stuff
		self.perm_db_suffix = db_suffix

		#Debug stuff
		self.DEBUG = debug
		self.debug_thresh_print = 10000
		self.debug_evt_num = 500
		if self.DEBUG:
			print "fileTool() instance", file_name
			self.perm_db_suffix = "XdebugX"
		#Private rfile management
		self.rfile_directory = "%s_range_files" % self.perm_db_suffix
		if ".root" in file_name:
			#Public attributes
			self.file_handle = R.TFile.Open(self.file_name, 'r')
			self.mode = "ROOT"
			self.exp_dct = {}
			self.N_channels_dct = {}
			self.tree_dct = {}
			self.tree_handle_dct = {}
			self.hist_dct = {}
			self.sister_db = self.__construct_rfile_name()

			#Private attributes

			#explorer params
			self.exp_finished = False
			self.get_leafs = get_leafs

			#range_constructor params
			self.columns = ["br_name TEXT", "leaf_num TEXT", "min REAL", "max REAL"]
			self.minmax_dct = {"Tree0": {"br_name": {"leafnum": ["min", "max"]} } }
			self.minmax_dct = {}
			#construct_all_ranges params
			self.trees = [] #list of tree handles
			self.tree_names = [] #parallel list of tree names - recursive is hard!

			#Channel counting params

			self.fast_channel_count = fast_channel_count
			#Init funcions
			self.__tree_find()
			self.__init_tree_dct()
			self.__init_N_channels_dct()
			#rfile management
			self.sister_db_exists = self.__sister_db_exists()
			if self.sister_db_exists:
				self.__check_constructed_rfile()

		elif ".db" in self.file_name:
			self.mode = "DB"
			self.file_handle = None
			
		elif ".txt" in self.file_name:
			self.mode = "txt"
			self.file_handle = None

		#Other filetypes not recognized
		else:	
			print "Fatal Error: fileTools() Filetype was not recognized as '.txt', '.db', or '.root'"
			sys.exit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 			
	def __tree_find(self, dct = None):
	#Find trees in the Rfile recursively and populate handles to self.trees and names to self.tree_dct
		if not self.exp_dct:
			self.exp_dct = self.__explorer()
		if dct == None:
			dct = dict(self.exp_dct)
		for k, v in dct.iteritems():
			try:
				keytype = v["TYPE"]
			except TypeError:
				continue
			else:
				#Piggy-back off the function to initialize tree_dct
				if str(keytype) in ["<class 'ROOT.TTree'>"]:
					self.trees.append(v["HANDLE"])
					self.tree_names.append(str(k))
					self.tree_handle_dct[str(k)] = v["HANDLE"]
				self.__tree_find(v)
					
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def __init_tree_dct(self):
	#Initialize a dictionary of trees found in the given file, with Non at the bottom of subleaf entries
		for tree in self.trees:
			tree_name = tree.GetName()
			self.tree_dct[tree_name] = {}
			tree.GetEntry(1) #Arbitrary, hopefully channels have consistent sdimension through events
			for branch in tree.GetListOfBranches():
				br_name = branch.GetName()
				self.tree_dct[tree_name][br_name] = {}
				for leafnum in xrange(tree.GetLeaf(br_name).GetLen()):
					self.tree_dct[tree_name][br_name][leafnum] = None

	def __init_N_channels_dct(self, fast=True):
	#Initialize a dictionary of number of subleafs, parallel structure to self.tree_dct
		self.N_channels_dct = copy.deepcopy(self.tree_dct)
		for tree_name in self.N_channels_dct:
			for br_name in self.N_channels_dct[tree_name]:
				q = self.tree_names.index(tree_name)
				tree = self.trees[q]
				N_sl = self.__N_subleaf_counter(tree, br_name,)
				self.N_channels_dct[tree_name][br_name] = N_sl

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	#Pending further development to tolerate TBranchElements, TLeafElements
	def __explorer(self, obj_handle=None, dct=None, get_leafs = None):
	#Construct a dictionary with parallel structure to the ROOT file (named at initialization)
		if get_leafs == None:
			get_leafs = self.get_leafs
		if obj_handle == None:
			obj_handle = self.file_handle
		if dct == None:
			dct = collections.OrderedDict(self.exp_dct)

		obj_name = obj_handle.GetName()
		dct[obj_name] = collections.OrderedDict({"TYPE": type(obj_handle), "HANDLE": obj_handle})
		obj_type = str(type(obj_handle))	
		#Different iterators depending on the ROOT class; recursively populate exp_dct
		if obj_type in ["<class 'ROOT.TFile'>", "<class '__main__.TKey'>", "<class 'ROOT.TDirectoryFile'>"]:
			obj_iter = obj_handle.GetListOfKeys()
			for sub in obj_iter:
				sub = obj_handle.Get(sub.GetName())
				self.__explorer(sub, dct[obj_name], get_leafs=get_leafs)
		elif obj_type in ["<class 'ROOT.TTree'>"]:
			obj_iter = obj_handle.GetListOfBranches()
			for sub in obj_iter:
				sub = obj_handle.GetBranch(sub.GetName())
				self.__explorer(sub, dct[obj_name], get_leafs=get_leafs)
		elif obj_type == "<class '__main__.TBranch'>":
			obj_iter = obj_handle.GetListOfLeaves()
			for sub in obj_iter:
				sub = obj_handle.GetLeaf(sub.GetName())
				self.__explorer(sub, dct[obj_name], get_leafs=get_leafs)
		#Errors at this level are possibly due to custom classes, eg LBNEDataNtp_t - no dictionary
		elif obj_type == "<class '__main__.TBranchElement'>" and get_leafs == True:
			iters = [obj_handle.GetListOfBranches(), obj_handle.GetListOfLeaves(), ]
			for k, obj_iter in enumerate(iters):
				for i, sub in enumerate(obj_iter):
					self.__explorer(sub, dct[obj_name], get_leafs=get_leafs)
		elif obj_type == "<class '__main__.TH1D'>":
			#This is the only time histograms are managed
			self.hist_dct[obj_handle.GetName()] = obj_handle
		elif obj_type == "<class '__main__.TLeafElement'>":
			return
		elif obj_type == "<class '__main__.TLeaf'>":
			return

		return dct

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def __N_subleaf_counter(self, tree, br_name, quiet=False):
	#tree is the tree containing the branch with GetName() of br_name, containing the desired leaf
	#Throws errors for leafs that have a variable number of subleafs; otherwise returns the number of subleafs in a leaf
	#Option fast determines whether every leaf will be checked for having a consistent number of subleafs over all events
		if self.DEBUG:
			#self.fast_channel_count = False
			#print "fast_channel_count set to %s" % self.fast_channel_count
			pass

		#Give the number of subleafs for the first event, in this branch
		if self.fast_channel_count:
			tree.GetEntry(0)
			return tree.GetLeaf(br_name).GetLen()

		tree_size = tree.GetEntries()
		N_subleaf_list = [0]*tree_size
		#Find out the subleaf population for every event	
		for event in xrange(tree_size):
			tree.GetEntry(event)
			leaf = tree.GetLeaf(br_name)
			N_subleaf_list[event] = leaf.GetLen()
			
		#Check that the number of subleafs in the given branch doesn't vary over events
		unq_N =  list(set(N_subleaf_list))
		variation = len(unq_N)
		if variation == 1:
			print "Branch good: %i channels present for all %i events" % (unq_N[0], tree_size)
			return unq_N[0] #Should be the sole entry
		elif variation > 1:
			if not quiet:
				print "Warning at N_subleaf_counter(%s, %s): %s.Len() varies over events" (tree, br_name, br_name)
				if variation < 20:
					print "Number of subleafs varies among: ", unq_N
				else:
					print "Over 20 different values found for the number of subleafs"
			return None
		
	 #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -		
	def construct_all_ranges(self, dbname_out=None):
	#Iterate over all trees in the file to produce a complete db
		mode = "ROOT"
		if dbname_out==None:
			dbname_out = self.sister_db
		elif dbname_out:
			print "Warning at FileTools(%s).construct_all_ranges(%s): Output database will not contribute to master histogram ranges" % (self.file_name, dbname_out)
		self.__file_check(self.construct_all_ranges, (dbname_out, ".db"))
		self.__mode_status_check(mode, self.construct_all_ranges)
		
		#Send all rfiles constructed into self.rfile_directory - can be changed at instantiation
		#Default rfile_directory: XRFX_range_files
		global cd
		pwd = os.getcwd()
		if self.rfile_directory not in os.listdir(pwd):
			os.mkdir(self.rfile_directory)
		with cd("%s/%s" % (pwd, self.rfile_directory)):		
			self.conn = sq3.connect("%s" % dbname_out)
			self.c = self.conn.cursor()
			for i_tree, tree in enumerate(self.trees):	
				try:
					self.range_construct(dbname_out, tree, i_tree, auto=True)
				except:
					print "Fatal Error at construct_all_ranges() - tree %s in database %s could not be constructed" % (tree, dbname_out)
					os.remove(dbname_out)
					sys.exit()
			self.conn.commit()
			self.conn.close()

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	
	def __construct_rfile_name(self):
		name = self.file_name.replace(".root", "")
		name += "_%s.db" % self.perm_db_suffix
		return name
		
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def range_construct(self, dbname_out, tree, i_tree, auto=False):
	#Find ranges for leafs and populate an SQLite3 db
	#Option append will add a new table to an existing database	

		mode = "ROOT"
		self.__file_check(self.range_construct, (dbname_out, ".db"))
		self.__mode_status_check(mode, self.range_construct)
		#auto=False runs a standalone write for a single given tree - 
		if auto == False:
			self.conn = sq3.connect("%s" % dbname_out, isolation_level=None)
			self.c = self.conn.cursor()
		#A new table is constructed for the given tree, overwritten automatically
		cols = ", ".join([col for col in self.columns])
		tab_name = str(tree.GetName())
		try:
			self.c.execute("DROP TABLE %s" % ( tab_name))
			print "Overwriting ", tab_name
		except sq3.OperationalError:
			pass
		self.c.execute("CREATE TABLE %s (%s)" % (tab_name, cols))

		#Initialize Dictionary
		minmax_dct = {}
		tree.GetEntry(1) #Arbitrary, hopefully channels have consistent dimension through events
		tree_name = tree.GetName()
		for branch in tree.GetListOfBranches():
			br_name = branch.GetName()
			minmax_dct[br_name] = {}
			for leafnum in xrange(self.N_channels_dct[tree_name][br_name]):
				minmax_dct[br_name][leafnum] = [10e10,-10e10]
		#Parse Root file
		for entry in xrange(tree.GetEntries()):
			if self.DEBUG and entry > self.debug_evt_num:
				break
			tree.GetEntry(entry)
			for branch in tree.GetListOfBranches():
				br_name = branch.GetName()
				leaf = tree.GetLeaf(br_name)
				N_sl = self.N_channels_dct[tree_name][br_name]
				for leafnum in xrange(N_sl):
					val = leaf.GetValue(leafnum)
					try:
						if val < minmax_dct[br_name][leafnum][0]:
							minmax_dct[br_name][leafnum][0] = val
						if val > minmax_dct[br_name][leafnum][1]:
							minmax_dct[br_name][leafnum][1] = val
					except KeyError:
						print "Fatal Error at range_construct(%s): minmax_dct was initialized incorrectly and may have corrupted %s - Please report to dctROOT admin" % (dbname_out, dbname_out)
						sys.exit()
			if not entry%self.debug_thresh_print:
				print "%s entries finished" % entry
		self.minmax_dct[tab_name] = dict(minmax_dct)
		#Output to db
		for br_name in minmax_dct:
			for leafnum, Lrange in minmax_dct[br_name].iteritems():
				self.c.execute("INSERT INTO %s VALUES ('%s','%s',%7.5f, %7.5f)"\
				% (tab_name, br_name, leafnum, Lrange[0], Lrange[1]))
		print "Ranges written to table %s in file %s" % (tab_name, dbname_out)
		
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def __sister_db_exists(self):
	#This will check whehter the sister_db has been constructed
		pwd = os.getcwd()
		if self.rfile_directory not in os.listdir(pwd):
			return False
		else:
			global cd
			with cd("%s/%s" % (pwd, self.rfile_directory)):	
				pwd = os.getcwd()
				if self.sister_db not in os.listdir(pwd):
					return False
				else:
					return True

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def __check_constructed_rfile(self):
	#Perform various checks on output database - make sure it was constructed properly
		status_good = True
		dbname = self.sister_db
		global cd
		pwd = os.getcwd()
		with cd("%s/%s" % (pwd, self.rfile_directory)):		
			conn = sq3.connect(dbname)
			c = conn.cursor()

			#First check will count that the total number of subleafs were counted
			for tree_name in self.tree_handle_dct:
				tot_N_sl = sum([N_sl for br, N_sl in self.N_channels_dct[tree_name].iteritems()])
				c.execute("SELECT COUNT(*) FROM %s" % tree_name)
				db_N_sl = c.fetchone()[0]
				if tot_N_sl != db_N_sl:
					print "Range file %s failed check for proper size: Reconstructing rangefile" % self.sister_db
					self.construct_all_ranges()
				else:
					return
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -	
	def db_dump(self, text_out, include_tree_name = False):
	#Dump the contents of a database to a .txt file
	#include_tree_name places the tree name at the top - disruptive with txt readers
		db_in = self.file_name

		mode = "DB"
		self.__file_check(self.db_dump, (text_out, ".txt"), (db_in, ".db"))
		self.__mode_status_check(mode, self.db_dump)
		text_handle = open(str(text_out), "w")
		
		#db tables associated with different trees will be listed sequentially
		conn = sq3.connect(str(db_in))
		c = conn.cursor()
		for tree in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"):
			tree_name = str(tree[0])
			if include_tree_name:
				text_handle.write("%s\n" % tree_name)
			for row in c.execute("SELECT * FROM %s" % tree_name):
				text_handle.write("%s %i %s %s \n" %\
				(str(row[0]), int(row[1]), str(row[2]), str(row[3])))
		text_handle.close()			
		conn.close()

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	def txt_to_sql(self, create, *args):
	#The input should be (False/True, ["text_file1","tree_name1"]...)
	#In append mode it will add a text file's data to as already existing sql database.  
	#In create mode it will take multiple text files and create a new sqldatabase from them
		mode = "DB"
		self.__file_check(self.txt_to_sql, (self.file_name, ".db"))
		self.__mode_status_check(mode, self.txt_to_sql)

		dB = sq3.connect(self.file_name)
		cursor = dB.cursor()
		#can 'create' be automated?
		if (create):
			cursor.executescript("drop table if exists rawtpcnoise;")
			#generalize for any input tree_name
			for L in args:
				file_handle = open(L[0],"r")
				tree_name = L[1]
				cursor.execute("CREATE TABLE " + tree_name + "(branch TEXT, leaf INT, min FLOAT, max FLOAT)")  
				for line in file_handle.readlines():
					line  = line.split()
					cursor.execute("INSERT INTO %s VALUES('%s',%s,%s,%s)" % (tree_name,line[0],int(line[1]),float(line[2]),float(line[3])))
		else:
			for L in args:
				file_handle = open(L[0],"r")
				tree_name = L[1]
				cursor.execute("drop table if exists " + tree_name + ";")
				cursor.execute("CREATE TABLE " + tree_name + "(branch TEXT, leaf INT, min FLOAT, max FLOAT)")  
				for line in file_handle.readlines():
					line  = line.split()
					print line
					cursor.execute("INSERT INTO %s VALUES('%s',%s,%s,%s)" % (tree_name,line[0],int(line[1]),float(line[2]),float(line[3])))

		dB.commit()
		cursor.close()

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	#IN PROGRESS
	def __mode_status_check(self, mode, method):
		func = method.__name__
		if mode != self.mode:
			print "Error at %s: Method does not support mode '%s'" % (func, self.mode)
			sys.exit()
		if not self.status_good:
			sys.exit()

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -		
	def __file_check(self, method, *args):
	#each arg is a tuple of (file_name, ".suffix")
		func = method.__name__
		for arg in args:
			if str(arg[1]) not in str(arg[0]):
				print "Error at %s: Improper filetype: '%s' not provided"\
				    % (func, str(arg[1]))
				sys.exit()

	def set_path(self):
	#Find out the os.path info to organize where outputs, inputs etc go
		return

#--------------------------------------------------------------------------------------------

class cd:
	"""Context manager for changing a directory in a 'with' block"""
	def __init__(self, new_path):
		self.new_path = os.path.expanduser(new_path)

	def __enter__(self):
		self.saved_path = os.getcwd()
		os.chdir(self.new_path)

	def __exit__(self, typ, val, traceback):
		os.chdir(self.saved_path)
		#--------------------------------------------------------------------------------------------

script = []
#testing range_reader
if 1 in script:
	DT = dctTools({}).range_reader("test_db")

#Testing range_writer
if 2 in script:
	FT = fileTools("rawtpcnoise_tree_1.root")
	FT.construct_all_ranges("test_db", overwrite=False)
	#dctTools(FT.minmax_dct).printer(trim=False)

#Testing tiers()
if 3 in script:
	FT = fileTools("rawtpcnoise_tree_1.root")
#	fdct = FT.explorer()
	dctTools(fdct).printer()
	print dctTools(test_dct).tiers()

#Testing __tree_find
if 4 in script:
	FT = fileTools("rawtpcnoise_tree_1.root")
	#fdct = FT.explorer()
	print FT.trees
	dctTools(FT.tree_dct).printer()
	
#Testing range_reader append
if 5 in script:
	FT = fileTools("rawtpcnoise_tree_1.root")
	DT = dctTools(FT.tree_dct)
	DT.range_reader("test_db.db", append=True)
	DT.printer()
#Debugging on daq trees
if 6 in script:
	FT = fileTools("daq_hist_0003095_00000.root")
	#FT.explorer()
	fdct = FT.exp_dct
	dctTools(fdct).printer()
#Debugging db_dump
if 7 in script:
	fileTools("test_db.db").db_dump( "deadmeat.txt")
#New tests on Kirby's stuff
if 8 in script:
	FT = fileTools("daq_hist_0003095_00000.root")
	FT.construct_all_ranges("kirby_db.db")
	DT = dctTools(FT.exp_dct)
	kirb_ranges =DT.range_reader("kirby_db.db")
	dctTools(kirb_ranges).printer()
#Testing append option in 
if 9 in script:
	explored_dct = fileTools("daq_hist_0003095_00000.root").tree_dct
	dctTools(explored_dct).printer()
	ranges = dctTools(explored_dct).range_reader("kirby_db.db", append=True)
	dctTools(ranges).printer()
	#!! Called an error related to kirby's root file

#Testing __N_subleaf_counter
if 10 in script:
	FT = fileTools("daq_hist_0003095_00000.root")
	DT = dctTools(FT.N_channels_dct)
	DT.printer(trim=False)
#Test hist_dct
if 11 in script:
	FT = fileTools("daq_hist_0003095_00000.root")
	DT = dctTools(FT.hist_dct)
	DT.printer(trim=False)
#Test best_ranges
if 12 in script:
	FT = fileTools("daq_hist_0003095_00000.root")
	DT = dctTools(FT.tree_dct)
	DT.range_reader("kirby_db.db", append=True)
	DT.get_best_ranges()
	DT.printer()
#Test best_ranges of *args
if 13 in script:
	FT1 = fileTools("daq_hist_0003095_00000.root")
	FT2 = fileTools("rawtpcnoise_tree_1.root")

	DT1 = dctTools(FT1.tree_dct)
	DT1.range_reader("kirby_db.db", append=True)
	DT2 = dctTools(FT2.tree_dct)
	#DT2.range_reader("test_db.db", append=True)

	DT4 = dctTools({})
	DT4.get_best_ranges(DT1, DT2)

#Complex/undocumented classes break the program
if 14 in script:
	FT3 = fileTools("manytrees.root", get_leafs=True)
	FT3.construct_all_ranges("many_db.db")
	DT3 = dctTools(FT3.exp_dct)
	DT3.printer()
	DB = fileTools("many_db.db")
	DB.db_dump("many_db.txt")
#Setting up permanent db residents
if 15 in script:
	FT2 = fileTools("rawtpcnoise_tree_1.root")
	FT2.construct_all_ranges()
	print FT2.sister_db
	FT1 = fileTools(FT2.sister_db)
	FT1.db_dump("sister.txt")
#Test gabe's txt_to_sql 
if 16 in script:
	#FT = fileTools("kirby_db.db").db_dump("kirby.txt")
	FT = fileTools("gabe_db.db")
	FT.txt_to_sql(False, ("kirby.txt", "kirbytree"))
	FT2 = fileTools("gabe_db.db").db_dump("gabe_db.txt")
#Test __check_constructed_rfile
if 17 in script:
	FT = fileTools("daq_hist_0003095_00000.root")


