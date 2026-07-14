# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""StableChaos: bounded, persistent dynamics from antagonistic + imitative coupling.

This package unifies two demonstrations of "stable chaos" -- trajectories that
never settle to a fixed point yet never diverge:

* the **Stable Chaos Model** (:mod:`stablechaos.scm`), an N-node stochastic ring;
* the **Tranception phase lattice** (:mod:`stablechaos.oscillator`,
  :mod:`stablechaos.lattice`), a frustrated Kuramoto lattice.

Shared diagnostics live in :mod:`stablechaos.metrics` and the waveform algebra in
:mod:`stablechaos.waveform`. "All of my ideas, converging into one."
"""

from __future__ import annotations

from .lattice import Lattice, Orientation
from .metrics import (
    acumen,
    autocorrelation,
    kuramoto_order,
    mean_step_size,
    node_variance,
    occupancy_entropy,
)
from .oscillator import PhaseConfig, PhaseLattice
from .scm import SCMConfig, StableChaosModel
from .state import STEP, State, sign
from .waveform import Waveform, superpose

__version__ = "1.0.0"

__all__ = [
    "State",
    "STEP",
    "sign",
    "SCMConfig",
    "StableChaosModel",
    "Lattice",
    "Orientation",
    "PhaseConfig",
    "PhaseLattice",
    "Waveform",
    "superpose",
    "node_variance",
    "mean_step_size",
    "occupancy_entropy",
    "autocorrelation",
    "kuramoto_order",
    "acumen",
    "__version__",
]
