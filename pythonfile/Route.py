from Location import Location, LocationList
import numpy as np


class BasicRoute:
    def __init__(self, locations: [Location], tohome: bool = False):
        self.locs = locations
        self.tohome = tohome
        self.segmentNum = len(locations) - 1

    def __len__(self):
        return len(self.locs)

    def __getitem__(self, idx):
        return (self.locs[idx],)

    def __iter__(self):
        return iter(self.locs)

    def segments(self):
        # skip over first object
        iterObj = iter(self)
        next(iterObj)
        for _ in range(self.segmentNum):
            yield next(iterObj)
        return

    def toLocationList(self):
        xs, ys = [], []
        for loc in self.locs:
            xs.append(loc.x)
            ys.append(loc.y)
        return LocationList(xs, ys)


class GPSRoute(BasicRoute):
    reachedHome = lambda loc: False

    # home is always (0,0)

    @staticmethod
    def config(reachedHome=None):
        if reachedHome is None:
            GPSRoute.reachedHome = lambda loc: False
        else:
            GPSRoute.reachedHome = reachedHome

    @staticmethod
    def reachedHomeCircle(radius):
        return lambda loc: Location.home.distanceTo(loc) < radius

    # @classmethod
    # def fromGPStoLocation(cls, lat, lng):
    #     point = LocationList.fromGPS([lat], [lng])
    #     return point.toLocations()[0]

    @classmethod
    def fromGPStoRoute(cls, lats, lngs):
        locList = LocationList.fromGPS(lats, lngs).toLocations()
        tohome = cls.reachedHome(locList[-1])
        return cls(locList, tohome)

