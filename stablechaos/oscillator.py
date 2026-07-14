# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Frustrated Kuramoto dynamics on a geometric phase lattice.

Each node carries a phase ``phi_i`` advanced by its natural frequency plus a
mean-field coupling summed over orientation classes. Orthogonal and adjacent
couplings are (by default) imitative (positive), while polar coupling is
antagonistic (negative), producing frustration. The update is a forward-Euler
step with per-class mean-field normalization, vectorized through per-class
source/target index arrays precomputed once in :meth:`PhaseLattice.__init__`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lattice import Lattice, Orientation
from .metrics import kuramoto_order

_TWO_PI: float = 2.0 * np.pi


@dataclass
class PhaseConfig:
    """Parameters controlling the phase-lattice dynamics."""

    k_orthogonal: float = 1.0
    k_adjacent: float = 0.5
    k_polar: float = -1.0
    omega_mean: float = 0.0
    omega_spread: float = 0.1
    dt: float = 0.05
    seed: int | None = None


class PhaseLattice:
    """Phase oscillators coupled by lattice orientation class."""

    def __init__(self, lattice: Lattice, config: PhaseConfig = PhaseConfig()) -> None:
        """Initialize phases, natural frequencies, and coupling index arrays."""
        self.config = config
        self.n_nodes = lattice.n_nodes
        rng = np.random.default_rng(config.seed)
        self.phases = rng.uniform(0.0, _TWO_PI, self.n_nodes)
        self.omega = rng.normal(config.omega_mean, config.omega_spread, self.n_nodes)
        self._classes = self._build_classes(lattice, config)

    def step(self) -> None:
        """Advance all phases one forward-Euler step and wrap to ``[0, 2pi)``."""
        phases = self.phases
        rate = self.omega.copy()
        for gain, src, tgt, degree in self._classes:
            interference = np.sin(phases[tgt] - phases[src])
            accumulated = np.bincount(
                src, weights=interference, minlength=self.n_nodes
            )
            rate += gain * (accumulated / degree)
        self.phases = np.mod(phases + self.config.dt * rate, _TWO_PI)

    def run(self, steps: int) -> np.ndarray:
        """Run ``steps`` updates, returning ``(steps + 1, n_nodes)`` history."""
        history = np.empty((steps + 1, self.n_nodes), dtype=np.float64)
        history[0] = self.phases
        for index in range(steps):
            self.step()
            history[index + 1] = self.phases
        return history

    def order_parameter(self) -> float:
        """Return the Kuramoto order parameter of the current phases."""
        return float(kuramoto_order(self.phases))

    def _build_classes(
        self, lattice: Lattice, config: PhaseConfig
    ) -> list[tuple[float, np.ndarray, np.ndarray, np.ndarray]]:
        """Precompute per-orientation source/target/degree arrays."""
        gains = {
            Orientation.ORTHOGONAL: config.k_orthogonal,
            Orientation.ADJACENT: config.k_adjacent,
            Orientation.POLAR: config.k_polar,
        }
        sources: dict[Orientation, list[int]] = {key: [] for key in gains}
        targets: dict[Orientation, list[int]] = {key: [] for key in gains}
        for coupling in lattice.couplings:
            sources[coupling.orientation].extend((coupling.i, coupling.j))
            targets[coupling.orientation].extend((coupling.j, coupling.i))
        classes = []
        for orientation, gain in gains.items():
            src = sources[orientation]
            if gain == 0.0 or not src:
                continue
            classes.append(self._make_class(gain, src, targets[orientation]))
        return classes

    def _make_class(
        self, gain: float, src: list[int], tgt: list[int]
    ) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
        """Build immutable index arrays and safe per-node degrees for a class."""
        src_arr = np.asarray(src, dtype=np.int64)
        tgt_arr = np.asarray(tgt, dtype=np.int64)
        degree = np.bincount(src_arr, minlength=self.n_nodes).astype(np.float64)
        degree_safe = np.where(degree == 0.0, 1.0, degree)
        return (float(gain), src_arr, tgt_arr, degree_safe)
