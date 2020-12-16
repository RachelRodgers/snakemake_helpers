# snakemake_helpers.py

import glob
import os
import re
import sys
import shutil

def build_search_patterns(read_pattern_list, read_extension_list):

		search_pattern_list = []

		for curr_read_pattern in read_pattern_list:

				for curr_extension in read_extension_list:
						search_pattern = "*" + curr_read_pattern + "*" + curr_extension

						if not search_pattern in search_pattern_list:
								search_pattern_list.append(search_pattern)

		return(search_pattern_list)

def rename_files(config, include_idx = False):

	READDIR = config["Paths"]["Reads"]
	
	# If there are valid read files sitting in /data, rename them for consistency:
	
	# First, build all possible read file patterns depending on Patterns in config file (these will always be there)
	read1Patterns = config["Patterns"]["Read1Identifiers"]
	read2Patterns = config["Patterns"]["Read2Identifiers"]
	readExtensions = config["Patterns"]["ReadExtensions"]
	
	allRead1Patterns = build_search_patterns(read1Patterns, readExtensions)
	allRead2Patterns = build_search_patterns(read2Patterns, readExtensions)
	
	# Second, go look in the READDIR directory for any files matching these patterns and store in a list
	allPatternsList = allRead1Patterns + allRead2Patterns

	# If we need to include index files:
	if (include_idx == True):
		index1Patterns = config["Patterns"]["Index1Identifiers"]
		index2Patterns = config["Patterns"]["Index2Identifiers"]

		allIndex1Patterns = build_search_patterns(index1Patterns, readExtensions)
		allIndex2Patterns = build_search_patterns(index2Patterns, readExtensions)

		allPatternsList = allPatternsList + index1Patterns + index2Patterns
		
	inputFileList = []
	
	for pattern in allPatternsList:
		inputFileList.extend(glob.glob(READDIR + "/" + pattern))
	
	# Third, if there are any valid files in the READDIR directory, rename them with a consistent structure and store in /READDIR/renamed/
	# Original files with original file names will be moved to the /READDIR/archived/ directory after renaming is complete
	
	# Check that there's stuff in inputFileList
	if (len(inputFileList) != 0):
	
		for inputFileName in inputFileList:
	
			inputFileName = os.path.basename(inputFileName)
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
	
			# If you can't find an R1 pattern, look for an R2 pattern
			if index == -1:
				for read2Pattern in read2Patterns:
					index = inputFileName.find(read2Pattern)
					if index != -1:
						pattern = read2Pattern
						readType = "R2"
						break
	
			# If you can't find the R1 or R2 designator something's probably wrong, stop
			if index == -1:
				sys.stderr.write("No R1 or R2 pattern found in " + inputFileName)
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
	
					# Once renamed, move the original files from the data directory to the archived directory so snake won't rename them again next time
			if not os.path.exists(READDIR + "/archived"):
				os.makedirs(READDIR + "/archived")
			shutil.move(READDIR + "/" + inputFileName, READDIR + "/archived/" + inputFileName)


