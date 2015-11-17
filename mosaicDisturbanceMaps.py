#!/bin/sh
import sys, os, fnmatch
import random
def readDefaults(defaultFile):
    out_dict = {}
    f = open(defaultFile)
    for line in f:
        input_vars = line.split(";")
        if len(input_vars) == 3:
            out_dict[input_vars[1].replace(" ", "")] =\
            r'"{0}"'.format(input_vars[2].replace(" ", "").replace("\n", ""))
    f.close()
    # Specific formatting
    for key in 'searchStrings', 'pathRows', 'bands', 'searchDir', 'rootDir':
        out_dict[key] = out_dict[key].strip("\"").rstrip("\n").split(",")
    return out_dict

def getDirectories(roots, searchDir, pathrows):
    out_list = []
    print '\n\nFinding directories'
    #print pathrows
    print '{0} in {1}'.format(', '.join(searchDir), ', '.join(roots))
    #print searchDir
    #print roots	
    for pathrow in pathrows:
        for root in roots:
            for d in searchDir:
                new_folder = os.path.join(root, pathrow, d) #Changed this b/c I felt it was less error prone -Jamie#"{0}/{1}/{2}".format(root, pathrow, d)
                if os.path.exists(new_folder):
                    out_list.append(new_folder)            
    #print out_list    
    return out_list 
    
def searchDirectory(directory, search_strings):
    local_files = []
    print '\nSearching directory '
    print directory
    print 'for this string'
    print ', '.join(search_strings)
    
    for path, names, files in os.walk(directory):
        for f in files:
            if f.endswith(".bsq"):
                #go_ahead = 1
		go_ahead=0

                for search in search_strings:
                    #print f
		    #print search
		    #print fnmatch.fnmatch(f,search)
		    #if fnmatch.fnmatch(f,search): go_ahead = 0
		    #import pdb; pdb.set_trace()
		    #if search[0] == "!":	
		    #	if fnmatch.fnmatch(f,search[1:]): 
		    #	    local_files.remove(path+"/"+f)	
		    #else: 
		    if fnmatch.fnmatch(f,search): local_files.append(os.path.join(path, f))
		#now cull out the bad matches
		for search in search_strings:
		    if search[0] == "!":
			#import pdb; pdb.set_trace()
			if fnmatch.fnmatch(f, search[1:]):
			   #import pdb; pdb.set_trace()
			   if os.path.join(path,f) in local_files:
			       local_files.remove(os.path.join(path, f))

                #if go_ahead: local_files.append(path + "/" + f)
    for item in sorted(local_files):
        print os.path.basename(item)
    #import pdb; pdb.set_trace()
    return local_files

def createMosaic(files, bands, outputFile):
    print '\nCreating mosaic'
    print 'from files' 
    for f in files:
        print os.path.basename(f)
    print 'and bands: {0}'.format(', '.join(bands))
    #print bands
    #import pdb; pdb.set_trace()
    run_id = str(random.randint(0, 1000))
    exec_string = "gdalbuildvrt -srcnodata 0 {0}.vrt ".format(outputFile)
    for f in files: exec_string += "{0} ".format(f)
    os.system(exec_string)

    selected_bands = "gdalbuildvrt -separate -srcnodata 0 temp_stack_{0}.vrt ".format(run_id)
    cleanup = ['temp_stack_{0}.vrt'.format(run_id)]
    for band in bands:
        newfile = "ts_{0}_{1}.vrt".format(band, run_id)
        os.system("gdal_translate -of VRT -b {0} -a_nodata 0 {1}.vrt {2}".format(band, outputFile, newfile))
        selected_bands += newfile + " "
        cleanup.append(newfile)
    os.system(selected_bands)
    os.system("gdal_translate -of ENVI -a_nodata 0 temp_stack_{1}.vrt {0}.bsq".format(outputFile, run_id))
    for f in cleanup:
        try: os.remove(f)
        except: pass
    print "Created {0}".format(outputFile)
    
def parsePathrow(combos):
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
    newfile = outputFile + "_meta.txt"
    g = open(newfile, "wb")
    g.write("Scenes and files included in mosaic:\n")
    for pathrow in pathrows:
        found = []
        for f in files:
            if pathrow in f: found.append(f)
        if not found: outstring = "No files found for scene {0}\n".format(pathrow)
        elif len(found) > 1:
            outstring = "Multiple files found for scene {0}:\n".format(pathrow)
            for f in found: outstring += "\t{0}\n".format(f)
        else:
            outstring = "{0}: {1}\n".format(pathrow, found[0])
        g.write(outstring)
    g.close()

                        
def main(inputParams):
    for var in inputParams: exec "{0} = {1}".format(var, inputParams[var])
    if not os.path.exists(outputDir): os.mkdir(outputDir)
    os.chdir(outputDir)
    outputFile = "{0}/{1}".format(outputDir, outMosaic)
    all_files = []
    pathRows = parsePathrow(pathRows)
    #import pdb; pdb.set_trace()
    for directory in getDirectories(rootDir, searchDir, pathRows):
        for f in searchDirectory(directory, searchStrings):
            all_files.append(f)
    checkFoundFiles(all_files, pathRows, outputFile)
    createMosaic(all_files, bands, outputFile)
            
if __name__ == '__main__':
    defaultFile = sys.argv[1]
    inputParams = readDefaults(defaultFile)
    sys.exit(main(inputParams))
