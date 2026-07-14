# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.scm: shape, bounds, determinism, validation, ablation."""

import numpy as np
import pytest

from stablechaos.metrics import mean_step_size, occupancy_entropy
from stablechaos.scm import SCMConfig, StableChaosModel

TICKS = 2000
WINDOW = 200


@pytest.fixture(scope="module")
def full_traj() -> np.ndarray:
    """Trajectory of the full model (opposition + imitation)."""
    config = SCMConfig(n_nodes=4, opposition=True, imitation=True, seed=7)
    return StableChaosModel(config).run(TICKS)


@pytest.fixture(scope="module")
def opposition_traj() -> np.ndarray:
    """Trajectory of the opposition-only ablation."""
    config = SCMConfig(n_nodes=4, opposition=True, imitation=False, seed=7)
    return StableChaosModel(config).run(TICKS)


def test_run_shape() -> None:
    """run(ticks) includes the initial state: shape (ticks+1, n, 2)."""
    traj = StableChaosModel(SCMConfig(n_nodes=4, seed=0)).run(50)
    assert traj.shape == (51, 4, 2)


def test_run_stays_in_bounds(full_traj: np.ndarray) -> None:
    """All states remain within the clamped domain [-1, 1]^2."""
    assert full_traj.min() >= -1.0 - 1e-9
    assert full_traj.max() <= 1.0 + 1e-9


def test_exposed_attributes() -> None:
    """The model exposes states, config and an advancing tick counter."""
    model = StableChaosModel(SCMConfig(n_nodes=6, seed=0))
    assert model.t == 0
    assert len(model.states) == 6
    assert model.config.n_nodes == 6
    model.tick()
    assert model.t == 1


def test_same_seed_is_deterministic() -> None:
    """Identical seeds reproduce identical trajectories."""
    a = StableChaosModel(SCMConfig(n_nodes=4, seed=42)).run(100)
    b = StableChaosModel(SCMConfig(n_nodes=4, seed=42)).run(100)
    assert np.array_equal(a, b)


def test_different_seed_differs() -> None:
    """Different seeds produce different trajectories."""
    a = StableChaosModel(SCMConfig(n_nodes=4, seed=1)).run(100)
    b = StableChaosModel(SCMConfig(n_nodes=4, seed=2)).run(100)
    assert not np.array_equal(a, b)


def test_reset_reproduces_with_same_seed() -> None:
    """reset(seed) restores a reproducible starting point."""
    model = StableChaosModel(SCMConfig(n_nodes=4, seed=5))
    first = model.run(60)
    model.reset(seed=5)
    second = model.run(60)
    assert np.array_equal(first, second)


def test_odd_node_count_raises() -> None:
    """An odd node count is invalid."""
    with pytest.raises(ValueError):
        StableChaosModel(SCMConfig(n_nodes=5))


def test_too_small_node_count_raises() -> None:
    """Fewer than four nodes is invalid."""
    with pytest.raises(ValueError):
        StableChaosModel(SCMConfig(n_nodes=2))


def test_full_model_stays_live(full_traj: np.ndarray) -> None:
    """With imitation the full model keeps moving and never freezes."""
    assert mean_step_size(full_traj, window=WINDOW) > 0.01


def test_opposition_freezes_a_channel(opposition_traj: np.ndarray) -> None:
    """Opposition saturates the antagonistic A-channel (|A| -> 1) AND freezes
    the dynamics: the capped rule drives the tail step size to ~0."""
    tail_a = np.abs(opposition_traj[-WINDOW:, :, 0])
    assert float(np.mean(tail_a)) > 0.9
    assert mean_step_size(opposition_traj, window=WINDOW) < 0.002


def test_full_explores_more_than_opposition(
    full_traj: np.ndarray, opposition_traj: np.ndarray
) -> None:
    """The full model occupies more of state space than opposition alone."""
    assert occupancy_entropy(full_traj) > occupancy_entropy(opposition_traj)
