# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.lattice: classification, neighbour counts, indexing."""

from stablechaos.lattice import Coupling, Lattice, Orientation, classify

ORTH = Orientation.ORTHOGONAL
ADJ = Orientation.ADJACENT
POLAR = Orientation.POLAR


def _find_coord(lattice: Lattice, target: tuple[int, int, int]) -> int:
    """Return the node index whose 3-D coordinate equals target."""
    for idx in range(lattice.n_nodes):
        if tuple(lattice.coords(idx)) == target:
            return idx
    raise AssertionError(f"coordinate {target} not present")


def _find_interior(lattice: Lattice, size: int, dim: int) -> int:
    """Return an interior node index (active coordinates off the boundary)."""
    for idx in range(lattice.n_nodes):
        coord = lattice.coords(idx)
        if all(0 < coord[k] < size - 1 for k in range(dim)):
            return idx
    raise AssertionError("no interior node found")


def _counts(lattice: Lattice, idx: int) -> tuple[int, int, int]:
    """Return (orthogonal, adjacent, polar) neighbour counts for a node."""
    return (
        len(lattice.neighbors(idx, ORTH)),
        len(lattice.neighbors(idx, ADJ)),
        len(lattice.neighbors(idx, POLAR)),
    )


def test_classify_by_squared_distance() -> None:
    """Offsets are classified by squared distance within the 27-neighbourhood."""
    assert classify((0, 0, 0)) is Orientation.SELF
    assert classify((1, 0, 0)) is ORTH
    assert classify((1, 1, 0)) is ADJ
    assert classify((1, 1, 1)) is POLAR


def test_classify_outside_neighborhood_is_none() -> None:
    """Offsets beyond the 27-neighbourhood classify to None."""
    assert classify((2, 0, 0)) is None
    assert classify((1, 1, 2)) is None


def test_n_nodes() -> None:
    """Node count equals size ** dim for each dimension."""
    assert Lattice(5, 1).n_nodes == 5
    assert Lattice(5, 2).n_nodes == 25
    assert Lattice(3, 3).n_nodes == 27


def test_index_coords_roundtrip() -> None:
    """index and coords are mutual inverses in every dimension."""
    for lattice in (Lattice(5, 1), Lattice(4, 2), Lattice(3, 3)):
        for idx in range(lattice.n_nodes):
            assert lattice.index(lattice.coords(idx)) == idx


def test_center_node_3d() -> None:
    """The 3x3x3 centre node has 6/12/8 orthogonal/adjacent/polar neighbours."""
    lattice = Lattice(3, 3)
    center = _find_coord(lattice, (1, 1, 1))
    assert _counts(lattice, center) == (6, 12, 8)


def test_corner_node_3d() -> None:
    """A 3x3x3 corner node has 3/3/1 orthogonal/adjacent/polar neighbours."""
    lattice = Lattice(3, 3)
    corner = _find_coord(lattice, (0, 0, 0))
    assert _counts(lattice, corner) == (3, 3, 1)


def test_toroidal_uniform_3d() -> None:
    """Every node of a toroidal 3x3x3 lattice has 6/12/8 neighbours."""
    lattice = Lattice(3, 3, toroidal=True)
    for idx in range(lattice.n_nodes):
        assert _counts(lattice, idx) == (6, 12, 8)


def test_interior_counts_1d_and_2d() -> None:
    """Interior nodes match the per-dimension neighbourhood decomposition."""
    line = Lattice(5, 1)
    grid = Lattice(5, 2)
    assert _counts(line, _find_interior(line, 5, 1)) == (2, 0, 0)
    assert _counts(grid, _find_interior(grid, 5, 2)) == (4, 4, 0)


def test_counts_totals_match_neighbor_sums() -> None:
    """counts() equals the summed directed neighbour counts halved."""
    lattice = Lattice(3, 3)
    totals = lattice.counts()
    for orientation in (ORTH, ADJ, POLAR):
        directed = sum(
            len(lattice.neighbors(idx, orientation)) for idx in range(lattice.n_nodes)
        )
        assert directed % 2 == 0
        assert totals.get(orientation, 0) == directed // 2


def test_couplings_are_ordered_and_non_self() -> None:
    """Undirected couplings use i < j and never carry the SELF class."""
    lattice = Lattice(4, 2)
    assert lattice.couplings
    for coupling in lattice.couplings:
        assert isinstance(coupling, Coupling)
        assert coupling.i < coupling.j
        assert coupling.orientation is not Orientation.SELF


def test_counts_1d_and_2d_totals() -> None:
    """Total coupling counts match the closed-form edge and diagonal counts."""
    line = Lattice(5, 1)
    grid = Lattice(3, 2)
    assert line.counts().get(ORTH, 0) == 4
    assert line.counts().get(ADJ, 0) == 0
    assert line.counts().get(POLAR, 0) == 0
    assert grid.counts().get(ORTH, 0) == 12
    assert grid.counts().get(ADJ, 0) == 8
    assert grid.counts().get(POLAR, 0) == 0
