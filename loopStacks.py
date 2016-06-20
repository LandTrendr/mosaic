'''
loopStacks.py

Inputs:
	- starting parameter files (year/band does not need to be filled out)
	- year range [ie. 1985-1990]
	- output directory
	- outputfile prefix
	
Outputs:
	- stacked mosaic per year

'''
import sys, os
import stackMosaics as stack
from lthacks.lthacks import *

def parseYearRange(yrange):
	ends = yrange.strip().split("-")
	end1 = int(ends[0])
	end2 = int(ends[1])
	
	return range(end1, end2+1)

def main(listOfParams, yearRange, outputDir, outputPrefix):
	
	params = [os.path.realpath(i) for i in listOfParams]
	outdir = os.path.realpath(outputDir)
	
	years = parseYearRange(yearRange)
	
	this_script = os.path.abspath(__file__)
	
	for y in years:
		outpath = os.path.join(outdir, outputPrefix + "_" + str(y) + ".bsq")
		stack.main(params, outpath, yearOverride=y)
	
		createMetadata(sys.argv, outpath, lastCommit=getLastCommit(this_script))
	
if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1:-3], args[-3], args[-2], args[-1]))
	


