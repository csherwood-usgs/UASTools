
# EXIF_from_images.py
# Read all of the UAS image files in a directory.
# Generate a .csv file with name, time, lat, lon, (relative) altitude,
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
from datetime import datetime

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

def get_exif_data(imgpath):
    """
    Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags
    https://www.codingforentrepreneurs.com/blog/extract-gps-exif-images-python/
    """
    exif_data = {}
    print("Trying to open ",imgpath)
    try:
        image=Image.open(imgpath)
    except:
        print("Failed to open ",imgpath)

    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    else:
        print("No info in ",imgpath)
    image.close()
    return exif_data

def get_camera_settings(impath):
    """
    Decode some standard camera info from the EXIF portion of the images
    """
    exif_data = get_exif_data(impath)
    mdict = {}
    mdict.update( {'ISOSpeedRatings' : float( exif_data['ISOSpeedRatings'])} )
    val = exif_data['ExposureTime']
    fval = float(val[0])/float(val[1])
    mdict.update( {'ExposureTime' : fval } )

    val = exif_data['FNumber']
    fval = float(val[0])/float(val[1])
    mdict.update( {'FNumber' : fval } )

    # According to https://www.dpreview.com/forums/post/54376235
    # ShutterSpeedValue is defined as an APEX (Additive System of Photographic Exposure) value, where:
    # ShutterSpeed=-log2(ExposureTime).
    val = exif_data['ShutterSpeedValue']
    fval = float(val[0])/float(val[1])
    mdict.update( {'ShutterSpeedValue' : fval } )

    val = exif_data['DateTime']
    print(val)
    dt = datetime.strptime(val,'%Y:%m:%d %H:%M:%S')
    mdict.update( {'datetime' : dt } )

    date, time = val.split(' ')
    mdict.update( {'Date' : date } )
    mdict.update( {'Time' : time } )

    return mdict

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

    # initialize counters
    fcount = 0
    xcount = 0
    mcount = 0
    ecount = 0
    # initialize data lists and arrays
    dt_l = []
    date_l = []
    time_l = []
    lat_l = []
    lon_l = []
    alta_l = []
    altr_l = []
    fstop_l = []
    exptime_l = []
    iso_l = []
    shutterspd_l = []

    files = [f for f in os.listdir(path) if ( f.endswith('.jpg') or f.endswith('.JPG'))]
    print(os.path.join(path,files[0]))
    for file in files:
        fcount = fcount+1
        fpath = os.path.join(path,file)

        # check to make sure there is EXIF info
        try:
            mdict = get_camera_settings(fpath)
            print(mdict)
            dt_l.append( mdict['datetime'] )
            date_l.append( mdict['Date'] )
            time_l.append( mdict['Time'] )
            fstop_l.append( mdict['FNumber'] )
            exptime_l.append( mdict['ExposureTime'])
            shutterspd_l.append( mdict['ShutterSpeedValue'])
            ecount = ecount+1
        except:
            print('No camera metadata in:',fpath)

        # look for XMP metadata (DJI images)
        altr = np.NaN
        try:
            xmp_dict = get_dji_meta( fpath )
            altr = xmp_dict['RelativeAltitude']
            print("Altr:",altr)
            altr_l.append( altr )
            xcount = xcount+1
        except:
            altr_l.append(np.NaN)
            print('No XMP metadata from:', fpath )

        # get lat/lon
        i = Image.open(fpath)
        # check to make sure the file opened as an image
        if i:
            try:
                info = i._getexif()
                lat,lon,alta = get_gps_data(i)
                lat_l.append( lat )
                lon_l.append( lon )
                alta_l.append( alta )
                mcount = mcount+1
            except:
                lat_l.append( np.NaN )
                lon_l.append( np.NaN )
                alta_l.append( np.NaN )
                print('Could not find GPS data in:',fpath)

            i.close()
        else:
            print('Could not open ',fpath)

    #fout.write('{0},{1:.8f},{2:.8f},{3:.1f}\n'.format(file,lat,lon,altr))
    #print('{0},{1:.8f},{2:.8f},{3:.1f},{4:.1f}'.format(file,lat,lon,alt,altr))

    fout.close()
    print("File count:",fcount," with XMP data: ",xcount," with lat/lon data:",mcount,'with EXIF metadata: ',ecount)

if __name__ == "__main__":
    main()
