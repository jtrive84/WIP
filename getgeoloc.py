#/usr/bin/env python
"""
Return latitude and longitude as dict based on provided address.
"""
import webbrowser
import requests
import sys
import re
import os


proxies = {
    "http" :"http://cac9159:FJ7865bn@proxy.cna.com:8080/",
    "https":"https://cac9159:FJ7865bn@proxy.cna.com:8080/",
    }


API_KEY = "AIzaSyChI37elgjsfforLX1Ms7mYz9NxS_VbCM0"


def getgeoloc(address: str, authkey=API_KEY) -> dict:
    """
    Encode URL with address and pass to Geocode API
    to retrieve corresponding geolocation.
    """
    address_base    = "https://maps.googleapis.com/maps/api/geocode/json?address="
    encoded_address = re.sub("\s+", "+", address.strip()).replace(",", "")
    encoded_url     = address_base + encoded_address + "&key=" + authkey
    response        = requests.get(encoded_url,proxies=proxies)
    coords          = response.json()['results'][0]['geometry']['location']
    return(coords)



def getmaploc(address:str, authkey=API_KEY):
    """
    Set pin at location given by address using google maps API.
    """
    address_base    = r"https://www.google.com/maps/search/?api=1&query="
    encoded_address = re.sub("\s+", "+", address.strip()).replace(",", "")
    full_url        = address_base + encoded_address + "&key=" + authkey
    webbrowser.open(full_url)
    return(None)






if __name__ == "__main__":

    address = sys.argv[1].strip()

    try:
        if "--load-map" in sys.argv[1:]:
            getmaploc(address=address)
        else:
            ll  = getgeoloc(address)
            lat = ll['lat']
            lon = ll['lng']
            print(ll)
            coords = str(lat) + "," + str(lon)
            #getmaploc(address=coords)
    except:
        print("Invalid address specified. Exiting.")
