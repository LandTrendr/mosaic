#!/bin/sh

#updated by Tara Larrue (tlarrue@bu.edu) on 2/3/15 to clip buffers before mosaicking
#updated by Tara Larrue (tlarrue@bu.edu) on 9/8/15 to be compatible with islay 
#updated by Tara Larrue (tlarrue@bu.edu) on 9/10/15 to use older mosaicking method b/c of gdal_merge overlapping issue

import sys, os, fnmatch
import random
from lthacks.lthacks import *

TSA_MASKS = "/vol/v1/general_files/datasets/spatial_data/us_contiguous_tsa_masks_nobuffer/us_contiguous_tsa_nobuffer_{0}.bsq"

def readDefaults(defaultFile):
	'''extract parameters from a parameter file'''
	out_dict = {}
	f = open(defaultFile)
	for line in f:
		input_vars = line.split(";")
		if len(input_vars) == 3:
			out_dict[input_vars[1].replace(" ", "")] =\
			r'"{0}"'.format(input_vars[2].replace(" ", "").replace("\n", ""))
	f.close()
	
	#modify if not pathrow argument (not mosaicking from scenes directories)

	# Specific formatting
	for key in 'searchStrings', 'pathRows', 'bands', 'searchDir', 'rootDir':
		try:
			out_dict[key] = out_dict[key].strip("\"").rstrip("\n").split(",")
		except KeyError:
			if key == 'pathRows':
				out_dict[key] = None
			else:
				raise KeyError
		
	return out_dict

def getDirectories(roots, searchDir, pathrows):
	'''creates a list of directories'''
	out_list = []
	print '\n\nFinding directories'
	print '{0} in {1}'.format(', '.join(searchDir), ', '.join(roots))
	for pathrow in pathrows:
		for root in roots:
			for d in searchDir:
				new_folder = os.path.join(root, pathrow, d) 
				if os.path.exists(new_folder):
					out_list.append(new_folder)
	return out_list 
	
def searchDirectory(directory, search_strings):
	'''search a directory for list of files using search strings'''
	local_files = []
	print '\nSearching directory '
	print directory
	print 'for this string'
	print ', '.join(search_strings)
	
	for path, names, files in os.walk(directory):
		for f in files:
			if f.endswith(".bsq"):

				go_ahead=0  

				for search in search_strings:
					if fnmatch.fnmatch(f,search): local_files.append(os.path.join(path, f))
					
				#now cull out the bad matches
				for search in search_strings:
					if search[0] == "!":

						if fnmatch.fnmatch(f, search[1:]):

			   				if os.path.join(path, f) in local_files:
			   					local_files.remove(os.path.join(path, f))

	for item in sorted(local_files):
		print os.path.basename(item)

	return local_files

def createMosaic(files, bands, outputFile):
	'''generate a mosaic from a list of rasters and bands'''

	bands = [str(b) for b in bands]

	print '\nCreating mosaic'
	print 'from {0} files'.format(str(len(files)))
	for f in files:
		print os.path.basename(f)
	print 'and bands: {0}'.format(', '.join(bands))

	run_id = str(random.randint(0, 1000))
	exec_string = "gdalbuildvrt -srcnodata 0 {0}.vrt ".format(outputFile)
	for f in files: exec_string += "{0} ".format(f)
	os.system(exec_string)

	selected_bands = "gdalbuildvrt -separate -srcnodata 0 temp_stack_{0}.vrt ".format(run_id)
	cleanup = ['temp_stack_{0}.vrt'.format(run_id)]
	for band in bands:
		newfile = "ts_{0}_{1}.vrt".format(band, run_id)
		os.system("gdal_translate -of VRT -b {0} -a_nodata 0 {1}.vrt {2}".format(band, 
		outputFile, newfile))
		selected_bands += newfile + " "
		cleanup.append(newfile)
	os.system(selected_bands)
	os.system("gdal_translate -of ENVI -a_nodata 0 temp_stack_{1}.vrt {0}.bsq".format(outputFile, 
	run_id))
	for f in cleanup:
		try: os.remove(f)
		except: pass
	print "Created {0}".format(outputFile)
	
