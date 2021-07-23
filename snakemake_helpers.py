# snakemake_helpers.py

import glob
import os
import re
import sys
import shutil
import gzip

def empty_file_check(config):
	READDIR = config["Paths"]["Reads"]
	EMPTYDIR = os.path.join(READDIR + "/empty")
	RENAMEDDIR = os.path.join(READDIR + "/renamed")

	# make directory to hold empty files
	if not os.path.exists(EMPTYDIR):
		os.makedirs(EMPTYDIR)

	# check for empty R1 files, if empty, move R1 and mate to empty dir
	read1Files = glob.glob(os.path.join(RENAMEDDIR, "*R1*"))

	for r1 in read1Files:
		r2 = re.sub("R1", "R2", r1)
		print("Looking at " + r1 + " and " + r2)
		# open the R1 file and count the number of ">" characters
		sequenceFile = gzip.open(r1, "rt")
		data = sequenceFile.read()
		numSeqs = data.count(">")
		print("Number of sequences is " + str(numSeqs))
		sequenceFile.close()

		if numSeqs == 0:
			print (r1 + "is empty")
			shutil.move(r1, EMPTYDIR)
			shutil.move(r2, EMPTYDIR)

def get_new_names(config):
	MAP = config["Paths"]["Map"]
	nameList = []
	mappingFile = open(MAP)

	next(mappingFile) # skip first line (header)

	for line in mappingFile:
		lineSplit = line.split("\t")
		nameList.append(lineSplit[0])

	mappingFile.close()
	return(nameList)

def build_search_patterns(read_pattern_list, read_extension_list):

		search_pattern_list = []

		for curr_read_pattern in read_pattern_list:

				for curr_extension in read_extension_list:
						search_pattern = "*" + curr_read_pattern + "*" + curr_extension

						if not search_pattern in search_pattern_list:
								search_pattern_list.append(search_pattern)

		return(search_pattern_list)

def rename_files(config):

	READDIR = config["Paths"]["Reads"]
	
	# If there are valid read files sitting in /data, rename them for consistency:
	
	# First, build all possible read file patterns depending on Patterns in config file (these will always be there)
	read1Patterns = config["Patterns"]["Read1Identifiers"]
	read2Patterns = config["Patterns"]["Read2Identifiers"]
	index1Patterns = config["Patterns"]["Index1Identifiers"]
	index2Patterns = config["Patterns"]["Index2Identifiers"]
	readExtensions = config["Patterns"]["ReadExtensions"]
	
	allRead1Patterns = build_search_patterns(read1Patterns, readExtensions)
	allRead2Patterns = build_search_patterns(read2Patterns, readExtensions)
	allIndex1Patterns = build_search_patterns(index1Patterns, readExtensions)
	allIndex2Patterns = build_search_patterns(index2Patterns, readExtensions)
	
	# Second, go look in the READDIR directory for any files matching these patterns and store in a list
	allPatternsList = allRead1Patterns + allRead2Patterns + allIndex1Patterns + allIndex2Patterns
	print(allPatternsList)

	inputFileList = []
	
	for pattern in allPatternsList:
		inputFileList.extend(glob.glob(READDIR + "/" + pattern))
	
	# Third, if there are any valid files in the READDIR directory, rename them with a consistent structure and store in /READDIR/renamed/
	# Original files with original file names will be moved to the /READDIR/archived/ directory after renaming is complete
	
	# Check that there's stuff in inputFileList
	if (len(inputFileList) != 0):
	
		for inputFile in inputFileList:
	
			inputFileName = os.path.basename(inputFile)
			index = -1
			pattern  = ""
			extension = ""
			readType = ""
	
			# Get extension for the current file so the re-named file will have the same extension
			for extPattern in readExtensions:
				if inputFileName.endswith(extPattern):
					extension = extPattern

			# Look for the R1 designator in the current file name
			for read1Pattern in read1Patterns:
				index = inputFileName.find(read1Pattern)
				if index != -1:
					pattern = read1Pattern
					readType = "R1"
					break
	
			# No R1: look for an R2 pattern
			if index == -1:
				for read2Pattern in read2Patterns:
					index = inputFileName.find(read2Pattern)
					if index != -1:
						pattern = read2Pattern
						readType = "R2"
						break

			# No R1 or R2: look for an I1 pattern
			if index == -1:
				for index1Pattern in index1Patterns:
					index = inputFileName.find(index1Pattern)
					if index != -1:
						pattern = index1Pattern
						readType = "I1"
						break
			
			# No R1, R2, or I1: look for an I2 pattern
			if index == -1:
				for index2Pattern in index2Patterns:
					index = inputFileName.find(index2Pattern)
					if index != -1:
						pattern = index2Pattern
						readType = "I2"
						break
	
			# If you can't find any of those designator something's probably wrong, stop
			if index == -1:
				sys.stderr.writdxqe("No R1 or R2 pattern found in " + inputFileName)
				sys.exit()
	
			# Otherwise, let's build the new name
			# Extract the sample name + the read designator, and replace everything that may come after with _R[12].fastq.gz
			newFileName = inputFileName[:index] + "_" + readType + extension

			# Check that the /data/renamed directory exists (I don't want to rename original sequence files!)
			if not os.path.exists(READDIR + "/renamed"):
				os.makedirs(READDIR + "/renamed")
	
			# Copy the original files to the /data/renamed directory
			shutil.copy(READDIR + "/" + inputFileName, READDIR + "/renamed/" + inputFileName)
	
			# Rename the files within the /data/renamed directory
			os.rename(READDIR + "/renamed/" + inputFileName, READDIR + "/renamed/" + newFileName)
			# Check if the new file name ends with a ".gz," and if not, gzip the file
			if not newFileName.endswith(".gz"):
				newGZFile = READDIR + "/renamed/" + newFileName + ".gz"
				with open(inputFile, "rb") as f_in, gzip.open(newGZFile, "wb") as f_out:
					f_out.writelines(f_in)


			# Once renamed, move the original files from the data directory to the archived directory so snake won't rename them again next time
			if not os.path.exists(READDIR + "/archived"):
				os.makedirs(READDIR + "/archived")
			shutil.move(READDIR + "/" + inputFileName, READDIR + "/archived/" + inputFileName)



