
===============================================================================
Calculating Distance Between Geographic Coordinate Pairs
===============================================================================

http://www.movable-type.co.uk/scripts/gis-faq-5.1.html
https://en.wikipedia.org/wiki/Haversine_formula

.. article references



For certain types of analysis, it is necessary to compute the distance between
a pair of geographic coordinates, or the distance between many sets of coordinates
and a central reference point. This can be readily accomplished by making
use of the *Haversine formula*, which determines the great-circle distance
between two points on a sphere given their longitudes and latitudes. The
formulaic representation of the Haversine formula is:

$$
d = 2r\arcsin \left({\sqrt {\sin^{2}\left({\frac{\varphi_{2}-
    \varphi_{1}}{2}}\right)+\cos(\varphi_{1})\cos(\varphi_{2})\sin^{2}
    \left({\frac{\lambda_{2}-\lambda_{1}}{2}}\right)}}\right)

$$



there is a need to determine the distance
between coordinate pairs




To convert decimal degrees to radians, multiply the number of degrees
by pi/180 = 0.017453293 radians/degree.

Inverse trigonometric functions return results expressed in radians. To
express c in decimal degrees, multiply the number of radians by
180/pi=57.295780 degrees/radian. (But be sure to multiply the number of
RADIANS by R to get d.)



.. rubric:: Footnotes

.. [#] https://en.wikipedia.org/wiki/Haversine_formula


