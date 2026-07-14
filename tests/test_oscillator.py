# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.oscillator: synchronisation, frustration, bounds, shape."""

import numpy as np

from stablechaos.lattice import Lattice
from stablechaos.oscillator import PhaseConfig, PhaseLattice

TWO_PI = 2.0 * np.pi


def _row_order(phases: np.ndarray) -> float:
    """Kuramoto order parameter of a single 1-D phase array."""
    return float(np.abs(np.mean(np.exp(1j * phases))))


def _tail_mean_order(history: np.ndarray, tail: int) -> float:
    """Mean Kuramoto order over the last `tail` recorded rows."""
    rows = history[-tail:]
    return float(np.mean([_row_order(row) for row in rows]))


def test_run_shape_and_bounds() -> None:
    """run(steps) returns (steps+1, n) with finite phases wrapped to [0, 2*pi)."""
    lattice = Lattice(4, 2, toroidal=True)
    plattice = PhaseLattice(lattice, PhaseConfig(seed=3, dt=0.05))
    history = plattice.run(200)
    assert history.shape == (201, lattice.n_nodes)
    assert np.all(np.isfinite(history))
    assert np.all(history >= -1e-12)
    assert np.all(history < TWO_PI + 1e-9)


def test_order_parameter_is_valid_fraction() -> None:
    """order_parameter returns a scalar in [0, 1]."""
    lattice = Lattice(4, 2, toroidal=True)
    plattice = PhaseLattice(lattice, PhaseConfig(seed=1))
    plattice.run(50)
    value = float(plattice.order_parameter())
    assert 0.0 <= value <= 1.0


def test_identical_frequencies_synchronise() -> None:
    """Positive coupling with identical natural frequencies drives r -> 1."""
    lattice = Lattice(8, 2, toroidal=True)
    config = PhaseConfig(
        k_orthogonal=1.0,
        k_adjacent=0.5,
        k_polar=0.0,
        omega_mean=0.0,
        omega_spread=0.0,
        dt=0.05,
        seed=0,
    )
    history = PhaseLattice(lattice, config).run(3000)
    assert _row_order(history[-1]) > 0.95


def test_polar_frustration_suppresses_order() -> None:
    """Strong negative polar coupling frustrates synchronisation on a 3-D torus."""
    lattice = Lattice(6, 3, toroidal=True)
    base = dict(
        k_orthogonal=1.0,
        k_adjacent=0.5,
        omega_mean=0.0,
        omega_spread=0.0,
        dt=0.05,
        seed=0,
    )
    frustrated = PhaseLattice(lattice, PhaseConfig(k_polar=-1.5, **base)).run(3000)
    aligned = PhaseLattice(lattice, PhaseConfig(k_polar=0.0, **base)).run(3000)
    frustrated_order = _tail_mean_order(frustrated, 500)
    aligned_order = _tail_mean_order(aligned, 500)
    assert frustrated_order < 0.8
    assert aligned_order > frustrated_order
