# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.metrics: variance, step size, entropy, autocorr, order."""

import numpy as np
import pytest

from stablechaos.metrics import (
    acumen,
    autocorrelation,
    kuramoto_order,
    mean_step_size,
    node_variance,
    occupancy_entropy,
)


def test_node_variance_shape_and_zero() -> None:
    """node_variance returns one value per tick; identical nodes give zero."""
    traj = np.zeros((10, 4, 2))
    traj[:, :, 0] = np.arange(10)[:, None]  # identical across nodes each tick
    variance = node_variance(traj)
    assert variance.shape == (10,)
    assert np.allclose(variance, 0.0)


def test_node_variance_positive_when_nodes_differ() -> None:
    """Differing nodes yield positive per-tick variance."""
    rng = np.random.default_rng(0)
    traj = rng.uniform(-1.0, 1.0, size=(20, 6, 2))
    assert np.all(node_variance(traj) > 0.0)


def test_mean_step_size_zero_for_constant() -> None:
    """A constant trajectory has zero mean step size."""
    traj = np.full((50, 4, 2), 0.25)
    assert mean_step_size(traj) == pytest.approx(0.0)


def test_mean_step_size_window_positive() -> None:
    """A moving trajectory has a positive windowed mean step size."""
    traj = np.zeros((100, 3, 2))
    traj[:, :, 0] = np.arange(100)[:, None] * 0.01
    assert mean_step_size(traj, window=10) > 0.0


def test_occupancy_entropy_constant_is_zero() -> None:
    """All mass in a single bin gives zero normalized entropy."""
    traj = np.full((40, 5, 2), 0.1)
    assert occupancy_entropy(traj) == pytest.approx(0.0, abs=1e-9)


def test_occupancy_entropy_spread_exceeds_point() -> None:
    """A spread trajectory occupies more of state space than a point."""
    rng = np.random.default_rng(1)
    spread = rng.uniform(-1.0, 1.0, size=(500, 8, 2))
    constant = np.zeros((500, 8, 2))
    assert occupancy_entropy(spread) > occupancy_entropy(constant)


def test_autocorrelation_shape_and_zero_lag() -> None:
    """autocorrelation has length max_lag+1 and unit value at lag zero."""
    rng = np.random.default_rng(2)
    series = rng.standard_normal(200)
    acf = autocorrelation(series, max_lag=15)
    assert acf.shape == (16,)
    assert acf[0] == pytest.approx(1.0)


def test_kuramoto_order_aligned_is_one() -> None:
    """Perfectly aligned phases give order parameter one."""
    phases = np.full(50, 0.7)
    assert float(kuramoto_order(phases)) == pytest.approx(1.0)


def test_kuramoto_order_uniform_circle_is_zero() -> None:
    """Phases spread evenly around the circle give order parameter zero."""
    phases = np.linspace(0.0, 2.0 * np.pi, 200, endpoint=False)
    assert float(kuramoto_order(phases)) == pytest.approx(0.0, abs=1e-6)


def test_kuramoto_order_batched() -> None:
    """A (T, N) input yields one order value per row."""
    phases = np.zeros((4, 10))
    result = np.asarray(kuramoto_order(phases))
    assert result.shape == (4,)
    assert np.allclose(result, 1.0)


def test_acumen_is_node_mean() -> None:
    """acumen averages an (N, 2) state array over the node axis."""
    states = np.array([[1.0, 2.0], [3.0, 4.0], [-1.0, 0.0]])
    result = acumen(states)
    assert result.shape == (2,)
    assert np.allclose(result, np.array([1.0, 2.0]))
