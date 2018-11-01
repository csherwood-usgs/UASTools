
# GPS_list_from_DJI.py
# Read all of the files in a directory with DJI Phantom 3 or 4 Images
# and generate a .csv file with name, lat, lon, altitude
#
# Usage:
# > activate IOOS3 (or other conda environment with sys, os, numpy, and pillow)
# (IOOS3) > python GPS_list_from_DJI.py target_directory
#
# A file called image_locations.csv will be created (or clobbered) in this directory
#
# csherwood@usgs.gov
#
# Part of this was adapted from https://www.codingforentrepreneurs.com/blog/extract-gps-exif-images-python/
# Thanks to the DJI Mavic forum for pointing out that this metadata is in the XMP segment of the image

import sys
import os
import numpy as np

# EXIF Reader
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def latlon_from_gps_data(gps_data):
    lat = np.nan
    lon = np.nan
    alt = np.nan
    try:
        v = gps_data['GPSLatitude']
        lat = float(v[0][0])/float(v[0][1])+        (1./60.)*float(v[1][0])/float(v[1][1])+        (1./3600.)*float(v[2][0])/float(v[2][1])
        if gps_data['GPSLatitudeRef']=='S':
            lat = -1.*lat

        v = gps_data['GPSLongitude']
        lon = float(v[0][0])/float(v[0][1])+        (1./60.)*float(v[1][0])/float(v[1][1])+        (1./3600.)*float(v[2][0])/float(v[2][1])
        if gps_data['GPSLongitudeRef']=='W':
            lon = -1.*lon
        try:
            v = gps_data['GPSAltitude']
            alt = float(v[0])/float(v[1])
        except:
            alt=np.nan

        return lat, lon, alt

    except:
        return np.nan, np.nan, np.nan

def get_gps_data(i):
    info = i._getexif()
    exif_data={}
    lat = np.nan
    lon = np.nan
    alt = np.nan
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                gps_data[sub_decoded] = value[t]

            lat,lon,alt=latlon_from_gps_data(gps_data)

    return lat,lon,alt

def get_dji_meta( filepath ):
    """
    Returns a dict with DJI-specific metadata stored in the XMB portion of the image
    """

    # list of metadata tags
    djimeta=["AbsoluteAltitude","RelativeAltitude","GimbalRollDegree","GimbalYawDegree",\
         "GimbalPitchDegree","FlightRollDegree","FlightYawDegree","FlightPitchDegree"]

    # read file in binary format and look for XMP metadata portion
    fd = open(filepath,'rb')
    d= fd.read()
    xmp_start = d.find(b'<x:xmpmeta')
    xmp_end = d.find(b'</x:xmpmeta')

    # convert bytes to string
    xmp_b = d[xmp_start:xmp_end+12]
    xmp_str = xmp_b.decode()

    fd.close()

    # parse the XMP string to grab the values
    xmp_dict={}
    for m in djimeta:
        istart = xmp_str.find(m)
        ss=xmp_str[istart:istart+len(m)+10]
        val = float(ss.split('"')[1])
        xmp_dict.update({m : val})

    return xmp_dict

def main():
    fcount = 0
    xcount = 0
    mcount = 0
    print(sys.argv[0])
    argc = len(sys.argv)
    if argc<2:
        print("Need a target directory as a command-line argument.")
        sys.exit(1)
    if argc>2:
        print("Dont understand more than one command-line argument.")
        sys.exit(1)
    path = sys.argv[1]
    print("Looking in: "+path)
    files = [f for f in os.listdir(path) if ( f.endswith('.jpg') or f.endswith('.JPG'))]
    if not files:
        print("No jpg files found.")
        sys.exit(1)

    outfile = 'image_locations.csv'
    outpath = os.path.join(path,outfile)
    try:
        fout = open(outpath, 'w')
    except:
        print("Could not open "+outpath)
        sys.exit(1)

    files = [f for f in os.listdir(path) if ( f.endswith('.jpg') or f.endswith('.JPG'))]
    print(os.path.join(path,files[0]))
    for file in files:
        fcount = fcount+1
        fpath = os.path.join(path,file)
        altr = np.NaN
        try:
            xmp_dict = get_dji_meta( fpath )
            altr = xmp_dict['RelativeAltitude']
            xcount = xcount+1
        except:
            print('No XMP metadata from', fpath )

        i = Image.open(fpath)
        # check to make sure the file opened as an image
        if i:
            # check to make sure there is EXIF info
            try:
                info = i._getexif()
                lat,lon,alt = get_gps_data(i)
                fout.write('{0},{1:.8f},{2:.8f},{3:.1f}\n'.format(file,lat,lon,altr))
                print('{0},{1:.8f},{2:.8f},{3:.1f},{4:.1f}'.format(file,lat,lon,alt,altr))
                mcount = mcount+1
            except:
                print('Could not find EXIF data in ',fpath)

            i.close()
        else:
            print('Could not open ',fpath)

    fout.close()
    print("File count:",fcount," with XMP data: ",xcount," with lat/lon data:",mcount)

if __name__ == "__main__":
    main()
