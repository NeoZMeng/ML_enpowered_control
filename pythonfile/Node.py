from collections import defaultdict

from Location import Location
from Route import BasicRoute
import json


class Node:
    homeNode = None
    # stores all nodes, use dict type for easy access
    nodes = None  # {loc: Node}
    nodeMap = None
    minDist = 0.25
    gridSize = 0.3

    @staticmethod
    def init(minDist=0.1, gridSize=0.1):
        Node.prepareRecord()
        Node.homeNode = Node(Location.home, Location.home.asTuple())
        Node.minDist = minDist
        Node.gridSize = gridSize

    @classmethod
    def prepareRecord(cls):
        cls.nodes = {}
        cls.nodeMap = defaultdict(lambda: defaultdict(list))

    def __init__(self, loc: Location, xy = None):
        assert isinstance(loc, Location)
        self.loc = loc
        self.next = {}  # {loc: [Node, home count, total count]}
        assert loc not in Node.nodes
        # add itself into the nodes record
        # since the node is of class self.__class__, it has to be add to the self.__class__.nodes
        Node.nodes[loc] = self
        if xy is not None:
            Node.nodeMap[xy[0]][xy[1]].append(self)

    def __hash__(self):
        return hash(self.loc)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.loc == other.loc
        raise TypeError(f"equality comparison between Node object and type(other) object is not supported")

    def __repr__(self):
        return repr(self.loc)

    def __str__(self):
        return f"{self.loc}, next = {[(loc, *self.next[loc][1:]) for loc in self.next]}]"

    def toJson(self):
        return [self.loc.json(), [[loc.json(), *self.next[loc][1:]] for loc in self.next]]

    @classmethod
    def addFromJson(cls, jsonNode):
        loc, nexts = jsonNode
        loc = Location(*loc)
        node = cls.get(loc, addition=True)
        node.next = {}
        for next in nexts:
            nloc = Location(*next[0])
            node.next[nloc] = [cls.get(nloc, addition=True), *next[1:]]

    def updateNext(self, node, tohome: bool, *args):
        if node.loc in self.next:
            self.next[node.loc][1] += int(tohome)
            self.next[node.loc][2] += 1
        else:
            self.next[node.loc] = [node, int(tohome), 1]

    def _prob(self, loc):
        if loc in self.next:
            data = self.next[loc]
            return data[1] / data[2]
        return False

    @staticmethod
    def get(loc, addition=False):
        x = int(loc.x / Node.gridSize)
        y = int(loc.y / Node.gridSize)
        nodes = []
        # used a grid to manage the nodes, so it will be faster to find the nearest node
        # will try to find the nearest node in a 3x3 grid for accurate results
        for i in range(x - 1, x + 2):
            if i in Node.nodeMap:
                nodeColumn = Node.nodeMap[i]
                for j in range(y - 1, y + 2):
                    if j in nodeColumn:
                        nodes.extend(nodeColumn[j])
        if len(nodes) > 0:
            closestNode = min(nodes, key=lambda node: node.loc.distanceTo(loc))
            if closestNode.loc.distanceTo(loc) < Node.minDist:
                return closestNode
        return Node(loc, (x, y)) if addition else None

    @classmethod
    def process(cls, route: BasicRoute):
        tohome = route.tohome
        lastNode = cls.get(route.locs[0], addition=True)
        for segment in route.segments():
            loc = segment
            node = cls.get(loc, addition=True)
            if node == lastNode:
                continue
            lastNode.updateNext(node, tohome)
            lastNode = node

    @classmethod
    def prob(cls, node1, node2):
        if node2.loc not in node1.next:
            # no histroy of going from node1 to node 2, probablility is 0
            return 0
        nextData = node1.next[node2.loc]
        return nextData[1] / nextData[2]

    @classmethod
    def getNodes(cls):
        return cls.nodes

    @classmethod
    def storeNodes(cls, fileName):
        data = [node.toJson() for node in cls.nodes.values()]
        jdata = json.dumps(data)
        with open(fileName, 'w+') as file:
            file.write(jdata)

    @classmethod
    def loadNodes(cls, fileName):
        data = None
        with open(fileName, 'r') as file:
            data = file.read()
        jdata = json.loads(data)
        for jsonNode in jdata:
            cls.addFromJson(jsonNode)

    @classmethod
    def nextNode(cls, route, i):
        node1 = cls.get(route[i], addition=True)
        i += 1
        while cls.get(route[i], addition=True) == node1:
            i += 1
        return route[i]

class ReverseNode(Node):
    pass


