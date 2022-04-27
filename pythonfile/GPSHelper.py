from math import sin, cos, degrees, radians, asin, sqrt

r = 6370000 #m

def distance(lat1, lng1, lat2, lng2):
    lat1rad = radians(lat1)
    lng1rad = radians(lng1)
    lat2rad = radians(lat2)
    lng2rad = radians(lng2)
    dlon = lng2rad - lng1rad
    dlat = lat2rad - lat2rad
    a = sin(dlat / 2) ** 2 + cos(lat1rad) * cos(lat2rad) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * r
