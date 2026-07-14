# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Generate every paper figure into ``paper/figures/`` deterministically.

No arguments are required: the seed is fixed at 42, the matplotlib backend is
forced to Agg, and each written file path is printed. The full run completes in
well under three minutes. Invoke from the repository root::

    python demos/generate_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stablechaos.lattice import Lattice
from stablechaos.metrics import kuramoto_order
from stablechaos.oscillator import PhaseConfig, PhaseLattice
from stablechaos.scm import SCMConfig, StableChaosModel
from stablechaos.viz import figures as F

SEED = 42
SCM_TICKS = 2000
LATTICE_SIZE = 6
LATTICE_DIM = 3
LATTICE_STEPS = 4000
SWEEP_STEPS = 2000
DT = 0.05
K_POLARS = (0.0, -0.5, -1.0)
FIG_DIR = Path(__file__).resolve().parents[1] / "paper" / "figures"


def _scm_runs(seed: int) -> dict[str, np.ndarray]:
    """Return T=2000 SCM trajectories for the full model and both ablations."""
    configs = {
        "full": SCMConfig(n_nodes=4, seed=seed),
        "opposition": SCMConfig(n_nodes=4, opposition=True, imitation=False, seed=seed),
        "imitation": SCMConfig(n_nodes=4, opposition=False, imitation=True, seed=seed),
    }
    return {name: StableChaosModel(cfg).run(SCM_TICKS) for name, cfg in configs.items()}


def _lattice_histories(lattice: Lattice, seed: int) -> dict[float, np.ndarray]:
    """Return phase histories for each selected polar coupling strength."""
    histories: dict[float, np.ndarray] = {}
    for k in K_POLARS:
        config = PhaseConfig(k_polar=k, dt=DT, seed=seed)
        histories[k] = PhaseLattice(lattice, config).run(LATTICE_STEPS)
    return histories


def _lattice_sweep(lattice: Lattice, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Sweep polar coupling and return (k_values, time-averaged order)."""
    k_values = np.linspace(-2.0, 0.5, 11)
    r_means = np.empty(k_values.shape, dtype=float)
    for idx, k in enumerate(k_values):
        config = PhaseConfig(k_polar=float(k), dt=DT, seed=seed)
        history = PhaseLattice(lattice, config).run(SWEEP_STEPS)
        order = kuramoto_order(history)
        cut = int(len(order) * 0.75)
        r_means[idx] = float(np.mean(order[cut:]))
    return k_values, r_means


def _z_slice(lattice: Lattice, phases: np.ndarray, z: int) -> np.ndarray:
    """Return the 2-D phase field at plane ``z`` of a 3-D lattice, indexed [y, x]."""
    field = np.zeros((lattice.size, lattice.size), dtype=float)
    for idx in range(lattice.n_nodes):
        cx, cy, cz = lattice.coords(idx)
        if cz == z:
            field[cy, cx] = float(phases[idx])
    return field


def _render(func, base: Path, *args, **kwargs) -> None:
    """Call a figure function, close its figure, and print the output paths."""
    plt.close(func(*args, out=base, **kwargs))
    for suffix in (".pdf", ".png"):
        print(base.with_suffix(suffix))


def main() -> int:
    """Produce all nine paper figures (PDF and PNG each)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    scm = _scm_runs(SEED)
    _render(F.fig_scm_trajectories, FIG_DIR / "fig_scm_trajectories", scm["full"])
    _render(F.fig_scm_phase_portrait, FIG_DIR / "fig_scm_phase_portrait", scm["full"])
    _render(F.fig_scm_ablation, FIG_DIR / "fig_scm_ablation", scm)
    _render(F.fig_scm_occupancy, FIG_DIR / "fig_scm_occupancy", scm["full"])
    lattice = Lattice(size=LATTICE_SIZE, dim=LATTICE_DIM, toroidal=True)
    histories = _lattice_histories(lattice, SEED)
    _render(F.fig_lattice_order, FIG_DIR / "fig_lattice_order", histories, DT)
    k_values, r_means = _lattice_sweep(lattice, SEED)
    _render(F.fig_lattice_sweep, FIG_DIR / "fig_lattice_sweep", k_values, r_means)
    z_mid = LATTICE_SIZE // 2
    fields = {
        "synchronized (K_polar = 0)": _z_slice(lattice, histories[0.0][-1], z_mid),
        "frustrated (K_polar = -1)": _z_slice(lattice, histories[-1.0][-1], z_mid),
    }
    _render(F.fig_lattice_phases, FIG_DIR / "fig_lattice_phases", fields)
    _render(F.fig_neighborhood, FIG_DIR / "fig_neighborhood")
    _render(F.fig_wave_superposition, FIG_DIR / "fig_wave_superposition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
