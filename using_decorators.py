


def document_it(func):
    def new_function(*args, **kwargs):
        print("Running function: ", func.__name__)
        print("Positional arguments: ", args)
        print("Keyword arguments: ", kwargs)
        result = func(*args, **kwargs)
        print("Result: ", result)
        return(result)
    return(new_function)



def add_ints(a, b):
    return(a + b)

# Manual decorator assignment:
cooler_add_ints = document_it(add_ints)

a=cooler_add_ints(10, 11)


# Using @document_it syntax:

@document_it
def add_ints(a, b):
    return(a + b)


# Doubling decorators:

def square_it(func):
    def new_function(*args, **kwargs):
        result = func(*args, **kwargs)
        return(result * result)
    return(new_function)


@square_it
@document_it
def add_ints(a, b):
    return(a + b)

add_ints(10,10)


# Timing decorator.
import time
from functools import wraps

def timethis(func):
    """
    Decorator that reports execution time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(func.__name__, end-start)
    return(wrapper)


# typeassert decorator ########################################################

import inspect
from functools import wraps
#
# def typeassert(*ty_args, **ty_kwargs):
#     def decorate(func):
#         # If in optimized mode, diable type checking.
#         if not __debug__:
#             return(func)
#
#         # Map function argument names to supplied types.
#         sig = inspect.signature(func)
#         bound_types = sig.bind_partial(*ty_args, **ty_kwargs).arguments
#
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             bound_values = sig.bind(*args, **kwargs)
#             # Enforce type asssertions across supplied arguments.
#             for name, value in bound_values.arguments.items():
#                 if name in bound_types:
#                     if not isinstance(value, bound_types[name]):
#                         raise TypeError("Argument {} must be {}".format(name, )
#
#





def distunits(distance_units):
    """1km = .621371mi"""
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            result_init = function(*args, **kwargs)
            if distance_units.lower().startswith("mi"):
                # Convert result_init (in km) to miles.
                result = .621371 * result_init
            elif distance_units.lower().startswith("f"):
                # Convert result_init (in km) to feet.
                result = 5280. * .621371 * result_init
            elif distance_units.lower().strip()=="meters":
                # Convert result_init (in km) to meters.
                result = 1000. * result_init
            else:
                result = result_init
            return(result)
        return(wrapper)
    return(decorator)



@distunits("meters")
def getdist(geoloc1:tuple, geoloc2:tuple, R=6368):
    """
    Compute air-travel distance between geographic coordinate pairs.
    :param geoloc1: (lat1, lon1) of first geolocation
    :param geoloc2: (lat2, lon2) of second geolocation
    :param R: Radius of Earth in 6367km/3957mi (est.)
    """
    # Convert degress to radians then compute differences.
    rlat1, rlon1 = [i * math.pi / 180 for i in geoloc1]
    rlat2, rlon2 = [i * math.pi / 180 for i in geoloc2]
    drlat, drlon = (rlat2 - rlat1), (rlon2 - rlon1)

    init = (math.sin(drlat / 2.))**2 + (math.cos(rlat1)) * \
           (math.cos(rlat2)) * (math.sin(drlon /2.))**2

    # The intermediate result `init` is the great circle distance
    # in radians. The return value will be in the same units as R.
    # (see http://www.movable-type.co.uk/scripts/gis-faq-5.1.html).
    return(2.0 * R * math.asin(min(1., math.sqrt(init))))




c1 = (41.8781,-87.6298)
c2 = (40.7128,-74.0060)

dst1 = getdist(geoloc1=c1, geoloc2=c2)























