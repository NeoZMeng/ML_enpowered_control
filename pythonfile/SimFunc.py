import numpy as np
import sys
sys.path.insert(1, 'SaveFuel_WholeProgram')
from DestinationPrediction import DestiPred
from EnergyPrediction import EnergyPred
import pandas as pd
from math import sqrt, asin, atan
from GPSHelper import distance

# iroute = None
route = None
lowSoc = 0.3
minSoc = 0.1
timeStep = None
status = None
nextTime = 0
curr_time = 0








def init(homeGPS_lat, homeGPS_lng, check_period):
    global iroute, timeStep, nextTime
    # iroute = i
    timeStep = check_period
    nextTime = 0
    homeGPS = (homeGPS_lat, homeGPS_lng)
    DestiPred.init(homeGPS=homeGPS, probThreshold=0.6, homeRadius=0.1)
    DestiPred.load()
    EnergyPred.init(homeGPS=homeGPS)
    EnergyPred.load()


def getRoute(fileName):
    # read from files[index]
    # store data in route
    # return a version for autonomie to simulate
    global route
    route_pd = pd.read_csv(fileName)
    simu_speed = []
    simu_slope = []
    routeIterObj = iter(route_pd.to_numpy())
    lastPoint = next(routeIterObj)
    try:
        while True:
            point = next(routeIterObj)
            dist = distance(point[1], point[2], lastPoint[1], lastPoint[2])
            dt = point[0] - lastPoint[0]
            if dt == 0:
                continue
            dh = point[3] - lastPoint[3]
            speed = dist / dt
            slope = atan(dh / dist)
            simu_speed.append([lastPoint[0], speed])
            simu_slope.append([lastPoint[0], slope])
            lastPoint = point
    except StopIteration:
        pass
    route = route_pd
    return np.asarray(simu_speed), np.asarray(simu_slope)


def recordTime(time):
    global curr_time
    curr_time = time


# isim is the index of the GPS point the simulation is currently on
def engineOnOff(soc):
    global nextTime, status
    if curr_time < nextTime:
        return status
    nextTime += timeStep

    if soc < minSoc:
        status = True
        return status
    if soc > lowSoc:
        status = False
        return status
    idx = 0
    for point_time in route["time"].to_numpy():
        if curr_time <= point_time:
            break
        idx += 1
    lats = route["lats"][:idx]  # [:isim]
    lngs = route["lngs"][:idx]  # [:isim]
    toHome = DestiPred.predict(lats, lngs)
    if not toHome:
        status = True
        return status
    # calculate current gps from routes, should be replaced with real gps coordinates
    if idx > 0:
        t1, t2 = route["time"][idx - 1:idx + 1]
        lat1, lat2 = route["lats"][idx - 1:idx + 1]
        lng1, lng2 = route["lngs"][idx - 1:idx + 1]
        frac = (curr_time - t1) / (t2 - t1)
        curr_lat = frac * (lat2 - lat1) + lat1
        curr_lng = frac * (lng2 - lng1) + lng1

        socEsti = EnergyPred.predict(curr_lat, curr_lng)[1]
        socEsti /= 100
        status = (soc - socEsti) < minSoc
    else:
        status = False
    return status


def learnRoute():
    DestiPred.learn(route["lats"], route["lngs"])
    DestiPred.store()
def clearLearnedRoute():
    DestiPred.clearRouteMemory()
    DestiPred.store()