import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image, ExifTags
from datetime import datetime
import pandas as pd
from lxml import etree

namespace = {'def': 'http://www.topografix.com/GPX/1/1'}

%matplotlib inline
%config InlineBackend.figure_format = 'svg'
t = np.linspace(0, 20, 500)

plt.plot(t, np.sin(t))
plt.show()

# get list of .gpx files
path = '.'
glist=[os.path.join(path,g) for g in os.listdir(path) if ( g.endswith('.gpx') or g.endswith('.GPX'))]
print glist
tree = etree.parse(glist[0])
# how many tracks in this file (none)?
# trks = tree.findall("{%s}trk" % namespace)
# print(trks)

# This works
elist = tree.xpath('./def:trk//def:trkpt',namespaces=namespace)
lonlat = [e.values() for e in elist]
lonlat = np.array(lonlat,dtype="float")
print(lonlat[0])
print(elist[5].find('ele').text)
print(np.shape(elist))

# This works
elist = tree.xpath('./def:trk//def:trkpt//def:time',namespaces=namespace)
fmt = '%Y-%m-%dT%H:%M:%S-04:00' #2017-05-04T14:14:12-04:00
time = [datetime.strptime(e.text, fmt) for e in elist]
print time[0], np.shape(time)
print(np.shape(elist))

# This works
elist = tree.xpath('./def:trk//def:trkpt//def:ele',namespaces=namespace)
ele = np.array([float(e.text) for e in elist])
print(ele[0], np.shape(ele))
print(np.shape(elist))

# This works
elist = tree.xpath('./def:trk//def:trkpt//def:ele2',namespaces=namespace)
ele2 = np.array([float(e.text) for e in elist])
print(ele2[0], np.shape(ele2))
print(np.shape(elist))

# get a list of images files
path = '.'
flist=[os.path.join(path,f) for f in os.listdir(path) if ( f.endswith('.jpg') or f.endswith('.JPG'))]

# print the time stamp
for f in flist:
    t=Image.open(f)._getexif()[36867]
    print(f,t)


# here is how to get all of the exif info:
# img = Image.open(flist[0])
# exif_data = img._getexif()
# exif = { ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS }
# print(exif)
