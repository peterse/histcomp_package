#E Peters Gabe Nowak 3/11/2015
#DQMHistComp: Full analysis package for rescaling histograms, creating profiles, and comparing using

import rHist as rH
import dctROOT as dR
from optparse import OptionParser

#Reads in the following options:
#--input
#--range - List of range files corresponding to 
#--outdir - Location of the outputs directory
parser = OptionParser()
parser.add_option("--input",dest="input",help="Ordered input files, .root only",type='string', nargs=self.NFILES)
parser.add_option("--range",dest = "rfiles", help = "Ordered range file inputs, .db only", type='string', nargs=self.NFILES)
parser.add_option("--outdir", dest = "outdir", help = "Output directory file", type ='string')
(options, args) = parser.parse_args()

#Instatiate OptionsClass
my_options = rH.OptionsClass()

#################################################################
# # # # # # # # # # # # USER INPUTS # # # # # # # # # # # # # # #

my_options.







# # # # # # # # # # # # END INPUT # # # # # # # # # # # # # # # #
#################################################################


rH.Comparator(OUT_DIR= , INPUT= 
