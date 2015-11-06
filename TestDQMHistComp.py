#TestDQMHistComp.py
#Barrage of tests to check user's environment for proper file management
#Evan Peters 3/11/2015

import unittest
import shutil
import os, sys

def check_mods():
	mods_good = True
	missing = []
	try:
		import rHist as rH
	except:
		mods_good = False
		missing.append("rHist.py")
	try:
		import dctROOT as dR
	except:
		mods_good = False
		missing.append("dctROOT.py")
	try:
		import DQMHistComp as DQM
	except:
		mods_good = False
		missing.append("DQMHistComp.py")
	if not mods_good:
		print "Missing modules %s; recover them and place them in the current directory, then test again" % ", ".join([mod for mod in missing])
		sys.exit()

check_mods()

import rHist as rH
import dctROOT as dR
import DQMHistComp as DQM

class OutputTestBatch(unittest.TestCase):
	"""Barrage of tests for output management in the user's environment"""

	test_dir = "test_dir"
	test_input = ["test_file_1.root", "test_file_2.root"]
	CompInst = rH.Comparator(OUT_DIR=test_dir, INPUT=test_input, debug=True, db_suffix="XdebugX", quiet=True)
	CompInst.execute()
	rfile_dir = CompInst.rfile_directory

	def test_output_created(self):
		self.assertIn(self.test_dir, os.listdir(os.getcwd()))

	def test_rfiles_dir(self):
		self.assertIn(self.test_dir, os.listdir(os.getcwd()))
	
	def test_rfiles_made(self):
		with dR.cd(self.rfile_dir):
			pwd = os.getcwd()
			self.assertTrue(len(os.listdir(pwd)) == len(self.test_input))

	def tearDown(self):
		for dr in [self.test_dir, self.rfile_dir]:
			shutil.rmtree("/%s" % dr)


unittest.main()


#Test ideas
# DQMHistComp read only






















