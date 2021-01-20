from raycast import *
import urllib.request, urllib.error
import os, json, csv, sys
import numpy as np
import argparse
import requests
import math
import imghdr
from pathlib import Path
from io import StringIO
maptype = "satellite"
size = "400x400"
zoom = "15"
fileformat = "png"
city = 'colombia'
datadir = '../data'
outdir = '../out'
imgdir = '../out/colombia/'

# Use your Google Static Maps API key
key = "AIzaSyCaE-7H7K4QZdO8KWgcKGFd12y2nZhDe7g"
cdn = [1,2,3,4]
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0'#,
    #'From': 'youremail@domain.com'  # This is another valid field
}
# Parse the shapefiles to find census tract boundaries and map it to a square grid
accessKey = "1606007831_2776494910341617389_%2F_jvWKZwJ9mrtn1cYhAvGt7FYMbL4e5ayOgMlvnCpWlNM%3D"

# to extract latitude-longitude pairs for download locations.
def getDownloadLocs(boundary_locs):
    p = Polygon([Point(l2, l1) for l1, l2 in boundary_locs])
    lats = [pair[1] for pair in boundary_locs]
    lons = [pair[0] for pair in boundary_locs]
    latMin = min(lats)
    latMax = max(lats)
    lonMin = min(lons)
    lonMax = max(lons)
    print(latMin,latMax,lonMin,lonMax)
    download_locs = []
    for i in np.arange(latMin + 0.01, latMax, 0.013):
        for j in np.arange(lonMin + 0.01, lonMax, 0.013):
            if p.contains(Point(i, j)):
                download_locs.append((i, j))

    if len(download_locs) == 0:
        download_locs.append(((latMin + latMax) / 2, (lonMin + lonMax) / 2))
    return download_locs


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def make_url(lat_deg, lon_deg, access_Key, zoom=15):
    # returns the list of urls when lat, lon, zoom and accessKey is provided
    x_tyle, y_tyle = deg2num(lat_deg, lon_deg, zoom)
    get_url = []
    get_url.append(str(
        "https://sat-cdn2.apple-mapkit.com/tile?style=7&size=2&scale=1&z=15&x=" + str(
            x_tyle) + "&y=" + str(y_tyle) + "&v=7072&accessKey=" + str(access_Key)))
    for i in cdn:
        pass
    return get_url

def get_img( url_str):
    # to get the images from the url provided and save it
    global headers

    try:
        x_ = url_str.find('&x=')
        y_ = url_str.find('&y=')
        v_ = url_str.find('&v=')
        x_tyle = url_str[x_ + 3:y_]
        y_tyle = url_str[y_ + 3:v_]
        file_name = str(x_tyle) + "_" + str(y_tyle) + ".jpeg"
        r = requests.get(url_str,  # allow_redirects=True,
                         headers=headers)
        open(file_name, 'wb').write(r.content)
        if imghdr.what(file_name) is 'jpeg':
            print(file_name, "JPEG")
        else:
            os.remove(file_name)
            print(file_name, "NOT JPEG")
    except:
        print("Ops Blown Off!")

# Read obesity file from 500 cities project
def readObfile(obfile):

    tractids = []
    obvalues = {}
    with open(obfile, 'r') as f:
        obreader = csv.reader(f)
        header = next(obreader)
        for i in range(0, len(header)):
            if header[i] == 'TractFIPS':
                tractind = i
                continue
            if header[i] == 'GeographicLevel':
                levelind = i
                continue
            if header[i] == 'Data_Value':
                dataind = i
                continue
        for row in obreader:
            if row[levelind] != 'Census Tract':
                continue
            if row[dataind] == '':
                print(row)
                continue
            tractids.append(row[tractind])
            obvalues[row[tractind]] = row[dataind]
    print('Total number of census tracts in datafile: ', len(tractids))
    return tractids, obvalues

