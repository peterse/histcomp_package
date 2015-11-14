# histcomp_package
DQMHistComp package contents:

DQMHistComp.py - The application that will plot input .root file histograms on uniform ranges and run a histogram analysis
SetOptions.txt - A sample input file for DQMHistComp.py
BatchMake.py - An application to create batches of files that contribute to uniform histogram ranges, and also initializes sqlite3 databases of histogram ranges for .root files
BatchMake.txt - A sample input file for BatchMake.py
dctROOT.py - a module of tools for communication between SQL, ROOT, and Python objects

# # # # # # # INSTALLATION # # # # # # # 
1. CONFIGURE PATHS
2. 
# # # # # # # INSTRUCTIONS FOR USE # # # # # # # 
1. CREATE A NEW BATCH: Choose the .root files which will contribute their branch ranges to the output histograms. Choose a batch name (BATCHNAME) and the files it will contain (APPEND) and create an input .txt file- use BatchMake.txt as a reference for running this script
2. RUN BATCHMAKE.PY: Run BatchMake.py with the above .txt file as input, eg:
	'python BatchMake.py -i my_batch_options.txt
The first time a .root file is passed to BatchMake.py, the program will construct an SQL database of its branch ranges - this will take a while! 
3. CREATE A NEW OPTIONS SET: Choose the .root files (INPUT) to run the histogram analysis on, the files whose ranges you wish to contribute to the histograms (eg. pass your batch name to (RANGEFILE)), and the output directory (OUT_DIR) and create an input .txt file - use SetOptions.txt as a reference.
4. RUN DQMHistComp.py: Run DQMHistComp.py with the above .txt file as input, eg:
	'python DQMHistComp.py -i my_options.txt'
This will populate the output directory 
5. Explore options: BatchMake.py has options for viewing batches and batch contents, and for removing certain files from a given batch. DQMHistComp.py has a number of advanced settings, like constructing profile histograms, using weight branches, and whether the input .root files will contribute their ranges to the uniform histograms.


Evan Peters and Gabe Nowak
A set of python modules and .txt example files for combining histogram ranges and publishing histogram comparisons; intended for use with MicroBooNE and Minerva experiments at Fermilab
