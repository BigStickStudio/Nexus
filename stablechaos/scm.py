# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""The Stable Chaos Model (SCM): an N-node ring with two coupling mechanisms.

Each node ``i`` holds a :class:`~stablechaos.state.State` ``(A_i, B_i)`` in
``[-1, 1]^2``. The update is synchronous: every node reads the tick-``t`` states
and writes the tick-``t+1`` states. Two terms combine:

* **Opposition** (antagonistic coupling): against the diametric node ``o``, the
  A-channel opposes and the B-channel follows to consensus -- the legacy
  ``State.repel`` direction, with the B step capped at half the gap so a pair
  settles at its midpoint instead of a sign-step limit cycle.
* **Imitation** (consensus coupling): a stochastic ``{-1, 0, +1}`` draw steers
  the node toward/away from its ring neighbors, or advances/retreats.

This is the symmetrized formalization of the legacy four-node prototype rules
(``Stable Chaos Model/node.py``), which were heterogeneous and
iteration-order-dependent; see ``docs/LEGACY.md``. Together the two terms yield
bounded, persistent, non-converging dynamics ("stable chaos").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .state import STEP, State, sign


@dataclass
class SCMConfig:
    """Configuration for a :class:`StableChaosModel` run.

    ``n_nodes`` must be even and at least ``4``; other values raise
    :class:`ValueError`. ``opposition`` and ``imitation`` are ablation switches.
    """

    n_nodes: int = 4
    step: float = STEP
    opposition: bool = True
    imitation: bool = True
    seed: int | None = None

    def __post_init__(self) -> None:
        """Validate the ring size (even and ``>= 4``)."""
        if self.n_nodes < 4 or self.n_nodes % 2 != 0:
            raise ValueError(
                f"n_nodes must be even and >= 4, got {self.n_nodes}"
            )


class StableChaosModel:
    """Synchronous N-node ring implementing the stable-chaos update rule."""

    def __init__(self, config: SCMConfig = SCMConfig()) -> None:
        """Build the model and draw seeded initial states."""
        self.config = config
        self.t = 0
        self._rng = np.random.default_rng(config.seed)
        self.states: list[State] = self._initial_states()

    def _initial_states(self) -> list[State]:
        """Draw ``A_i, B_i ~ Uniform(-1, 1)`` for every node."""
        draws = self._rng.uniform(-1.0, 1.0, size=(self.config.n_nodes, 2))
        return [State(float(a), float(b)) for a, b in draws]

    def _apply_opposition(self, w: State, i: int, old: list[State]) -> State:
        """Apply the antagonistic term against the diametric node.

        The A-channel opposes: ``A_i += delta * sign(A_i - A_o)``, driving the
        pair to the ``+/-1`` boundary where clamping freezes it. The B-channel
        follows to consensus: the step is ``sign(gap)`` capped at ``|gap| / 2``
        so a diametric pair meets at their midpoint and rests there. For gaps
        wider than ``2 * delta`` this equals the legacy ``delta * sign(gap)``
        step; the cap removes the legacy sign-step limit cycle so opposition
        alone truly freezes into rigid order.
        """
        n = self.config.n_nodes
        opp = old[(i + n // 2) % n]
        delta = self.config.step
        da = delta * sign(w.a - opp.a)
        gap = opp.b - w.b
        db = sign(gap) * min(delta, abs(gap) / 2.0)
        return w.moved(da, db)

    def _apply_imitation(self, w: State, i: int, old: list[State]) -> State:
        """Apply the stochastic consensus term against ring neighbors."""
        n = self.config.n_nodes
        left = old[(i + 1) % n]
        right = old[(i - 1) % n]
        r_a, r_b = (int(v) for v in self._rng.integers(-1, 2, size=2))
        delta = self.config.step
        if r_a == 1 and r_b == 1:
            return w.moved(-delta, -delta)
        if r_a == -1 and r_b == -1:
            return w.moved(delta, delta)
        if r_a != 0:
            return w.toward(left, delta) if r_a == 1 else w.away(left, delta)
        if r_b != 0:
            return w.toward(right, delta) if r_b == 1 else w.away(right, delta)
        return w

    def tick(self) -> None:
        """Advance every node by one synchronous update."""
        old = self.states
        new: list[State] = []
        for i in range(self.config.n_nodes):
            w = old[i]
            if self.config.opposition:
                w = self._apply_opposition(w, i, old)
            if self.config.imitation:
                w = self._apply_imitation(w, i, old)
            new.append(w.clamped())
        self.states = new
        self.t += 1

    def _snapshot(self) -> np.ndarray:
        """Return the current states as an ``(n_nodes, 2)`` array."""
        return np.array([s.as_tuple() for s in self.states], dtype=float)

    def run(self, ticks: int) -> np.ndarray:
        """Run ``ticks`` updates, returning ``(ticks + 1, n_nodes, 2)``.

        Row ``0`` is the initial state; row ``k`` is the state after ``k`` ticks.
        """
        if ticks < 0:
            raise ValueError(f"ticks must be non-negative, got {ticks}")
        out = np.empty((ticks + 1, self.config.n_nodes, 2), dtype=float)
        out[0] = self._snapshot()
        for k in range(ticks):
            self.tick()
            out[k + 1] = self._snapshot()
        return out

    def reset(self, seed: int | None = None) -> None:
        """Reset the tick counter, rng and states.

        Uses ``seed`` when provided, otherwise the configured seed.
        """
        active_seed = seed if seed is not None else self.config.seed
        self._rng = np.random.default_rng(active_seed)
        self.t = 0
        self.states = self._initial_states()
