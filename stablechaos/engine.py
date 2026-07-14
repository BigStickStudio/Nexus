# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""The fused Stable Chaos engine: one clock, one topology, a closed loop.

This module merges the Stable Chaos Model (:mod:`stablechaos.scm`) and the
Tranception phase lattice (:mod:`stablechaos.oscillator`) into a single
dynamical system, fulfilling the legacy objective to merge the Stable Chaos
Model and Tranception for self stabilization amidst chaos.

Every node of one toroidal lattice carries BOTH a phase ``phi_i`` and an SCM
state ``s_i = (A_i, B_i)`` in ``[-1, 1]^2``. A single :meth:`StableChaosEngine.step`
advances both, coupled both ways:

* **SCM on the lattice topology** -- ``opposite(i)`` is the toroidal antipode
  (coordinate ``c -> (c + size // 2) mod size`` on every axis), ``left``/``right``
  are the ``+x`` / ``-x`` orthogonal neighbors. The per-node update is exactly the
  :mod:`stablechaos.scm` rule (half-gap-capped opposition, then imitation,
  sequential, clamped).
* **Downward coupling** -- the live ``B`` channel wanders the frequency field
  ``omega_i = omega_i0 + omega_gain * B_i`` and the frozen ``A`` pattern carves a
  spatial frustration landscape ``K_pol,i = k_polar * (1 + f * A_i) / (1 + f)``.
* **Upward coupling** -- with ``drive='phase'`` the SCM branch signs are sourced
  from the phase field itself, so the fused system is deterministic after seeded
  initialization; ``drive='random'`` restores the original seeded RNG drive as an
  ablation control.

With ``omega_gain=0`` and ``frustration_gain=0`` the phase sub-system reduces
bit-for-bit to a plain :class:`~stablechaos.oscillator.PhaseLattice`; the
composed lattice makes that equivalence exact rather than approximate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lattice import Lattice, Orientation
from .metrics import kuramoto_order
from .oscillator import PhaseConfig, PhaseLattice
from .state import STEP

_TWO_PI: float = 2.0 * np.pi
_DRIVES: tuple[str, ...] = ("phase", "random")


@dataclass
class EngineConfig:
    """Configuration for a :class:`StableChaosEngine`.

    ``size`` must be even and at least ``4`` (the toroidal antipode requires an
    even, non-degenerate ring on every axis); ``dim`` must be ``1``, ``2`` or
    ``3`` (polar frustration only exists at ``3``, but ``1``/``2`` are allowed);
    ``drive`` selects the upward coupling and ``frustration_gain`` must lie in
    ``[0, 1]``. Invalid values raise :class:`ValueError`.

    The defaults (``omega_gain=1``, ``frustration_gain=1``, ``k_polar=-1``,
    ``step=STEP``, ``drive='phase'``) are the measured sweet spot on the seed-42
    6x6x6 torus: they hold the order parameter at a sustained ``r ~ 0.23`` with
    the tightest regulation (``std(r) ~ 0.001``) and the strongest spatial
    coherence-vs-A organization (Pearson ``r ~ -0.19``). Larger ``step`` raises
    ``r`` but the faster-wandering A field washes that spatial signature out, so
    the slower legacy ``STEP`` is retained.
    """

    size: int = 6
    dim: int = 3
    k_orthogonal: float = 1.0
    k_adjacent: float = 0.5
    k_polar: float = -1.0
    omega_mean: float = 0.0
    omega_spread: float = 0.1
    dt: float = 0.05
    step: float = STEP
    omega_gain: float = 1.0
    frustration_gain: float = 1.0
    drive: str = "phase"
    opposition: bool = True
    imitation: bool = True
    seed: int | None = None

    def __post_init__(self) -> None:
        """Validate size parity, dimensionality, drive, and gain ranges."""
        if self.size < 4 or self.size % 2 != 0:
            raise ValueError(
                f"size must be even and >= 4 for the toroidal antipode, "
                f"got {self.size}"
            )
        if self.dim not in (1, 2, 3):
            raise ValueError(f"dim must be 1, 2, or 3, got {self.dim}")
        if self.drive not in _DRIVES:
            raise ValueError(f"drive must be one of {_DRIVES}, got {self.drive!r}")
        if not 0.0 <= self.frustration_gain <= 1.0:
            raise ValueError(
                f"frustration_gain must lie in [0, 1], got {self.frustration_gain}"
            )

    def phase_config(self, seed: int | None) -> PhaseConfig:
        """Return the equivalent :class:`PhaseConfig` for a given seed."""
        return PhaseConfig(
            k_orthogonal=self.k_orthogonal,
            k_adjacent=self.k_adjacent,
            k_polar=self.k_polar,
            omega_mean=self.omega_mean,
            omega_spread=self.omega_spread,
            dt=self.dt,
            seed=seed,
        )


class StableChaosEngine:
    """A fused phase-and-state lattice advanced by a single closed-loop clock."""

    def __init__(self, config: EngineConfig = EngineConfig()) -> None:
        """Build the toroidal lattice, coupling classes, and seeded fields."""
        self.config = config
        self.lattice = Lattice(config.size, config.dim, toroidal=True)
        self.n = self.lattice.n_nodes
        self._classes = self._build_classes()
        self._const_terms = self._build_const_terms()
        self._polar_present = (
            config.k_polar != 0.0 and Orientation.POLAR in self._classes
        )
        self._antipode, self._left, self._right = self._neighbor_indices()
        self.phases = np.empty(self.n, dtype=np.float64)
        self.omega0 = np.empty(self.n, dtype=np.float64)
        self.states = np.empty((self.n, 2), dtype=np.float64)
        self.t = 0
        self._rng = np.random.default_rng(config.seed)
        self._initialize(config.seed)

    def _build_classes(self) -> dict[Orientation, tuple[np.ndarray, ...]]:
        """Per-orientation ``(src, tgt, degree)`` arrays for the mean field.

        Built from ``lattice.couplings`` in the exact same order as
        :class:`PhaseLattice` (each undirected edge contributes ``(i, j)`` and
        ``(j, i)``) so the ``bincount`` accumulation is bit-identical; the polar
        gain is kept out of these arrays because it becomes spatially varying.
        """
        classes = (Orientation.ORTHOGONAL, Orientation.ADJACENT, Orientation.POLAR)
        sources: dict[Orientation, list[int]] = {o: [] for o in classes}
        targets: dict[Orientation, list[int]] = {o: [] for o in classes}
        for coupling in self.lattice.couplings:
            sources[coupling.orientation].extend((coupling.i, coupling.j))
            targets[coupling.orientation].extend((coupling.j, coupling.i))
        built: dict[Orientation, tuple[np.ndarray, ...]] = {}
        for orientation in classes:
            src = sources[orientation]
            if not src:
                continue
            src_arr = np.asarray(src, dtype=np.int64)
            tgt_arr = np.asarray(targets[orientation], dtype=np.int64)
            degree = np.bincount(src_arr, minlength=self.n).astype(np.float64)
            degree = np.where(degree == 0.0, 1.0, degree)
            built[orientation] = (src_arr, tgt_arr, degree)
        return built

    def _build_const_terms(self) -> list[tuple[Orientation, float]]:
        """Constant-gain orthogonal/adjacent terms, in PhaseLattice order."""
        candidates = (
            (Orientation.ORTHOGONAL, self.config.k_orthogonal),
            (Orientation.ADJACENT, self.config.k_adjacent),
        )
        return [
            (orientation, float(gain))
            for orientation, gain in candidates
            if gain != 0.0 and orientation in self._classes
        ]

    def _neighbor_indices(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Precompute antipode, ``+x`` (left) and ``-x`` (right) node indices."""
        size = self.config.size
        half = size // 2
        dim = self.config.dim
        antipode = np.empty(self.n, dtype=np.int64)
        left = np.empty(self.n, dtype=np.int64)
        right = np.empty(self.n, dtype=np.int64)
        for i in range(self.n):
            coord = self.lattice.coords(i)
            anti = tuple(
                (coord[ax] + half) % size if ax < dim else coord[ax]
                for ax in range(3)
            )
            left_c = ((coord[0] + 1) % size, coord[1], coord[2])
            right_c = ((coord[0] - 1) % size, coord[1], coord[2])
            antipode[i] = self.lattice.index(anti)
            left[i] = self.lattice.index(left_c)
            right[i] = self.lattice.index(right_c)
        return antipode, left, right

    def _initialize(self, seed: int | None) -> None:
        """Draw seeded phases, natural frequencies, and SCM states.

        The phase and frequency draws reuse :class:`PhaseLattice` so they are
        bit-identical to a standalone lattice run with the same seed; the SCM
        states are drawn from the engine's own generator.
        """
        plattice = PhaseLattice(self.lattice, self.config.phase_config(seed))
        self.phases = plattice.phases.copy()
        self.omega0 = plattice.omega.copy()
        self._rng = np.random.default_rng(seed)
        self.states = self._rng.uniform(-1.0, 1.0, size=(self.n, 2))
        self.t = 0

    def _drive_signs(self, phases: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return the SCM branch signs ``r_A, r_B`` in ``{-1, 0, +1}``."""
        if self.config.drive == "phase":
            r_a = np.sign(np.sin(phases - phases[self._antipode]))
            r_b = np.sign(np.sin(phases[self._left] - phases))
            return r_a, r_b
        draws = self._rng.integers(-1, 2, size=(self.n, 2)).astype(np.float64)
        return draws[:, 0], draws[:, 1]

    def _oppose(self, a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Antagonistic step against the antipode with the half-gap ``B`` cap."""
        delta = self.config.step
        opp = self._antipode
        da = delta * np.sign(a - a[opp])
        gap = b[opp] - b
        db = np.sign(gap) * np.minimum(delta, np.abs(gap) / 2.0)
        return np.clip(a + da, -1.0, 1.0), np.clip(b + db, -1.0, 1.0)

    def _imitate(
        self,
        aw: np.ndarray,
        bw: np.ndarray,
        a_old: np.ndarray,
        b_old: np.ndarray,
        r_a: np.ndarray,
        r_b: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Stochastic/phase-sourced consensus step against ring neighbors."""
        delta = self.config.step
        a_l, b_l = a_old[self._left], b_old[self._left]
        a_r, b_r = a_old[self._right], b_old[self._right]
        out_a, out_b = aw.copy(), bw.copy()
        retreat = (r_a == 1) & (r_b == 1)
        advance = (r_a == -1) & (r_b == -1)
        rest = ~(retreat | advance)
        left_move = rest & (r_a != 0)
        right_move = rest & (r_a == 0) & (r_b != 0)
        moves = (
            (retreat, aw - delta, bw - delta),
            (advance, aw + delta, bw + delta),
            (left_move, aw + delta * np.sign(np.where(r_a > 0, a_l - aw, aw - a_l)),
             bw + delta * np.sign(np.where(r_a > 0, b_l - bw, bw - b_l))),
            (right_move, aw + delta * np.sign(np.where(r_b > 0, a_r - aw, aw - a_r)),
             bw + delta * np.sign(np.where(r_b > 0, b_r - bw, bw - b_r))),
        )
        for mask, new_a, new_b in moves:
            out_a = np.where(mask, new_a, out_a)
            out_b = np.where(mask, new_b, out_b)
        return np.clip(out_a, -1.0, 1.0), np.clip(out_b, -1.0, 1.0)

    def _scm_update(
        self, a: np.ndarray, b: np.ndarray, r_a: np.ndarray, r_b: np.ndarray
    ) -> np.ndarray:
        """One synchronous SCM update, returning the ``(n, 2)`` state field."""
        aw, bw = (a.copy(), b.copy())
        if self.config.opposition:
            aw, bw = self._oppose(a, b)
        if self.config.imitation:
            aw, bw = self._imitate(aw, bw, a, b, r_a, r_b)
        return np.stack((aw, bw), axis=1)

    def _mean_field(self, phases: np.ndarray, orientation: Orientation) -> np.ndarray:
        """Per-node normalized mean-field interference for one orientation."""
        src, tgt, degree = self._classes[orientation]
        accumulated = np.bincount(
            src, weights=np.sin(phases[tgt] - phases[src]), minlength=self.n
        )
        return accumulated / degree

    def _phase_update(
        self, phases: np.ndarray, a_field: np.ndarray, b_field: np.ndarray
    ) -> np.ndarray:
        """Advance the phases one Euler step with state-modulated couplings."""
        cfg = self.config
        rate = self.omega0 + cfg.omega_gain * b_field
        for orientation, gain in self._const_terms:
            rate = rate + gain * self._mean_field(phases, orientation)
        if self._polar_present:
            k_pol = (
                cfg.k_polar
                * (1.0 + cfg.frustration_gain * a_field)
                / (1.0 + cfg.frustration_gain)
            )
            rate = rate + k_pol * self._mean_field(phases, Orientation.POLAR)
        return np.mod(phases + cfg.dt * rate, _TWO_PI)

    def step(self) -> None:
        """Advance phases and states one synchronous, closed-loop tick."""
        phases = self.phases
        a_field, b_field = self.states[:, 0], self.states[:, 1]
        r_a, r_b = self._drive_signs(phases)
        new_states = self._scm_update(a_field, b_field, r_a, r_b)
        new_phases = self._phase_update(phases, a_field, b_field)
        self.phases = new_phases
        self.states = new_states
        self.t += 1

    def run(self, steps: int) -> tuple[np.ndarray, np.ndarray]:
        """Run ``steps`` ticks, returning phase and state histories.

        The phase history has shape ``(steps + 1, n)`` and the state history
        ``(steps + 1, n, 2)``; row ``0`` is the initial condition.
        """
        if steps < 0:
            raise ValueError(f"steps must be non-negative, got {steps}")
        phase_hist = np.empty((steps + 1, self.n), dtype=np.float64)
        state_hist = np.empty((steps + 1, self.n, 2), dtype=np.float64)
        phase_hist[0] = self.phases
        state_hist[0] = self.states
        for k in range(steps):
            self.step()
            phase_hist[k + 1] = self.phases
            state_hist[k + 1] = self.states
        return phase_hist, state_hist

    def order_parameter(self) -> float:
        """Return the Kuramoto order parameter of the current phase field."""
        return float(kuramoto_order(self.phases))

    def reset(self, seed: int | None = None) -> None:
        """Reset time and re-draw fields, using ``seed`` or the configured seed."""
        active_seed = seed if seed is not None else self.config.seed
        self._initialize(active_seed)
