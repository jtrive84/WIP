import sys
import os
import time
import math
import requests
import datetime


USERNAME = "cac9159"
PASSWORD = "VM8925xh"

def getdistance(geoloc1:tuple, geoloc2:tuple, R=6367):
    """
    Compute distance between geographic coordinate pairs.
    :param geoloc1: (lat1, lon1) of first geolocation
    :param geoloc2: (lat2, lon2) of second geolocation
    :param R: Radius of Earth (est.)
    """
    # Convert degress to radians then compute differences.
    rlat1, rlon1 = [i * math.pi / 180 for i in geoloc1]
    rlat2, rlon2 = [i * math.pi / 180 for i in geoloc2]
    drlat, drlon = (rlat2 - rlat1), (rlon2 - rlon1)

    init = (math.sin(dlat / 2.))**2 + (math.cos(rlat1)) * \
           (math.cos(rlat2)) * (math.sin(dlon /2.))**2

    # The intermediate result `init` is the great circle distance
    # in radians. The return value will be in the same units as R.
    # min protects against possible roundoff errors that could
    # sabotage computation of the arcsine if the two points are
    # very nearly antipoda, e.g., on opposide sides of the Earth
    # (see http://www.movable-type.co.uk/scripts/gis-faq-5.1.html).
    return(2.0 * R * math.asin(min(1., math.sqrt(init))))
```


# 1609.34m per mile

# Replace CID and password.
proxies = {
    "http" :f"http://{USERNAME}:{PASSWORD}@proxy.cna.com:8080/",
    "https":f"https://{USERNAME}:{PASSWORD}@proxy.cna.com:8080/",
    }

API_KEY = "AIzaSyAD-B7TcHQh6-AkwpqRknCLeLUAdEpcVzc"
coords  = "&origins=41.8781,87.6298|40.7128,74.0060"
url     = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins=41.8781,87.6298&destinations=40.7128,74.0060&key=AIzaSyAD-B7TcHQh6-AkwpqRknCLeLUAdEpcVzc"
resp    = requests.get(url, proxies=proxies).json()

url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=41.8781,-87.6298&destinations=40.7128,-74.0060&key=AIzaSyAD-B7TcHQh6-AkwpqRknCLeLUAdEpcVzc"

def getiss(proxy=None):
    """
    Get timestamped geo-coordinates of International Space Station.
    """
    dpos = dict()
    URL  = "http://api.open-notify.org/iss-now.json"
    resp = requests.get(URL, proxies=proxy).json()
    if resp["message"]=="success":
        dpos["timestamp"] = resp["timestamp"]
        dpos["latitude"]  = float(resp["iss_position"]["latitude"])
        dpos["longitude"] = float(resp["iss_position"]["longitude"])
    return(dpos)


def getdistance(geoloc1:tuple, geoloc2:tuple):
    """
    Compute distance between geo-coordinates.
    :param geoloc1: (lat1, lon1) of first geolocation
    :param geoloc2: (lat2, lon2) of second geolocation
    """
    R = 6367 # Radius of Earth (in km).

    def to_rad(deg):
        return(deg * math.pi / 180.)

    lat1, lon1 = geoloc1
    lat2, lon2 = geoloc2
    dlat, dlon = (to_rad(lat2)-to_rad(lat1)),(to_rad(lon2)-to_rad(lon1))
    init = (math.sin(dlat/2.))**2 + (math.cos(to_rad(lat1))) * \
           (math.cos(to_rad(lat2))) * (math.sin(dlon/2.))**2
    # The intermediate result gcdist is the great circle distance in radians.
    # The great circle distance d will be in the same units as R.
    gcdist = 2. * math.asin(min(1., math.sqrt(init)))
    return(R * gcdist)


def getspeed(dpos1:dict, dpos2:dict, units="mph"):
    """
    Compute speed of ISS relative to Earth's surface using
    a pair of dicts produced by `getiss`.
    """
    # Convert unix epochs to timestamp datetime objects.
    ts1   = datetime.datetime.fromtimestamp(dpos1['timestamp'])
    ts2   = datetime.datetime.fromtimestamp(dpos2['timestamp'])
    secs  = abs((ts2-ts1).total_seconds())
    loc1  = (dpos1["latitude"], dpos1["longitude"])
    loc2  = (dpos2["latitude"], dpos2["longitude"])
    dist  = getdistance(geoloc1=loc1, geoloc2=loc2)
    vinit = (dist/secs)

    if units=="kph":
        vfinal = vinit * 3600              # kph
    elif units=="mph":
        vfinal = vinit * 3600 * 0.62137119 # mph
    else: vfinal = vinit
    return(vfinal)



def main():
    print("Capturing first geo-location snapshot...")
    dpos1 = getiss(proxy=proxies)
    time.sleep(5)
    print("Capturing second geo-location snapshot...")
    dpos2 = getiss(proxy=proxies)
    # Compute speed of ISS relative to Earth based on retrieved
    # geographical coordinates.
    print("Computing speed of ISS relative to Earth's surface...")
    vkph = getspeed(dpos1=dpos1, dpos2=dpos2, units="kph")
    vmph = getspeed(dpos1=dpos1, dpos2=dpos2, units="mph")
    print(f"ISS speed (km/h): {vkph:.2f}")
    print(f"ISS speed (mi/h): {vmph:.2f}")



if __name__ == "__main__":

    main()


