#################################################################
#
#
#             Mosaic Script
#
#             Inputs: Raster Images
#             Output: Raster Mosaic
#
#             Author: Jamie Perkins
#             Email: jperkins@bu.edu
#
#
#
#################################################################

import sys, os, glob
from osgeo import ogr, gdal, gdalconst
from gdalconst import *
import numpy as np
from tempfile import mkstemp


def readparams(path):

    params = open(path, 'r')

    #skip first line
    next(params)

    sceneDict = {}

    mask = None
    region = None
    type = ''

    for line in params:

        info = line.split(':')
        title = info[0].strip(' \n').lower()
        item = info[1].strip(' \n')
        #import pdb; pdb.set_trace()
        if title == 'name':
            name = item
        elif title == 'region':
            region = item
	elif title == 'mask':
	    mask = item
        elif title == 'type':
            type = ' -ot {0}'.format(item)
        else:
            sceneDict[title] = item

    params.close()

    return sceneDict, name, region, mask, type

def getArrayParams(images):

    #Store all corners in Lists
    ulxList = []
    ulyList = []
    lrxList = []
    lryList = []

    firstrun = True
    for item in images:

        sample = gdal.Open(item, GA_ReadOnly)
        sample_gt = sample.GetGeoTransform()

        if firstrun == True:
            Xdist = sample_gt[1]
            Ydist = sample_gt[5]
            driver = sample.GetDriver()
            projection = sample.GetProjection()
            transform = sample_gt
            firstrun = False

        #Get Corner Geo Information
        Xsize = sample.RasterXSize
        Ysize = sample.RasterYSize
        ulx = sample_gt[0]
        uly = sample_gt[3]
        lrx = ulx+Xsize*sample_gt[1]
        lry = uly+Ysize*sample_gt[5]

        #store in Lists
        ulxList.append(ulx)
        ulyList.append(uly)
        lrxList.append(lrx)
        lryList.append(lry)

        sample = None

    #Get Coordinates
    masterUlx = min(ulxList)
    masterUly = min(ulyList)
    masterLrx = max(lrxList)
    masterLry = max(lryList)

    #Get XY Size
    masterXsize = (masterLrx-masterUlx)/Xdist
    masterYsize = (masterLry-masterUly)/Ydist

    #store master params in dict
    masterParams = {

        'masterXsize': masterXsize,
        'masterYsize': masterYsize,
        'ulx': masterUlx,
        'uly': masterUly,
        'lrx': masterLrx,
        'lry': masterLry,
        'driver': driver,
        'projection': projection,
        'transform': transform

    }


    return masterParams

def getOffset(smaller, larger):

    error = False

    #get smaller image corners
    sgt = smaller.GetGeoTransform()
    sulx = sgt[0]
    suly = sgt[3]
    slrx = sulx+smaller.RasterXSize*sgt[1]
    slry = suly+smaller.RasterYSize*sgt[5]

    #get larger image corners
    lgt = larger.GetGeoTransform()
    lulx = lgt[0]
    luly = lgt[3]
    llrx = lulx+larger.RasterXSize*lgt[1]
    llry = luly+larger.RasterYSize*lgt[5]


    #determine offset
    diffx = (sulx - lulx)/lgt[1]
    if diffx < 0:
        raise NotImplementedError('Image ULX is within study area mask')

    #determine offset
    diffy = (suly - luly)/lgt[5]
    if diffy < 0:
        raise NotImplementedError('Image ULY is within study area mask')

    #Round diff values to integer values
    diffx = int(round(diffx))
    diffy = int(round(diffy))

    #check to make sure the lower right is not going to be offensive
    lorXoffset = diffx + smaller.RasterXSize
    lorYoffset = diffy + smaller.RasterYSize

    if lorXoffset > larger.RasterXSize:
        print 'Image LORX is not large enough to accomodate study area'
	error = True

    if lorXoffset > larger.RasterYSize:
        print 'Image LORY is not large enough to accomodate study area'
	error = True

    print diffx, diffy
    return diffx, diffy, error


