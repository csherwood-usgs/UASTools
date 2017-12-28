
# GPS_list_from_EXIF.py
# Read all of the files in a directory and generate a .csv file with name, lat, lon, altitude
#
# Usage:
# > activate IOOS3 (or other conda environment with sys, os, numpy, and pillow)
# > python GPS_list_from_EXIF.py
# csherwood@usgs.gov
#
# Part of this was adapted from https://www.codingforentrepreneurs.com/blog/extract-gps-exif-images-python/

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

def main():
    print('GPS_list_from_EXIF.py')
    path=input("Enter the target directory: ")
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
        fpath = os.path.join(path,file)
        i = Image.open(fpath)
        # check to make sure the file opened as an image
        if i:
            # check to make sure there is EXIF info
            try:
                info = i._getexif()
                lat,lon,alt = get_gps_data(i)
                fout.write('{0},{1:.8f},{2:.8f},{3:.3f}\n'.format(file,lat,lon,alt))
                print('{0},{1:.8f},{2:.8f},{3:.3f}'.format(file,lat,lon,alt))
            except:
                print('Could not find EXIF data in ',fpath)

        else:
            print('Could not open ',fpath)

    fout.close()

if __name__ == "__main__":
    main()
