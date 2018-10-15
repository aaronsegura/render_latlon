import os
import math
import argparse
import subprocess

class LatLon():

    def __init__(self, lat, lon):

        if lat > 90 or lat < -90:
            raise RuntimeError("Latitude must be between -90 and 90.  Received: %s" % lat)

        if lon > 180.0 or lon < -180.0:
            raise RuntimeError("Longitude must be between -180 and 180.  Received %s" % lon )

        self.lat = lat
        self.lon = lon

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
                        help='Upper-left Coordinates in "lat,lon" format')
    parser.add_argument('-l',
                        dest='LRLATLON',
                        type=str,
                        required=True,
                        help='Lower-right Coordinates in "lat,lon" format')
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
    parser.add_argument('-m',
                        dest='mapName',
                        type=str,
                        default="default",
                        help='Map Name, default: "default"')
    parser.add_argument('-n',
                        dest='numThreads',
                        type=int,
                        default=1,
                        help='Number of threads, default:1')

    args = parser.parse_args()

    if not os.path.exists(args.tileDir):
        raise RuntimeError("Tile directory does not exist: %s" % args.tileDir)

    try:
        [lat, lon] = args.ULLATLON.split(",")
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        raise RuntimeError("Invalid upper-bound coordinates: %s" % args.ULLATLON )

    ulPos = LatLon(lat, lon)

    try:
        [lat, lon] =  args.LRLATLON.split(",")
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        raise RuntimeError("Invalid lower-bound coordinates: %s" % args.LRLATLON)

    lrPos =  LatLon(lat, lon)

    if not (lrPos > ulPos):
        raise RuntimeError("%s and %s do not form a valid bounding box" % ( ulPos, lrPos))

    for zoomLevel in range(args.minZoom, args.maxZoom+1): # Arrays atart at 9

        (ulX, ulY, _) = ulPos.tile(zoomLevel)
        (lrX, lrY, _) = lrPos.tile(zoomLevel)

        renderCmd = "render_list -a -m %s -x %s -y %s -X %s -Y %s -z %s -Z %s -t %s -n %s" \
                % ( args.mapName, 
                    ulX, ulY, 
                    lrX, lrY, 
                    zoomLevel,
                    zoomLevel, 
                    args.tileDir,
                    args.numThreads)

        print "**********************************************************"
        print "Running: %s" % renderCmd

        p = subprocess.Popen(renderCmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        try:

            while True:
                line = p.stdout.readline()
                if not line: break
                print line

        except KeyboardInterrupt:

            print "Caught CTRL-C. Killing render."
            p.kill()
            exit(1)

if __name__ == '__main__':
    try:
        main()
    except RuntimeError, err:
        print "ERROR: %s" % err.message
