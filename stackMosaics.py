'''stackMosaics.py

Inputs:
	- list of parameter files as 1st set of arguments
	- outputfile path as last argument
	
Outputs:
	- stacked mosaic, hdr, & metadata
	
ex: python stackMosaics.py brightness.txt wetness.txt greenness.txt composite.bsq
'''

import mosaicDisturbanceMaps_nobuffer as mosaic
import sys, gdal, shutil
from gdalconst import *
from lthacks.intersectMask import *
from lthacks.lthacks import *
from tempfile import mkstemp

#define landtrendr bands
ltbands = [0 for x in range(30)]
for i in range(1,30): ltbands[i] = 1983 + i
	
def edithdr(path, band_nums, mosaics):
	#open hdr file
	hdrPath = path.replace('bsq', 'hdr')
	hdr = open(hdrPath, 'r')
	
	#create new tmp file
	tmpPath = '{0}.tmp.txt'.format(os.path.basename(hdrPath))
	tmp, tmpPath = mkstemp()

	new_file = open(tmpPath, 'w')

	#replace band names in file
	band = 0
	for line in hdr:
		if not line.startswith('Band'):
			new_file.write(line)
		else:
			band += 1
			band_num = band_nums[band-1]
			year = ltbands[int(band_num)]
			oldline = 'Band {0}'.format(band)
			layername = os.path.splitext(os.path.basename(mosaics[band-1]))[0]
			new_file.write(line.replace(oldline, layername + " " + str(year)))

	#close files
	new_file.close()
	os.close(tmp)
	hdr.close()
	#replace old hdr file
	os.remove(hdrPath)
	shutil.move(tmpPath, hdrPath)
	os.chmod(hdrPath, 0555)
	

def main(listOfParams, outpath, yearOverride=None):

	#first create 1-band mosaics
	print "\nCreating 1-band mosaics... "
	bands = []
	mosaics = []
	for param in listOfParams:
		param_dict = mosaic.readDefaults(param)
		if yearOverride:
			param_dict['bands'] = [str(ltbands.index(int(yearOverride)))]
		elif 'year' in param_dict.keys():
			param_dict['bands'] = [str(ltbands.index(int(param_dict['year'])))]
		else:
			pass
		
		#create list of bands & mosaic outputs
		if len(param_dict['bands']) > 1:
			sys.exit("Can only stack 1-band mosaics.")
		else:
			bands.append(param_dict['bands'][0])
			outdir = param_dict['outputDir'].replace('"','')
			file = param_dict['outMosaic'].replace('"','')
			mosaics.append(os.path.join(outdir, file + ".bsq"))
		
		mosaic.main(param_dict)
		
	#ensure mosaics/bands are sorted
	bands = sorted(bands)
	mosaics = [x for (y,x) in sorted(zip(bands,mosaics))]
		
	#then stack mosaics
	print "\nStacking 1-band mosaics... "
	outbands = []
	for ind,m in enumerate(mosaics):
		ds = gdal.Open(m, GA_ReadOnly)
		band = ds.GetRasterBand(1)
		outbands.append(band.ReadAsArray())
		if ind == 0:
			projection = ds.GetProjection()
			driver = ds.GetDriver()
			transform = ds.GetGeoTransform()
			nodata = band.GetNoDataValue()
			dt = band.DataType
	
	saveArrayAsRaster_multiband(outbands, transform, projection, driver, outpath, dt, nodata=nodata)
	
	edithdr(outpath, bands, mosaics)
	
	this_script = os.path.abspath(__file__)
	createMetadata(sys.argv, outpath, lastCommit=getLastCommit(this_script))
	
	#clean up
	if os.path.exists(outpath):
		print "\nCleaning up..."
		for m in mosaics:
			os.remove(m)
			os.remove(m.replace('bsq','hdr'))
			os.remove(m.replace('bsq','vrt'))
			os.remove(m.replace('.bsq','_meta.txt'))
			os.remove(m.replace('bsq','bsq.aux.xml'))
		print "\n Done!"
			
if __name__ == '__main__':
	try:
		year = int(sys.argv[-1])
	except ValueError:
		sys.exit(main(sys.argv[1:-1], sys.argv[-1]))
	else:
		sys.exit(main(sys.argv[1:-2], sys.argv[-2], yearOverride=year))
	
	
	
	
	
	