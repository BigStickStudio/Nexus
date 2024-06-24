from transceiver import Polarity
from resonator import Resonator

describe = lambda idx, cartesian: f"Index: {idx} Cartesian: {cartesian}"
get3DIndex = lambda x, y, z, dimension_size: z * dimension_size * dimension_size + y * dimension_size + x
get2DIndex = lambda x, y, dimension_size: x + y * dimension_size

class Position:
    def __init__(self, idx, origin):
        self.idx = idx
        self.x, self.y, self.z = origin
        self.origin = lambda: (self.x, self.y, self.z)
        
class Reflector(Position, Resonator):
    def __init__(self, idx, cartesian):
        super().__init__(idx, cartesian)
        self.cartesian = lambda: self.origin()
        self.orthogonal = set()       # These are the reflectors that are orthogonal to this reflector  - up to 6
        self.adjacent = set()         # These are the reflectors that are adjacent to this reflector    - up to 12
        self.polar = set()            # These are the reflectors that are polar to this reflector       - up to 8
        self.loopback = None          # This is a connection to ourselves                               - 1 | None
        self.neighbors = [self.loopback, *self.orthogonal, *self.adjacent, *self.polar]

    def __str__(self):
        return f"{describe(self.idx, self.origin())}" \
                f"\n\tOrthogonal: {len(self.orthogonal)}" \
                f"\n\tAdjacent: {len(self.adjacent)}" \
                f"\n\tPolar: {len(self.polar)}" \
                f"\n\tLoopback: {"Self" if self.loopback is not None else "None"}"
    
    def __repr__(self):
        return str(self)
    
    def addReflection(self, reflection):
        match reflection.polarity:
            case Polarity.Self:
                self.loopback = reflection
            case Polarity.Orthogonal:
                self.addOrthogonal(reflection)
            case Polarity.Adjacent:
                self.addAdjacent(reflection)
            case Polarity.Polar:
                self.addPolar(reflection)

    def addOrthogonal(self, reflection):
        self.orthogonal.add(reflection)
    
    def addAdjacent(self, reflection):
        self.adjacent.add(reflection)

    def addPolar(self, reflection):
        self.polar.add(reflection)

    
    def matcher(self, offset, neighbour_cartesians) -> bool:
        position = lambda: (self.x + offset[0], self.y + offset[1], self.z + offset[2])
        return position == neighbour_cartesians

    def isPolar(self, neighbor_cartesians):
        poles = [(1, 1, 1), (-1, 1, 1), (-1, 1, -1), (1, 1, -1)]
        return any([self.matcher(offset, neighbor_cartesians) for offset in poles])

    # This function could be modified to connect new reflectors and determine their influence
    def isOrthogonal(self, neighbor_cartesians):
        neighbor_x, neighbor_y, neighbor_z = neighbor_cartesians

        match_box = 0
        match_box += 1 if self.x == neighbor_x else 0
        match_box += 1 if self.y == neighbor_y else 0
        match_box += 1 if self.z == neighbor_z else 0

        return match_box == 1
    
    def isAdjacent(self,neighbor_cartesians):
        adjacencies = [(1, 1, 0), (1, 0, 1), (0, 1, 1), (-1, 1, 0), (-1, 0, 1), (0, 1, -1)]
        return any([self.matcher(offset, neighbor_cartesians) for offset in adjacencies])

    def reflectionType(self, neighbor_cartesians):
        print("\t\t\t\t > Determining Reflection Type")
        print("\t\t\t\t\t > Self: ", self.origin(), " Neighbor: ", neighbor_cartesians)
        if self.cartesian() == neighbor_cartesians:
            print("\t\t\t\t\t > Self Reflection")
            return Polarity.Self
        if self.isPolar(neighbor_cartesians):
            print("\t\t\t\t\t > Polar Reflection")
            return Polarity.Polar
        if self.isOrthogonal(neighbor_cartesians):
            print("\t\t\t\t\t > Orthogonal Reflection")
            return Polarity.Orthogonal
        if self.isAdjacent(neighbor_cartesians):
            print("\t\t\t\t\t > Adjacent Reflection")
            return Polarity.Adjacent
        
    # TODO: The transceiver needs to be wired up to the reflection type
    async def rcv(self, transmission): # Do we want to log who we receptioned from?
        print("  -[ Node Received: ", transmission, " ]")
        self.reception = transmission
        awaiting = await self.resonate()
        print(self.idx, " has resonated at ", self.phase, " with a resulting threshold of ", self.threshold)
        return awaiting
    
    ## This Function is purely for testing and simulation purposes to induce the reception of a signal
    async def incept(self, frequency = 440):
        print(" [ Node Incepted: ", self.idx, " ]")
        i = frequency
        while i > 0:
            await self.rcv(frequency)
            print("|> Incepting: ", i)
            print("theta::", self.theta, ", thrsh::", self.threshold, ", recpt::", self.reception)
            i -= 1

    # TODO: The transceiver needs to be wired up to the reflection type
    async def snd(self, other):
        print("  -[ Node Sending: ", self.theta, " to ", other.idx, " ]")
        self.reception = (self.theta + other.threshold) / 2.0
        await self.resonate()
        return await other.rcv(self.theta)
    
    ## This function is purely to simulate the sending of a signal
    async def simulate(self, idx):
        print(" [ Node Simulated: ] ", self.idx)
        i = self.resolution(440)
        while i > 0:
            await self.snd(self.connections[idx])
            print("|> Simulating: ", i)
            print("theta::", self.theta, ", thrsh::", self.threshold, ", recpt::", self.reception)
            i -= 1