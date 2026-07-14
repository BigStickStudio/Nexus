# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Matplotlib figure builders for StableChaos (headless-safe, no ``plt.show``).

Every ``fig_*`` function returns the :class:`matplotlib.figure.Figure` it builds
and, when ``out`` is given, writes both ``<out>.pdf`` and ``<out>.png`` at
dpi=200. Styling is consistent: a colorblind-safe line cycle, tight layout, and
no seaborn dependency.
"""
from __future__ import annotations

import itertools
from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import mpl_toolkits.mplot3d  # noqa: F401  (registers the '3d' projection)

from ..metrics import node_variance, occupancy_entropy, kuramoto_order
from ..lattice import classify, Orientation
from ..waveform import Waveform, superpose
from .colors import phase_color

# Colorblind-safe palette (Wong, 2011), ordered for contrast on white.
_WONG: list[str] = [
    "#000000", "#0072B2", "#D55E00", "#009E73",
    "#CC79A7", "#E69F00", "#56B4E9", "#F0E442",
]

plt.rcParams.update({
    "axes.prop_cycle": plt.cycler(color=_WONG),
    "font.size": 10,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def _save(fig: Figure, out: Path | str | None) -> None:
    """Write ``fig`` to ``<out>.pdf`` and ``<out>.png`` when ``out`` is set."""
    if out is None:
        return
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"), dpi=200)
    fig.savefig(path.with_suffix(".png"), dpi=200)


def fig_scm_trajectories(traj: np.ndarray, out: Path | str | None = None) -> Figure:
    """Plot A_i(t) and B_i(t) for every node on two stacked axes."""
    ticks = np.arange(traj.shape[0])
    n_nodes = traj.shape[1]
    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    for i in range(n_nodes):
        ax_a.plot(ticks, traj[:, i, 0], lw=1.0, label=f"node {i}")
        ax_b.plot(ticks, traj[:, i, 1], lw=1.0)
    for axis, name in ((ax_a, "A"), (ax_b, "B")):
        axis.set_ylabel(name)
        axis.set_ylim(-1.05, 1.05)
        axis.grid(True, alpha=0.3)
    ax_b.set_xlabel("tick")
    ax_a.set_title("SCM node trajectories")
    ax_a.legend(loc="upper right", ncol=n_nodes, fontsize=8)
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_scm_phase_portrait(traj: np.ndarray, out: Path | str | None = None) -> Figure:
    """Plot each node's (A, B) path with start (circle) and end (square) markers."""
    n_nodes = traj.shape[1]
    fig, ax = plt.subplots(figsize=(6, 6))
    for i in range(n_nodes):
        a = traj[:, i, 0]
        b = traj[:, i, 1]
        line, = ax.plot(a, b, lw=0.6, alpha=0.7, label=f"node {i}")
        ax.plot(a[0], b[0], marker="o", color=line.get_color(), ms=7)
        ax.plot(a[-1], b[-1], marker="s", color=line.get_color(), ms=7)
    ax.set_xlabel("A")
    ax.set_ylabel("B")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_title("SCM phase portrait")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_scm_ablation(trajs: dict[str, np.ndarray], out: Path | str | None = None) -> Figure:
    """Compare node-variance curves and occupancy entropy across ablations."""
    order = ["full", "imitation", "opposition"]
    fig, (ax_v, ax_e) = plt.subplots(1, 2, figsize=(11, 4.5))
    labels: list[str] = []
    entropies: list[float] = []
    for key in order:
        if key not in trajs:
            continue
        variance = node_variance(trajs[key])
        ax_v.plot(np.arange(variance.shape[0]), variance, label=key)
        labels.append(key)
        entropies.append(occupancy_entropy(trajs[key]))
    ax_v.set_xlabel("tick")
    ax_v.set_ylabel("node variance")
    ax_v.set_title("Cross-node variance")
    ax_v.grid(True, alpha=0.3)
    ax_v.legend(fontsize=8)
    ax_e.bar(labels, entropies, color=_WONG[: len(labels)])
    ax_e.set_ylabel("occupancy entropy")
    ax_e.set_ylim(0.0, 1.0)
    ax_e.set_title("State-space occupancy")
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_scm_occupancy(
    traj: np.ndarray, out: Path | str | None = None, bins: int = 48
) -> Figure:
    """Draw the (A, B) occupancy heatmap pooled over nodes and time."""
    a = traj[..., 0].ravel()
    b = traj[..., 1].ravel()
    fig, ax = plt.subplots(figsize=(6, 5))
    _, _, _, mesh = ax.hist2d(
        a, b, bins=bins, range=[[-1.0, 1.0], [-1.0, 1.0]], cmap="magma"
    )
    fig.colorbar(mesh, ax=ax, label="count")
    ax.set_xlabel("A")
    ax.set_ylabel("B")
    ax.set_aspect("equal")
    ax.set_title("SCM state-space occupancy")
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_lattice_order(
    histories: dict[float, np.ndarray], dt: float, out: Path | str | None = None
) -> Figure:
    """Plot the Kuramoto order parameter r(t) for each frustration strength."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for k_polar in sorted(histories):
        order = kuramoto_order(histories[k_polar])
        times = np.arange(order.shape[0]) * dt
        ax.plot(times, order, lw=1.2, label=f"K_polar = {k_polar:g}")
    ax.set_xlabel("time")
    ax.set_ylabel("order parameter r")
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.set_title("Phase-lattice synchronization")
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_lattice_sweep(
    k_values: Sequence[float], r_means: Sequence[float], out: Path | str | None = None
) -> Figure:
    """Plot mean order parameter vs the polar (frustration) coupling strength."""
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(k_values, r_means, marker="o", lw=1.5)
    ax.set_xlabel("K_polar")
    ax.set_ylabel(r"$\langle r \rangle$")
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.set_title("Order parameter vs frustration")
    fig.tight_layout()
    _save(fig, out)
    return fig


def _phase_image(field: np.ndarray) -> np.ndarray:
    """Map a 2-D array of phases to an RGB image via the phase color wheel."""
    height, width = field.shape
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            image[y, x] = phase_color(float(field[y, x]))
    return image


def fig_lattice_phases(
    fields: dict[str, np.ndarray], out: Path | str | None = None
) -> Figure:
    """Render labeled 2-D phase-field slices side by side, colored by phase."""
    names = list(fields)
    fig, axes = plt.subplots(1, len(names), figsize=(5.0 * len(names), 5.0))
    axis_list = list(np.atleast_1d(axes).ravel())
    for ax, name in zip(axis_list, names):
        ax.imshow(_phase_image(np.asarray(fields[name])),
                  origin="lower", interpolation="nearest")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(name)
    fig.suptitle(r"Phase field (hue = phase in $[0, 2\pi)$)")
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_neighborhood(out: Path | str | None = None) -> Figure:
    """Scatter the 26-neighborhood offsets colored by orientation class."""
    styles = {
        Orientation.ORTHOGONAL: ("#0072B2", "o", "orthogonal (6)"),
        Orientation.ADJACENT: ("#E69F00", "^", "adjacent (12)"),
        Orientation.POLAR: ("#D55E00", "s", "polar (8)"),
    }
    groups: dict[Orientation, list[tuple[int, int, int]]] = {k: [] for k in styles}
    for offset in itertools.product((-1, 0, 1), repeat=3):
        orientation = classify(offset)
        if orientation in groups:
            groups[orientation].append(offset)
    fig = plt.figure(figsize=(6.5, 6))
    ax = fig.add_subplot(111, projection="3d")
    for orientation, (color, marker, label) in styles.items():
        pts = np.array(groups[orientation])
        ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=color, marker=marker, s=90, label=label)
    ax.scatter([0], [0], [0], c="#000000", marker="*", s=140, label="self")
    ax.set_xlabel("dx")
    ax.set_ylabel("dy")
    ax.set_zlabel("dz")
    ax.set_title("26-neighborhood orientation classes")
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, out)
    return fig


def fig_wave_superposition(out: Path | str | None = None) -> Figure:
    """Show two near-frequency waves and their beating superposition."""
    duration = 2.0
    rate = 2000
    w1 = Waveform(amplitude=1.0, frequency=5.0, phase=0.0)
    w2 = Waveform(amplitude=1.0, frequency=6.0, phase=0.0)
    times, summed = superpose([w1, w2], duration, sample_rate=rate)
    _, y1 = w1.sample(duration, sample_rate=rate)
    _, y2 = w2.sample(duration, sample_rate=rate)
    beat_rate = abs(w2.frequency - w1.frequency) / 2.0
    envelope = (w1.amplitude + w2.amplitude) * np.abs(np.cos(2.0 * np.pi * beat_rate * times))
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax_top.plot(times, y1, lw=1.0, label="f1 = 5 Hz")
    ax_top.plot(times, y2, lw=1.0, label="f2 = 6 Hz")
    ax_bot.plot(times, summed, lw=1.0, label="superposition")
    ax_bot.plot(times, envelope, "--", color="#D55E00", lw=1.2, label="beat envelope")
    ax_bot.plot(times, -envelope, "--", color="#D55E00", lw=1.2)
    for axis in (ax_top, ax_bot):
        axis.grid(True, alpha=0.3)
        axis.legend(fontsize=8, loc="upper right")
    ax_bot.set_xlabel("time (s)")
    ax_top.set_ylabel("amplitude")
    ax_bot.set_ylabel("amplitude")
    ax_top.set_title("Waveform superposition and beating")
    fig.tight_layout()
    _save(fig, out)
    return fig
