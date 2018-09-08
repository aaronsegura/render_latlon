import os
import time
import math
import argparse
import subprocess

class LatLon():

    def __init__(self, lat, lon):
        self.lat = float(lat)
        self.lon = float(lon)

    def tile(self, zoom):
        lat_rad = math.radians(self.lat)
        n = 2.0 ** zoom
        x = int((self.lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (x,y,zoom)

    def __gt__(self, other):
        if self == other:
            return False
        else:
            # counter-intuitive
            return self.lat <= other.lat and self.lon >= other.lon

    def __eq__(self, other):
        return self.lat == other.lat and self.lon == other.lon

    def __repr__(self):
        return "LatLon(%s, %s)" % (self.lat, self.lon)

def main():

    parser = argparse.ArgumentParser(description='render_list based on lat/lon coordinates.')

    parser.add_argument('-u',
                        dest='ULLATLON',
                        type=str,
                        required=True,
                        help='Upper-left LatLon Coordinates in "lat,lon" format')
    parser.add_argument('-l',
                        dest='LRLATLON',
                        type=str,
                        required=True,
                        help='Lower-right LatLon Coordinates in "lat,lon" format')
    parser.add_argument('-z',
                        dest='minZoom',
                        type=int,
                        required=True,
                        help='Minimum Zoom Level')
    parser.add_argument('-Z',
                        dest='maxZoom',
                        type=int,
                        required=True,
                        help='Maximum Zoom Level')
    parser.add_argument('-t',
                        dest='tileDir',
                        type=str,
                        required=True,
                        help='mod_tile caching directory')

    args = parser.parse_args()

    if not os.path.exists(args.tileDir):
        raise RuntimeError("Tile directory does not exist: %s" % args.tileDir)

    try:
        ulPos = LatLon(args.ULLATLON.split(",")[0], args.ULLATLON.split(",")[1])
    except IndexError:
        raise RuntimeError("Invalid coordinates for Upper-left bound: %s" % args.ULLATLON)

    try:
        lrPos =  LatLon(args.LRLATLON.split(",")[0], args.LRLATLON.split(",")[1])
    except IndexError:
        raise RuntimeError("Invalid coordinates for Lower-right bound: %s" % args.LRLATLON)


    if not (lrPos > ulPos):
        raise RuntimeError("Error: %s and %s do not form a valid bounding box" % ( ulPos, lrPos))

    for zoomLevel in range(args.minZoom, args.maxZoom+1): # Arrays atart at 9

        (ulX, ulY, _) = ulPos.tile(zoomLevel)
        (lrX, lrY, _) = lrPos.tile(zoomLevel)

        renderCmd = "render_list -a -x %s -y %s -X %s -Y %s -z %s -Z %s -t %s" \
                    % ( ulX, ulY, lrX, lrY, zoomLevel, zoomLevel, args.tileDir)

        print "**********************************************************"
        print "Running: %s" % renderCmd

        p = subprocess.Popen(renderCmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        try:

            while True:
                line = p.stdout.readline()
                if not line: break
                print line
                time.sleep(0.1)

        except KeyboardInterrupt:

            print "Caught CTRL-C. Killing render."
            p.kill()
            exit(1)

if __name__ == '__main__':
    try:
        main()
    except RuntimeError, err:
        print "ERROR: %s" % err.message
