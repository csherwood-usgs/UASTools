
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
        print("No GPS info in ",imgpath)
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
    # But the Ricohs don't have it, and it is not needed.
    # val = exif_data['ShutterSpeedValue']
    # fval = float(val[0])/float(val[1])
    # mdict.update( {'ShutterSpeedValue' : fval } )

    val = exif_data['DateTime']
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

    # initialize counters
    fcount = 0
    xcount = 0
    mcount = 0
    ecount = 0
    # initialize data lists and arrays
    fpath_l = []
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

    files = [f for f in os.listdir(path) if ( f.endswith('.jpg') or f.endswith('.JPG'))]
    for file in files:
        fcount = fcount+1
        fpath = os.path.join(path,file)
        fpath_l.append( fpath )
        # check to make sure there is EXIF info
        try:
            mdict = get_camera_settings(fpath)
            try:
                dt_l.append( mdict['datetime'] )
                date_l.append( mdict['Date'] )
                time_l.append( mdict['Time'] )
            except:
                dt_l.append("")
                date_l.append("")
                time_l.append("")
                print("No date or time in:",fpath)

            try:
                iso_l.append( mdict['ISOSpeedRatings'] )
                fstop_l.append( mdict['FNumber'] )
                exptime_l.append( mdict['ExposureTime'])
                ecount = ecount+1
            except:
                iso_l.append(np.NaN)
                fstop_l.append(np.NaN)
                exptime_l.append(np.NaN)
                print('Missing camera metadata in:',fpath)

        except:
            dt_l.append("")
            date_l.append("")
            time_l.append("")
            iso_l.append(np.NaN)
            fstop_l.append(np.NaN)
            exptime_l.append(np.NaN)
            print("No EXIF data in ",fpath)

        # look for XMP metadata (DJI images)
        altr = np.NaN
        try:
            xmp_dict = get_dji_meta( fpath )
            altr = xmp_dict['RelativeAltitude']
            altr_l.append( altr )
            xcount = xcount+1
        except:
            altr_l.append(np.NaN)
            print('Missing XMP metadata in:', fpath )

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
                print('Missing GPS data in:',fpath)

            i.close()
        else:
            print('Could not open: ',fpath)

    # Summary statistics
    dt_a = np.array( dt_l )
    lat_a = np.array(lat_l)
    lon_a = np.array(lon_l)
    altr_a = np.array(altr_l)
    alta_a = np.array(alta_l)
    iso_a = np.array(iso_l)
    fstop_a = np.array(fstop_l)
    exptime_a = np.array(exptime_l)

    # Best altitude: use relative altitude if available, otherwise absolute altitude
    altb_a = np.NaN*np.ones_like(alta_a)
    for i in range( len(alta_a) ):
        altb_a[i]=altr_a[i]
        if(np.isnan(altr_a[i])):
            altb_a[i]=alta_a[i]

    # Calculate exposure value. See https://en.wikipedia.org/wiki/Exposure_value
    ev_a = np.log2( fstop_a**2 / exptime_a + np.log2( iso_a / 100.))

    # Write out csv of file info
    outfile = 'image_info.csv'
    outpath = os.path.join(path,outfile)
    try:
        fout = open(outpath, 'w')
    except:
        print("Could not open "+outpath)
        sys.exit(1)

    fout.write("path,latitude (degrees N),longitude (degrees E),altitude (m),ISO,Fstop,1/exposure time (s),exposure value\n")
    for i, p, in enumerate( fpath_l ):
        # print('{0:},{1:.6f},{2:.6f},{3:.1f},{4:.0f},{5:.1f},{6:.1f},{7:.1f}'.\
        #     format(p,lat_a[i],lon_a[i],altb_a[i],iso_a[i],fstop_a[i],1./exptime_a[i],ev_a[i]))
        fout.write("{0:},{1:.6f},{2:.6f},{3:.1f},{4:.0f},{5:.1f},{6:.1f},{7:.1f}\n".\
            format(p,lat_a[i],lon_a[i],altb_a[i],iso_a[i],fstop_a[i],1./exptime_a[i],ev_a[i]))
    fout.close()

    print("\n\n**********************************************************************************")
    print("EXIF_from_images.py run {}.".format( datetime.now().strftime('%Y:%m:%d %H:%M:%S')))
    print("\nPath: ",path)
    print("File count:",fcount," total, ",xcount," with XMP, ",mcount," with lat/lon, and ",ecount," with camera EXIF.")
    print("\nEarliest: ",min(dt_l).strftime('%Y:%m:%d %H:%M:%S'))
    print("  Latest: ",max(dt_l).strftime('%Y:%m:%d %H:%M:%S'))
    print("\n   North:  {0:.5f} South:  {1:.5f}".format(np.nanmax(lat_a),np.nanmin(lat_a)))
    print("    West: {0:.5f}  East: {1:.5f}".format(np.nanmin(lon_a),np.nanmax(lon_a)))
    print("\nAbsolute Altitude Min: {0:5.1f} Max: {1:5.1f} Median: {2:5.1f} m"\
        .format(np.nanmin(alta_a),np.nanmax(alta_a),np.nanmedian(alta_a)))
    print("Relative Altitude Min: {0:5.1f} Max: {1:5.1f} Median: {2:5.1f} m"\
        .format(np.nanmin(altr_a),np.nanmax(altr_a),np.nanmedian(altr_a)))
    print("\n    ISO:   Min:  {0:5.0f} Max:  {1:5.0f} Median:  {2:5.0f}"\
        .format(np.nanmin(iso_a),np.nanmax(iso_a),np.nanmedian(iso_a)))
    print(" F-stop:   Min:  {0:5.1f} Max:  {1:5.1f} Median:  {2:5.1f}"\
        .format(np.nanmin(fstop_a),np.nanmax(fstop_a),np.nanmedian(fstop_a)))
    print("Shutter:   Min:  {0:5.0f} Max:  {1:5.0f} Median:  {2:5.0f}"\
        .format(1./np.nanmin(exptime_a),1./np.nanmax(exptime_a),1./np.nanmedian(exptime_a)))
    print("     EV:   Min:  {0:5.1f} Max:  {1:5.1f} Median:  {2:5.1f}"\
        .format(np.nanmin(ev_a), np.nanmax(ev_a), np.nanmedian(ev_a)))
    print("\n.csv list is in",outpath)
    print("**********************************************************************************")


if __name__ == "__main__":
    main()
