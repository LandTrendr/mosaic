# mosaic
Scripts to mosaic LandTrendr output maps.

Dependency: LandTrendr ltutilites - https://github.com/LandTrendr/ltutilities

####*mosaicDisturbanceMaps_nobuffer.py*

LandTrendr outputs have a 10km buffer around scene borders. In order to guarantee buffers are not included in mosaics, this script first masks LandTrendr outputs with Landsat TSA masks, and then mosaics the masked outputs using the gdalbuildvrt command line utility. Landsat TSA masks can be downloaded from LandTrendr's ftp site: ftp://islay.coas.oregonstate.edu/us_contiguous_tsa_masks_nobuffer.zip

This script first scours through LandTrendr's server file system to create a list of band sequential rasters to mosaic. Functions to do this may need to be altered for compatibility with another file system.

To run:

1. Create a parameter file. An example file is included in this repo.

2. Run *"python mosaicDisturbanceMaps_nobuffer.py [path_to_parameter_file]"*








