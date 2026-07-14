# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Geometric phase lattice: nodes, orientation classes, and couplings.

Formalizes the legacy ``Tranception`` mesh. Neighbors of a node are the cells
in its ``{-1, 0, 1}^dim`` offset shell, classified by squared Euclidean
distance into orientation classes:

* ``SELF``       squared distance 0
* ``ORTHOGONAL`` squared distance 1 (face neighbors, up to 6 in 3D)
* ``ADJACENT``   squared distance 2 (edge neighbors, up to 12 in 3D)
* ``POLAR``      squared distance 3 (corner neighbors, up to 8 in 3D)

An interior 3D node therefore has 6 + 12 + 8 = 26 neighbors. ``toroidal=True``
wraps coordinates modulo ``size`` (completing the toroidal wrap left
unimplemented in the prototype).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product


class Orientation(Enum):
    """Neighbor class keyed by squared Euclidean distance (0, 1, 2, 3)."""

    SELF = 0
    ORTHOGONAL = 1
    ADJACENT = 2
    POLAR = 3


def classify(offset: tuple[int, int, int]) -> Orientation | None:
    """Classify a 3D integer offset by squared distance.

    Returns the matching :class:`Orientation`, or ``None`` when the offset
    falls outside the 27-cell neighborhood (any component magnitude > 1, or
    squared distance > 3).
    """
    if any(abs(component) > 1 for component in offset):
        return None
    squared = sum(component * component for component in offset)
    if squared > 3:
        return None
    return Orientation(squared)


@dataclass(frozen=True)
class Coupling:
    """Undirected coupling between two distinct nodes with ``i < j``."""

    i: int
    j: int
    orientation: Orientation


_LINK_CLASSES: tuple[Orientation, ...] = (
    Orientation.ORTHOGONAL,
    Orientation.ADJACENT,
    Orientation.POLAR,
)


class Lattice:
    """A ``dim``-dimensional cubic lattice of ``size**dim`` nodes."""

    def __init__(self, size: int, dim: int, toroidal: bool = False) -> None:
        """Build the lattice and precompute couplings and neighbor lists."""
        if dim not in (1, 2, 3):
            raise ValueError(f"dim must be 1, 2, or 3, got {dim}")
        if size < 1:
            raise ValueError(f"size must be >= 1, got {size}")
        self.size = int(size)
        self.dim = int(dim)
        self.toroidal = bool(toroidal)
        self.n_nodes = self.size**self.dim
        self._neighbor_map: list[dict[Orientation, list[int]]] = []
        self.couplings: list[Coupling] = []
        self._build()

    def coords(self, idx: int) -> tuple[int, int, int]:
        """Return the ``(x, y, z)`` coordinate of node ``idx`` (z-padded)."""
        result = [0, 0, 0]
        for axis in range(self.dim):
            result[axis] = (idx // (self.size**axis)) % self.size
        return (result[0], result[1], result[2])

    def index(self, coord: tuple[int, ...]) -> int:
        """Return the flat node index for ``coord`` (x fastest-varying)."""
        idx = 0
        multiplier = 1
        for axis in range(self.dim):
            idx += coord[axis] * multiplier
            multiplier *= self.size
        return idx

    def neighbors(self, idx: int, orientation: Orientation) -> list[int]:
        """Return neighbor indices of ``idx`` in the given orientation class."""
        if orientation is Orientation.SELF:
            return []
        return list(self._neighbor_map[idx][orientation])

    def counts(self) -> dict[Orientation, int]:
        """Return the total number of unique couplings per orientation class."""
        totals = {orientation: 0 for orientation in _LINK_CLASSES}
        for coupling in self.couplings:
            totals[coupling.orientation] += 1
        return totals

    def _neighbor_offsets(self) -> list[tuple[tuple[int, int, int], Orientation]]:
        """Enumerate non-self offsets and their orientation classes."""
        offsets: list[tuple[tuple[int, int, int], Orientation]] = []
        for combo in product((-1, 0, 1), repeat=self.dim):
            offset = combo + (0,) * (3 - self.dim)
            orientation = classify(offset)
            if orientation is None or orientation is Orientation.SELF:
                continue
            offsets.append((offset, orientation))
        return offsets

    def _shift(
        self, coord: tuple[int, int, int], offset: tuple[int, int, int]
    ) -> tuple[int, int, int] | None:
        """Apply ``offset`` to ``coord``; wrap or reject at the boundary."""
        shifted = []
        for value, delta in zip(coord, offset):
            moved = value + delta
            if self.toroidal:
                moved %= self.size
            elif not 0 <= moved < self.size:
                return None
            shifted.append(moved)
        return (shifted[0], shifted[1], shifted[2])

    def _build(self) -> None:
        """Populate neighbor lists and the unique coupling set."""
        offsets = self._neighbor_offsets()
        raw: list[dict[Orientation, set[int]]] = [
            {orientation: set() for orientation in _LINK_CLASSES}
            for _ in range(self.n_nodes)
        ]
        couplings: set[Coupling] = set()
        for idx in range(self.n_nodes):
            base = self.coords(idx)
            for offset, orientation in offsets:
                neighbor = self._shift(base, offset)
                if neighbor is None:
                    continue
                j = self.index(neighbor)
                if j == idx:
                    continue
                raw[idx][orientation].add(j)
                couplings.add(Coupling(min(idx, j), max(idx, j), orientation))
        self._neighbor_map = [
            {orientation: sorted(members) for orientation, members in node.items()}
            for node in raw
        ]
        self.couplings = sorted(
            couplings, key=lambda c: (c.i, c.j, c.orientation.value)
        )
