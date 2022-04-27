import numpy as np
import pandas as pd
from GPSHelper import distance
from SimFunc import *
from math import tan

class Car:
    # mass in kg, batteryCapacity in kWh, elecConsump in kWh/m, fuelConsump in L/kJ, maxCharging in kW
    def __init__(self, mass, batteryCapacity, elecConsump, fuelConsump, maxCharging):
        self.m = mass
        self.bat = batteryCapacity * 3600           # kJ
        self.eCons = elecConsump * 3600       # kJ/m
        self.fCons = fuelConsump
        self.maxCharging = maxCharging


class Simulator:
    # base unit: distance: m, mass kg, energy kJ
    def __init__(self, speedProfile, slopeProfile, startingSOC, dt, car: Car, minSOC, useNewAlg):
        self.speed = speedProfile  # numpy.ndarray of size (n, 2)
        self.slope = slopeProfile  # numpy.ndarray of size (n, 2)
        self.terminalt = self.speed[-1][0]
        self.batEnergy = car.bat * startingSOC
        self.minBatEnergy = minSOC * car.bat
        self.minSOC = minSOC
        self.dt = dt
        self.t = 0
        self.distanceDriven = 0
        self.car = car
        self.useNewAlg = useNewAlg
        self.fuelUsed = 0
        self.socRecord = []
        self.fuelRecord = []
        self.engineRecord = []
        self.tRecord = []
        self.energyRecord = []
        self.distanceRecord = []

    @property
    def soc(self):
        return self.batEnergy / self.car.bat

    def curr_speed(self):
        last_v = 0
        for t, v in self.speed:
            if self.t < t:
                return last_v
            last_v = v

    def curr_slope(self):
        last_slope = 0
        for t, slope in self.speed:
            if self.t < t:
                return last_slope
            last_slope = slope

    def electricConsumption(self):
        dist = self.dt * self.curr_speed()
        dh = tan(self.curr_slope()) * dist
        # potentialEnergy = self.car.m * 9.8 * dh / 1000
        # slope value is changing very rapidly
        potentialEnergy = 0
        energyConsump = potentialEnergy + dist * self.car.eCons
        return energyConsump, dist # in kJ

    def engineCharging(self, energyConsump):
        if self.minSOC - self.soc < 0.01:
            return energyConsump
        else:
            return self.car.maxCharging

    def fuelConsumption(self, energyConsump):
        return energyConsump * self.car.fCons # in Liter

    def engineOnOff(self):
        return self.batEnergy < self.minBatEnergy



    def simulate(self):
        progress = 0
        progressPeriod = self.terminalt / 20
        progresst = 0
        while self.t <= self.terminalt:
            if self.t > progresst:
                progresst += progressPeriod
                progress += 1
                print(f"working on {progress}/20")
            recordTime(self.t)
            energyConsump, dist = self.electricConsumption()
            self.distanceDriven += dist
            engineStatus = self.engineOnOff()
            if self.useNewAlg:
                engineStatus = engineStatus and engineOnOff(self.soc)
            if engineStatus:
                # engine on
                enginePowerDemand = self.engineCharging(energyConsump)
                fuelConsump = self.fuelConsumption(enginePowerDemand)
                self.batEnergy -= energyConsump - enginePowerDemand
                self.fuelUsed += fuelConsump
            else:
                self.batEnergy -= energyConsump
            self.socRecord.append(self.soc)
            self.distanceRecord.append(self.distanceDriven)
            self.fuelRecord.append(self.fuelUsed)
            self.engineRecord.append(engineStatus)
            self.tRecord.append(self.t)
            self.energyRecord.append(energyConsump)
            self.t += self.dt



    @staticmethod
    def getRoute(fileName):
        route = pd.read_csv(fileName)
        return route