def writefile(Array, filename, bnd, allbands, basefile):

    #create file on first pass
    if bnd == 1:
        driver = basefile.GetDriver()
        tmpbsq = driver.Create(filename, basefile.RasterXSize, basefile.RasterYSize, allbands, gdalconst.GDT_Int16)
        tmpbsq.SetGeoTransform(basefile.GetGeoTransform())
        tmpbsq.SetProjection(basefile.GetProjection())
    else:
        tmpbsq = gdal.Open(filename, GA_Update)

    tmpbsq.GetRasterBand(bnd).WriteArray(Array)

    #close file
    tmpbsq = None



def mktmps(imageSet, TSAfile, temp):

    TSA = gdal.Open(TSAfile, GA_ReadOnly)

    #iterate over each image to be mosaic'd
    for scene, path in imageSet.iteritems():
        
        filename = os.path.basename(path)
        print 'Working on {0}'.format(filename)

        raster = gdal.Open(path, GA_ReadOnly)
        
        tmpname = '{0}_tmp.bsq'.format(scene)
                
        diffx, diffy, er = getOffset(raster, TSA)
	if er == True:
            continue
        
        #pull out resized TSA file
        TSAarray = TSA.GetRasterBand(1).ReadAsArray(diffx, diffy, raster.RasterXSize, raster.RasterYSize)
        
        #Get Band Count
        bands = raster.RasterCount
        for band in range(bands):
            bandnum = band + 1
            
            print '\tWriting Band {0}'.format(bandnum)
            #Get Raster Array
            RasterArray = raster.GetRasterBand(bandnum).ReadAsArray()

            #define value held by TSA
            value = int(scene)

            #create new array with proper boundaries
            sizedArray = np.where(TSAarray == value, RasterArray, 0)

            tmpfile = os.path.join(temp, tmpname)
            writefile(sizedArray, tmpfile, bandnum, bands, raster)

        raster = None
    TSA = None



def main():

    #make this into dict read from file
    assert os.path.exists(sys.argv[1]), 'No Params File!'
    paramsPath = sys.argv[1]
    imageDict, outname, area, zone, btype = readparams(paramsPath)
    tmpdir = '/projectnb/trenders/proj/jamie_utils/py_scripts/aggregation/tmp'
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    TSARaster = '/projectnb/trenders/proj/jamie_utils/shapefiles/TSA_Raster/TSA_Raster.bsq'
    if not area == None:
        outpath = os.path.join('/projectnb/trenders/proj/jamie_utils/py_scripts/aggregation', area)
    else:
        outpath = '/projectnb/trenders/proj/jamie_utils/py_scripts/mosaic_script'
    if not os.path.exists(outpath):
        #print outpath
	#import pdb; pdb.set_trace()
        os.makedirs(outpath)
    outfile = '{0}.bsq'.format(outname)
    print 'Writing Mosaic: {0}'.format(outfile)
    print 'Region: {0}'.format(area)
    if not btype == '':
        print 'Data Type: {0}'.format(btype.strip())
    outfilepath = os.path.join(outpath, outfile)
    #zone not used right now
    if zone:
    	paramDict = getArrayParams(zone)

    mktmps(imageDict, TSARaster, tmpdir)

    mergeList = glob.glob(os.path.join(tmpdir, '*.bsq'))

    print '\nMerging Images'
    
    os.system('gdal_merge.py -o {0} -of ENVI -n 0{1} {2}'.format(outfilepath, btype, ' '.join(mergeList)))

    print 'Removing Temporary Files'

    for item in mergeList:
        base = item.replace('bsq', '*')
        basefiles = glob.glob(base)
	for thing in basefiles:
            os.remove(thing)
    print 'Written {0}'.format(outfilepath) 
    print 'Done'


if __name__ == '__main__':
    sys.exit(main())
