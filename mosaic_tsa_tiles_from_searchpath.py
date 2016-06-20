'''
mosaic_tsa_tiles_from_searchpath.py

Masks buffers & mosaics all TSA tiles listed in a parameter file.

Inputs:
-search_path (in quotes)
-scene index (index of os.path.basename(maplist_path).split("_")[index] that would return the path-row)
-start_band
-end_band
-output_path

Output:
-1 mosaic

Usage: 
python mosaic_tsa_tiles_from_searchpath.py "<search_path>" <scene_index> <start_band> <end_band> <output_path>
'''
import glob, sys
from mosaicDisturbanceMaps_nobuffer import *

def find_tiles(search_path):
	tiles = glob.glob(search_path)
	return tiles

def main(search_path, scene_index, start_band, end_band, output_path):
	
	tiles = find_tiles(search_path)
	if len(tiles) == 0:
		sys.exit("ERROR: No TSA files found from search path '" + search_path + "'")
		
	#mask out buffers
	output_dir = os.path.dirname(output_path)
	nobuffer_files = maskBuffers(tiles, output_dir, sceneIndex=scene_index)
	
	#create mosaic from masked raster
	bands = range(int(start_band), int(end_band)+1)
	createMosaic(nobuffer_files, bands, output_path.replace('.bsq',''))
	
	#clean up
	print "Cleaning up..."
	for f in nobuffer_files:
		os.remove(f)
		os.remove(f.replace('bsq','hdr'))
		os.remove(f.replace('.bsq','_meta.txt'))
	print " Done!"
		
if __name__ == '__main__':
	args = sys.argv[1:]
	print args
	sys.exit(main(*args))