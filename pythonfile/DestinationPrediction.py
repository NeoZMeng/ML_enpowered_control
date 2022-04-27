from Location import LocationList, Location
from Route import GPSRoute
from Node import Node
from warnings import warn


class DestiPred:
    homeGPS = None
    nodeJsonFileName = "nodes.json"
    probThreshold = 0.6

    @staticmethod
    def init(homeGPS, probThreshold=0.6, homeRadius=0.05):
        if (not isinstance(homeGPS, (tuple, list))) or len(homeGPS) != 2:
            raise ValueError("homeGPS parameter can only be tuple/list of 2 float, (lat, lng)")
        DestiPred.homeGPS = homeGPS
        DestiPred.probThreshold = probThreshold
        LocationList.homeGPS = homeGPS
        Location.init(homeGPS)
        reachedHomeFunc = GPSRoute.reachedHomeCircle(homeRadius)
        GPSRoute.config(reachedHome=reachedHomeFunc)
        Node.init(minDist=0.2, gridSize=0.2)

    @staticmethod
    def learn(lats, lngs):
        route = GPSRoute.fromGPStoRoute(lats, lngs)
        Node.process(route)

    @staticmethod
    def store():
        Node.storeNodes(DestiPred.nodeJsonFileName)

    @staticmethod
    def load():
        Node.loadNodes(DestiPred.nodeJsonFileName)

    # predicting from any two points is pointless as it easily returns 0 or None due to no record or two points being too close
    @staticmethod
    def prob(lats, lngs):
        pointer = len(lats) - 1
        node2 = None
        while node2 is None:
            if pointer < 0:
                warn("Cannot find any point from this input, if never driven this route, ignore this warning", category=UserWarning)
                return 0
            node2 = Node.get(Location.fromGPS(lats[pointer], lngs[pointer]))
            pointer -= 1
        node1 = None
        while node1 is None or node1 == node2:
            if pointer < 0:
                warn("Cannot find the previous point from this input, may be caused by the input being too short, if never driven this route, ignore this warning", category=UserWarning)
                return 0
            node1 = Node.get(Location.fromGPS(lats[pointer], lngs[pointer]))
            pointer -= 1
        return Node.prob(node1, node2)

    @staticmethod
    def predict(lats, lngs):
        return DestiPred.prob(lats, lngs) > 0.6

    @staticmethod
    def getNodeMap():
        return Node.getNodes()

    @staticmethod
    def nearHome(lat, lng):
        loc = Location.fromGPS(lat, lng)
        return GPSRoute.reachedHome(loc)

    @staticmethod
    def clearRouteMemory():
        Node.nodes = {}