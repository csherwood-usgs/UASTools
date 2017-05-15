#!/usr/local/bin/python

### EXIF COORDINATE TRANSFORM SCRIPT ###

# Raptor Maps Inc. (c) 2016
# Eddie Obropta - eddie@raptormaps.com

# This script takes a directory that contains images with EXIF data.
# The EXIF data is converted from its coordinate system to a destination
# coordinate system. The flight path state is created in a numpy array
# state = [x y z t],
# note: x,y,z units are dependend on destination coordinatre system
# t is in seconds

# note: this script has only been tested with Raptor Maps systems.
# All edge cases have not been tested. Assumptions are made about
# the EXIF format from Raptor Maps camera systems. Time is in seconds
# relative to the day. Odd things could happen if flight times go across
# time zones or across days. Use caution.
# Source coordinate system is almost always WGS 84 - EPSG:4326

# example script execution:
# reads EXIF data in /path/to/image/directory/ as WGS 84 (EPSG:4326) and converts to NAD83 UTM zone 19N (EPSG:26919)
#
# $ python exifCoordinatesTransform.py /path/to/image/directory/ -src EPSG:4326 -dst EPSG:26919
#
### ------------------------------- ###


import __future__
import sys
# argument parsing
import argparse
# glob for files
import glob
# file path tools
from os.path import join, basename
# regular expression
import re
# math library
import math
# Numpy
import numpy as np

# GDAL Python library
from osgeo import osr
# EXIF Reader
import exifread


""" Argument Parser """
parser = argparse.ArgumentParser(description='Read flight images and transform coordinate system')

# inputPath - location of files
parser.add_argument('inputPath',type=str,help='path to the directory containing the images')
# Source coordinate reference system, for example to use WGS 84 lat lng use "EPSG:4326"
parser.add_argument('-src',type=str,help='source coordinate reference system i.e "EPSG:4326"')
# Destination coordinate reference system, for example to use NAD83 / UTM zone 19N "EPSG:26919"
parser.add_argument('-dst',type=str,help='destination coordinate reference system i.e "EPSG:26919"')
# fileType: default is JPG and is case sensitive
parser.add_argument('--fileType', nargs='?', default='JPG', type=str, help='filetype of images to list the default is JPG - note: case sensitive')

# get arguments
args = parser.parse_args()

# get input arguments
mydir = args.inputPath
src_crs = args.src
dst_crs = args.dst
filetype = args.fileType

# construct filepath
filepath = join(mydir,'*.'+filetype)

# source coordinate system
srs_cs = osr.SpatialReference()
srs_cs.SetFromUserInput(src_crs)

# destination coordinate system
dst_cs = osr.SpatialReference()
dst_cs.SetFromUserInput(dst_crs)

# osr image transformation object
transform = osr.CoordinateTransformation(srs_cs, dst_cs)

# print coordinate system information
print " >> SOURCE COORDINATE REFERENCE SYSTEM: "
print srs_cs

print " >> DESTINATION COORDINATE REFERENCE SYSTEM: "
print dst_cs


""" MAIN """
def main():
    print " >> Read image files from ",filepath
    files = getGPSFiles(filepath)
    print " >> Transform coordinate system"
    x = transformCoordinateSystem(files)
    print " >> Flight path [x, y, z, t]"
    print x


