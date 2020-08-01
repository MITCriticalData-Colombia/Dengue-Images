from raycast import *
import urllib.request, urllib.error
import os, json, csv, sys
import numpy as np
import argparse
from pathlib import Path
maptype = "satellite"
size = "400x400"
zoom = "18"
fileformat = "png"
city = 'colombia'
datadir = '../data'
outdir = '../out'
imgdir = '../out/colombia/'

# Use your Google Static Maps API key
key = ""

# Parse the shapefiles to find census tract boundaries and map it to a square grid
# to extract latitude-longitude pairs for download locations.
def getDownloadLocs(boundary_locs):
    p = Polygon([Point(l2, l1) for l1, l2 in boundary_locs])
    lats = [pair[1] for pair in boundary_locs]
    lons = [pair[0] for pair in boundary_locs]
    latMin = min(lats)
    latMax = max(lats)
    lonMin = min(lons)
    lonMax = max(lons)

    download_locs = []
    for i in np.arange(latMin + 0.01, latMax, 0.013):
        for j in np.arange(lonMin + 0.01, lonMax, 0.013):
            if p.contains(Point(i, j)):
                download_locs.append((i, j))

    if len(download_locs) == 0:
        download_locs.append(((latMin + latMax) / 2, (lonMin + lonMax) / 2))
    return download_locs

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
def writeLocations(geojsonfile, municipal):

    with open(geojsonfile, 'r') as f:
        shapes = json.load(f)

    print('Number of census tracts in shape file = ' + str(len(shapes['features'])))

    filtered_shapes = []
    count = 0

    locs_by_tract = {}
    # boundary locations are in the counter clockwise direction
    found = False
    for tract in shapes['features']:
        print('*', end = ', ')
        sys.stdout.flush()
        if tract["properties"]["NAME_2"] == municipal:
            boundary_locs = tract['geometry']['coordinates'][0]

            print("municipal: " , municipal, boundary_locs)
    #     print(boundary_locs)
            boundary_locs.reverse()
            tractid = tract['properties']['NAME_1'] + tract['properties']['NAME_2'] + str(tract['properties']['ID_2'])
            locs = getDownloadLocs(boundary_locs)
            locs_by_tract[tractid] = locs
            #uncomment the break to run for all municipalities, currently it is not efficient for bigger polygons
            found = True
        if found:
            break

    f = open(os.path.join(datadir, city, 'download_' + city + '_tract_18_imgs_locs.csv'), 'w')
    locwriter = csv.writer(f)
    loc_count = 0
    for tractid in list(locs_by_tract.keys()):
        for i in range(0, len(locs_by_tract[tractid])):
            lat, lon = locs_by_tract[tractid][i]
            loc = str(lat) + ',' + str(lon)
            imgname = city + '_' + tractid + '_' + str(i) + '.png'
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
    zoom = '18'
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser( description=('program to download satellite imagery based on geojson and municipal'))
    parser.add_argument('--geo_json_file', help=('geo json file path for columbia municipalities'))
    parser.add_argument('--municipal', help='')
    args = parser.parse_args()
    if len(key) == 0:
        print("error: please set google provide key");
    else:
        if (not args.municipal) or (not args.geo_json_file):
            print("error: usage  python3 download_img.py --geo_json_file <file_path> --municipal <NAME_2 in json> ")
        else:
            writeLocations(args.geo_json_file,args.municipal)
            locfile = os.path.join(datadir, city, 'download_' + city + '_tract_18_imgs_locs.csv')
            downloadImages(locfile)
