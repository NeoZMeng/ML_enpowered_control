import math
import numpy as np

rEarth = 6370  # km


class Location:
    homeGPS = None  # [GPS lat, GPS lon]
    home = None

    @classmethod
    def init(cls, homeGPS):
        cls.homeGPS = homeGPS
        cls.home = Location(0, 0)

    def __init__(self, x, y):
        assert not isinstance(x, (str, list, tuple))
        self.x = x
        self.y = y

    def __getitem__(self, key):
        if key == 0 or key == 'x':
            return self.x
        if key == 1 or key == 'y':
            return self.y
        raise IndexError(f"Location obj index need to use 0, 1, 'x', 'y', but given {str(key)}")

    def __setitem__(self, key, value):
        if key == 0 or key == 'x':
            self.x = value
            return
        if key == 1 or key == 'y':
            self.y = value
            return
        raise IndexError(f"Location obj index need to use 0, 1, 'x', 'y', but given {str(key)}")

    def __eq__(self, other):
        if isinstance(other, Location):
            return self.x == other.x and self.y == other.y
        raise TypeError(f"equality comparison between Location object and {type(other)} object is not supported")

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return repr((self.x, self.y))

    def __str__(self):
        return f"({self.x: 2f}, {self.y: 2f})"

    def json(self):
        return self.asTuple()

    def asTuple(self):
        return (self.x, self.y)

    def distanceTo(self, loc):
        return np.linalg.norm(np.asarray([loc.x - self.x, loc.y - self.y]))

    def duplicate(self):
        return Location(self.x, self.y)

    @classmethod
    def fromGPS(cls, lat, lon):
        rlat = math.cos(math.radians(lat)) * rEarth
        y = math.radians(lat - cls.homeGPS[0]) * rEarth
        x = math.radians(lon - cls.homeGPS[1]) * rlat
        return cls(x, y)


class LocationList():  # vectorized location class
    homeGPS = None  # [GPS lat, GPS lon]
    home = Location(0, 0)

    @staticmethod
    def init(homeGPS):
        LocationList.homeGPS = homeGPS
        home = Location(0, 0)

    def __init__(self, x, y):
        self.x = np.asarray(x)
        self.y = np.asarray(y)

    def __getitem__(self, key):  # for getting a range of locations
        if isinstance(key, int):
            return Location(self.x[key], self.y[key])
        return LocationList(self.x[key], self.y[key])
        # raise IndexError()

    def __iter__(self):
        self.xiter = iter(self.x)
        self.yiter = iter(self.y)
        return self

    def __next__(self):
        return next(self.xiter), next(self.yiter)

    def __len__(self):
        return self.x.shape[0]

    def toLocations(self):
        if len(self.x.shape) == 0:
            return Location(self.x, self.y)
        return [Location(x, y) for x, y in self]

    @staticmethod
    def distance(loc1, loc2):
        return np.linalg.norm(np.asarray(loc2) - np.asarray(loc1), axis=1)

    @classmethod
    def fromGPS(cls, lats, lngs):
        lats = np.asarray(lats)
        lngs = np.asarray(lngs)
        rlats = np.cos(np.radians(lats)) * rEarth
        y = np.radians(lats - cls.homeGPS[0]) * rEarth
        x = np.radians(lngs - cls.homeGPS[1]) * rlats
        return cls(x, y)

    @classmethod
    def toGPS(cls, x, y):
        lats = np.degrees(y / rEarth) + cls.homeGPS[0]
        rlats = np.cos(np.radians(lats)) * rEarth
        lngs = np.degrees(x / rlats) + cls.homeGPS[1]
        return lats, lngs