""" Read GPS Files """
# return list of files with GPS data and print file stats
def getGPSFiles(filepath):
    files_gps = []
    files = sorted(glob.glob(filepath))
    n_images = len(files)
    n_images_GPS = 0
    for file in files:
        fs = open(file,'rb')

        # intialize arrays
        lat = []
        lon = []
        latref = []
        lonref = []
        alt = []
        time = []

        # attempt to read files
        try:
            tags = exifread.process_file(fs)
        except:
            print "No EXIF Data"
        try:  
            lon = tags['GPS GPSLongitude']
            lat = tags['GPS GPSLatitude']
            latref = tags['GPS GPSLatitudeRef']
            lonref = tags['GPS GPSLongitudeRef']
            alt = tags['GPS GPSAltitude']
            files_gps.append(file)
            n_images_GPS += 1
        except KeyError:
            print "No GPS Data for this image"

        # Get time information primarily from GPSTimeStamp
        try:
            time = tags['GPS GPSTimeStamp']
        except KeyError:
            time = tags['EXIF DateTimeOriginal']
            print "No GPS Time Stamp for this image"
            
    # raise warning if no images have GPS data
    if n_images_GPS == 0:
        raise UserWarning('No images with GPS')
    else:
        print "Images with GPS: %d out of %d - %.2f%%" % (n_images_GPS, n_images, 100*n_images_GPS/n_images)
    
    return files_gps

""" Transform Coordinate System """
# return numpy array of flight path state [x y z t] in transformed coordinates
def transformCoordinateSystem(files):

    # initialize arrays
    flight_path_x = []
    flight_path_y = []
    flight_path_z = []
    flight_path_t = []

    # loop over files that have GPS data
    for file in files:
        fs = open(file,'rb')
        tags = exifread.process_file(fs)
        lon = tags['GPS GPSLongitude']
        lat = tags['GPS GPSLatitude']
        latref = tags['GPS GPSLatitudeRef']
        lonref = tags['GPS GPSLongitudeRef']
        alt = tags['GPS GPSAltitude']
        # handle time reading
        try:
            time = tags['GPS GPSTimeStamp']
            time_num = eval(str(time));
        except:
            time = tags['EXIF DateTimeOriginal']
            time_split = str(time).split()
            time  = time_split[1].split(':')
            time_num = [float(i) for i in time]
                        
        alt_num = eval(str(alt))

        # convert time to seconds
        time_dec = (time_num[0]+time_num[1]/60.0 + time_num[2]/3600.0)*3600 # seconds

        ## Latitude
        # use regular expression to get value between brackets
        y_regx = re.search('\[(.*?)\]', str(lat))
        y_regx = y_regx.group(1)
        y_regx = y_regx.split(', ')
        # properly convert values to floats
        y = []
        y.append(eval(compile(y_regx[0],'<string>','eval', __future__.division.compiler_flag)))
        y.append(eval(compile(y_regx[1],'<string>','eval', __future__.division.compiler_flag)))
        y.append(eval(compile(y_regx[2],'<string>','eval', __future__.division.compiler_flag)))

        ## Longitude
        x_regx = re.search('\[(.*?)\]', str(lon))
        x_regx = x_regx.group(1)
        x_regx = x_regx.split(', ')
        x = []
        x.append(eval(compile(x_regx[0],'<string>','eval', __future__.division.compiler_flag)))
        x.append(eval(compile(x_regx[1],'<string>','eval', __future__.division.compiler_flag)))
        x.append(eval(compile(x_regx[2],'<string>','eval', __future__.division.compiler_flag)))
        
        # convert from latitude longitude minutes seconds to decimal
        ddx = (np.sign(x[0]))*(math.fabs(x[0]) + (x[1]/60.0) + (x[2]/3600.0))
        ddy = (np.sign(y[0]))*(math.fabs(y[0]) + (y[1]/60.0) + (y[2]/3600.0))

        # handle longitude west values to negative
        if str(lonref) == 'W':
            ddx = -1.0*ddx
        # handle latitude south values to negative
        if str(latref) == 'S':
            ddy = -1.0*ddy
            
        # get the coordinates in lat long
        # TransformPoint(X,Y) i.e. -> (long, lat)
        u = transform.TransformPoint(ddx, ddy)

        # append numpy arrays
        flight_path_x.append(u[0])
        flight_path_y.append(u[1])
        flight_path_z.append(alt_num)
        flight_path_t.append(time_dec)

        # close connection to file
        fs.close()

    # build flight path matrix
    flight_path = np.array([flight_path_x, flight_path_y, flight_path_z, flight_path_t])
    return flight_path

""" Execute main """
main()