def parsePathrow(combos):
	'''create a list of 6-digit TSAs from a string of TSA combos'''
	scenes = []
	for combo in combos:
		paths, rows = combo.split("/")
		for l in 'paths', 'rows':
			exec "{0} = {0}.split(\"-\")".format(l)
			exec "{0} = map(int, {0})".format(l)
			exec "if len({0}) == 2 and {0}[0] > {0}[1]: {0} = sorted(range({0}[1], {0}[0] + 1))".format(l)
			exec "if len({0}) == 2 and {0}[0] < {0}[1]: {0} = range({0}[0], {0}[1] + 1)".format(l)
		for path in paths:
			for row in rows:
				scenes.append("{0}{1}".format(str(path).zfill(3), str(row).zfill(3)))
	return scenes

def checkFoundFiles(files, pathrows, outputFile):
	'''Print list of rasters to be mosaics and any conflicts'''
	newfile = outputFile + "_meta.txt"
	g = open(newfile, "wb")
	g.write("Scenes and files included in mosaic:\n")
	for pathrow in pathrows:
		found = []
		for f in files:
			if "_"+pathrow+"_" in f: found.append(f)
		if not found: outstring = "No files found for scene {0}\n".format(pathrow)
		elif len(found) > 1:
			outstring = "Multiple files found for scene {0}:\n".format(pathrow)
			for f in found: outstring += "\t{0}\n".format(f)
		else:
			outstring = "{0}: {1}\n".format(pathrow, found[0])
		g.write(outstring)
	g.close()
	
def maskBuffers(files, outputDir, sceneIndex=None):
	'''mask buffers of list of rasters using TSA_MASKS'''
	nobuffer_files = []
	for f in files:
		if sceneIndex:
		
			scene = sixDigitTSA(os.path.basename(f).split("_")[int(sceneIndex)])
			
		else:
	
			try:
				scene = f.split('/')[f.split('/').index('scenes')+1]
				toto = int(scene)
			except ValueError:
				scene = os.path.basename(f).split('_')[3]
				try:
					toto = int(scene)
				except ValueError:
					if len(scene) != 6:
						print "WARNING: This is not in disturbance map format. Checking to \
						see if it is an insect map..."
						scene = sixDigitTSA(os.path.basename(f).split('_')[2])
						try:
							toto = int(scene)
						except ValueError:
							sys.exit("Cannot find scene number from file: "+ os.path.basename(f)+ 
							" Found: "+ scene)
		
		mask = TSA_MASKS.format(scene)
		
		print "\nMasking buffer for: ", f
		output = os.path.join(outputDir, os.path.splitext(os.path.basename(f))[0] + "_nobuff.bsq")
		statement = "intersectMask {0} {1} {2} --src_band=ALL --meta='Temp file made from\
		 mosaicDisturbanceMaps_nobuffer.py'".format(f, mask, output)

		if not os.path.exists(output):
			os.system(statement)
		if os.path.exists(output):
			nobuffer_files.append(output)
		else:
			print sys.exit("Buffer masking failed: " + f + "\n Exiting.")

	return nobuffer_files

						
def main(inputParams):
	#extract parameters
	for var in inputParams: exec "{0} = {1}".format(var, inputParams[var])
	
	#create output directory if it doesn't exist
	if not os.path.exists(outputDir): os.mkdir(outputDir)
	os.chdir(outputDir)
	outputFile = os.path.join(outputDir,outMosaic)
	
	#parse path-rows and create a list of rasters to mosaic
	all_files = []
	if pathRows:
		pathRows = parsePathrow(pathRows)
	else:
		pathRows = []
		
	for directory in getDirectories(rootDir, searchDir, pathRows):
		for f in searchDirectory(directory, searchStrings):
			all_files.append(f)
	checkFoundFiles(all_files, pathRows, outputFile)

	#mask out buffers
	nobuffer_files = maskBuffers(all_files, outputDir)
	
	#create mosaic from masked rasters
	createMosaic(nobuffer_files, bands, outputFile)
	
	#clean up
	print "Cleaning up..."
	for f in nobuffer_files:
		os.remove(f)
		os.remove(f.replace('bsq','hdr'))
		os.remove(f.replace('.bsq','_meta.txt'))
	print " Done!"
		
			
if __name__ == '__main__':
	defaultFile = sys.argv[1]
	inputParams = readDefaults(defaultFile)
	sys.exit(main(inputParams))