# Get download locations and write it to a csv file
def writeLocations(geojsonfile, state, municipal):

    with open(geojsonfile, 'r') as f:
        shapes = json.load(f)

    print('Number of census tracts in shape file = ' + str(len(shapes['features'])))

    count = 0
    filtered_shapes = []

    locs_by_tract = {}
    # boundary locations are in the counter clockwise direction
    found = False
    

    f =	 StringIO(municipal)	
    municipal_list = list(csv.reader(f, delimiter=','))
    print(municipal_list)
    for tract in shapes['features']:
        print('*', end = ', ')
        sys.stdout.flush()
        if tract["properties"]["DPTO_CNMBR"] == state:
            boundary_locs = tract['geometry']['coordinates'][0]
            blarray = np.array(boundary_locs)
            if blarray.ndim == 3:
                boundary_locs = tract['geometry']['coordinates'][0][0]

            print("municipal: " , tract["properties"]["MPIO_CNMBR"])
            if  tract["properties"]["MPIO_CNMBR"] not in municipal_list[0]:
                continue
    #     print(boundary_locs)
            boundary_locs.reverse()
            tractid = tract['properties']['DPTO_CNMBR'] + "_" + tract['properties']['MPIO_CNMBR'] + "_" + str(tract['properties']['MPIO_CCDGO'])
            locs = getDownloadLocs(boundary_locs)
            locs_by_tract[tractid] = locs

            #uncomment the break to run for all municipalities, currently it is not efficient for bigger polygons
    f = open(os.path.join(datadir, city, 'download_' + city + '_tract_18_imgs_locs.csv'), 'w')
    locwriter = csv.writer(f)
    loc_count = 0
    for tractid in list(locs_by_tract.keys()):
        for i in range(0, len(locs_by_tract[tractid])):
            lat, lon = locs_by_tract[tractid][i]
            loc = str(lat) + ',' + str(lon)
            parts = tractid.split("_")
            imgname = parts[0] + '/' + parts[1] + '/'+ parts[2] + '_' + str(i) + '.JPEG'
            infotext = [imgname, loc, tractid]
            loc_count += 1
            locwriter.writerow(infotext)
    f.close()

    print("Total number of download locations: ", loc_count)
    return

# Download images from Google Static Maps API
def downloadImages(locfile):

    f = open(locfile, 'r')
    locreader = csv.reader(f)
    download_count = 0
    zoom = '15'
    for row in locreader:

        download_count += 1
        loc = row[1]
        img_url = "https://maps.googleapis.com/maps/api/staticmap?" + \
                  "center=" + loc + "&" + \
                  "zoom=" + zoom + "&" + \
                  "maptype=" + maptype + "&" + \
                  "size=" + size + "&" + \
                  "format=" + fileformat + "&" + \
                  "key=" + key
        imgname = row[0]
        img_path = os.path.join(imgdir, imgname)
        img_full_path = os.path.dirname(os.path.abspath(img_path))
        if not os.path.exists(img_full_path):
        	os.makedirs(img_full_path,0o777,True)
        	os.chmod(img_full_path, 0o777)
        print(img_full_path)
        try:
            urllib.request.urlretrieve(img_url, img_path)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                print("Page not found!")
            elif err.code == 403:
                print("Access denied!")
            else:
                print("Something happened! Error code", err.code)
            print(img_url)
            break
        except urllib.error.URLError as err:
            print("Some other error happened:", err.reason)
            print(img_url)
            break
        print(download_count, end=' ')
        sys.stdout.flush()

    f.close()
# Download images from Google Static Maps API
def downloadAppImages(locfile):

    f = open(locfile, 'r')
    locreader = csv.reader(f)
    download_count = 0

    for row in locreader:

        download_count += 1
        loc = row[1]

        imgname = row[0]
        img_path = os.path.join(imgdir, imgname)
        img_full_path = os.path.dirname(os.path.abspath(img_path))

        if not os.path.exists(img_full_path):
        	os.makedirs(img_full_path,0o777,True)
        	os.chmod(img_full_path, 0o777)
        #print(img_full_path)
        global headers
        locs = loc.split(',')
        url_str = make_url(round(float(locs[0]),4),round(float(locs[1]),4),accessKey)
        #print(url_str)
        try:

            r = requests.get(url_str[0],  # allow_redirects=True,
                             headers=headers)
            open(img_path, 'wb').write(r.content)

        except Exception as e:
            print(e)
            break

        sys.stdout.flush()

    f.close()

if __name__ == "__main__":
    #a = api(
    #    accessKey, 6.1638, 6.3737, -75.7192, -75.4723)

    parser = argparse.ArgumentParser( description=('program to download satellite imagery based on geojson and municipal'))
    parser.add_argument('--geo_json_file', help=('geo json file path for columbia municipalities'))
    parser.add_argument('--state', help='')
    parser.add_argument('--municipal', help='')
    args = parser.parse_args()
    if len(key) == 0:
        print("error: please set google provide key");
    else:
        if (not args.municipal) or (not args.geo_json_file):
            print("error: usage  python3 download_img.py --geo_json_file <file_path> --state <state> --municipal <NAME_2 in json> ")
        else:
            writeLocations(args.geo_json_file,args.state,args.municipal)
            locfile = os.path.join(datadir, city, 'download_' + city + '_tract_18_imgs_locs.csv')
            downloadAppImages(locfile)
