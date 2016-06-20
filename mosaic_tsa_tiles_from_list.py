'''
mosaic_tsa_tiles_from_list.py

Masks buffers & mosaics all TSA tiles listed in a parameter file.

Inputs:
-maplist_path
-scene index (index of os.path.basename(maplist_path).split("_")[index] that would return the path-row)
-start_band
-end_band
-output_path

Output:
-1 mosaic

Usage: 
python mosaic_tsa_tiles_from_list.py <maplist_path> <scene_index> <start_band> <end_band> <output_path>
'''
import glob, sys
from mosaicDisturbanceMaps_nobuffer import *

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	
	#open parameter file
	txt = open(file, 'r')
	
	#skip 1st line (title line)
	next(txt)
	
	#define empty map list
	map_list = []
	
	#loop through parameter file lines & construct parameter dictionary
	for line in txt:
	
		if not line.startswith('#'): #skip commented out lines
			
			item = line.strip(' \n').lower()
			map_list.append(item)
						 
	txt.close()
	
	return map_list


def find_tiles(search_path):
	tiles = glob.glob(search_path)
	return tiles

def main(maplist_path, scene_index, start_band, end_band, output_path):
	
	#get list of TSA tiles
	tiles = getTxt(maplist_path)
	if len(tiles) == 0:
		sys.exit("ERROR: No TSA files found from list file '" + maplist_path + "'")
		
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