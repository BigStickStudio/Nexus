from Tranception import Orientation
from Tranception.resonator import Resonator
from Tranception.debug import debug

describe = lambda idx, cartesian: f"Reflector Index: {idx} Cartesian: {cartesian}"
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
        Resonator.__init__(self)
        self.cartesian = lambda: self.origin()
        self.orthogonal = set()       # These are the reflectors that are orthogonal to this reflector  - up to 6
        self.adjacent = set()         # These are the reflectors that are adjacent to this reflector    - up to 12
        self.polar = set()            # These are the reflectors that are polar to this reflector       - up to 8
        self.loopback = None          # This is a connection to ourselves                               - 1 | None
        self.neighbors = [self.loopback, *self.orthogonal, *self.adjacent, *self.polar]
        self.distance = lambda neighbor: sum([(a - b) ** 2 for a, b in zip(self.origin(), neighbor)]) ** 0.5
        print("\t\t\t - Reflector initialized")

    def __str__(self):
        return f"{describe(self.idx, self.origin())}" \
                f"\n\tOrthogonal: {len(self.orthogonal)}" \
                f"\n\tAdjacent: {len(self.adjacent)}" \
                f"\n\tPolar: {len(self.polar)}" \
                f"\n\tLoopback: {"Self" if self.loopback is not None else "None"}"
    
    def __repr__(self):
        return str(self)
    
    def report(self):
        return f"\t{describe(self.idx, self.origin())}" \
                f"\n\t\tOrthogonal: {len(self.orthogonal)}" \
                f"\n\t\tAdjacent: {len(self.adjacent)}" \
                f"\n\t\tPolar: {len(self.polar)}" \
                f"\n\t\tLoopback: {"Self" if self.loopback is not None else "None"}"
    
    def reflectionType(self, neighbor_cartesians):
        debug(5 ,"\t\t\t\t > Determining Reflection Type")
        distance = self.distance(neighbor_cartesians)
        debug(5 ,f"\t\t\t\t\t > Self: {self.origin()}, Neighbor:  {neighbor_cartesians} => Distance: {distance}")

        if distance > 2:
            return Orientation.OutOfRange
        if distance == 0:
            return Orientation.Self
        elif distance <= 1:
            return Orientation.Orthogonal
        elif distance <= 1.5:
            return Orientation.Adjacent
        else:
            return Orientation.Polar
        
    def addReflection(self, reflection):
        match reflection.polarity:
            case Orientation.Self:
                self.loopback = reflection
            case Orientation.Orthogonal:
                self.addOrthogonal(reflection)
            case Orientation.Adjacent:
                self.addAdjacent(reflection)
            case Orientation.Polar:
                self.addPolar(reflection)

    def addOrthogonal(self, reflection):
        self.orthogonal.add(reflection)
    
    def addAdjacent(self, reflection):
        self.adjacent.add(reflection)

    def addPolar(self, reflection):
        self.polar.add(reflection)


        
    # TODO: The transceiver needs to be wired up to the reflection type
    async def rcv(self, transmission): # Do we want to log who we receptioned from?
        print("  -[ Node Received: ", transmission, " ]")
        self.set_frequency = transmission
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