"""
https://developers.google.com/maps/documentation/geocoding/start
"""
import re
import sys
import os
import requests


USERNAME = "cac9159"
PASSWORD = "VM8925xh"
API_KEY  = "AIzaSyAD-B7TcHQh6-AkwpqRknCLeLUAdEpcVzc"

proxies = {
    "http" :"http://{USERNAME}:{PASSWORD}@proxy.cna.com:8080/",
    "https":f"https://{USERNAME}:{PASSWORD}@proxy.cna.com:8080/",
    }

#https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key=YOUR_API_KEY


def get_latlon(address, authkey=API_KEY, proxy=None, dryrun=False) -> dict:
    """
    Obtain geographic coordinate pairs via Google's Geocode API.
    Requires apikey, which can be obtained here:
        https://developers.google.com/maps/documentation/geocoding/get-api-key

    Parameters
    ----------
    address: str
        Street address of interest.

    authkey: str
        Goolge Geocode API authorization key. Required. Anonymous usage
        no longer permitted.

    proxy: dict
        Optional proxy server details used for request.

    dryrun: bool
        If True, return encoded url and exit. Otherwise, submit url
        to Geocode API.

    Returns
    -------
    dict
        Dictionary containing keys "lat" for latitude, "lng" for
        longitude and "url" for the encoded url.
    """
    base_url    = "https://maps.googleapis.com/maps/api/geocode/json?address="
    encaddress  = re.sub("\s+", "+", address.strip()).replace(",", "")
    encoded_url = base_url + encaddress + "&key=" + authkey

    if dryrun:
        coords, lat, lng = None, None, None
    else:
        response = requests.get(encoded_url, proxies=proxy).json()
        coords   = response["results"][0]["geometry"]["location"]
        lat, lng = coords["lat"], coords["lng"]
    return({"url":encoded_url, "lat":lat, "lng":lng})





def get_dist(loc1, loc2, authkey=API_KEY, proxy=None, dryrun=False):
    """
    Compute distance between two pairs of geographic coordinates.

    https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=Washington,DC&destinations=New+York+City,NY&key=YOUR_API_KEY
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"

    # Convert loc1 to geographic coordinates if given as address.
    





# Test API function calls ====================================================]

addrs = [
    "8315 S. Kolin, Chicago IL 60652",
    "1130 Ontario Oak Park, IL 60302",
    "4630 West 128th Street Alsip Illinois 60803",
    "4630 w. 128th St. Alsip Illinois 60803",
    ]

res0 = get_latlon(addrs[0], authkey=API_KEY, proxy=proxies, dryrun=False)
url0 = res0["url"]
lat0 = res0["lat"]
lng0 = res0["lng"]


