# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Diagnostics for stable-chaos trajectories and phase fields.

These functions quantify the two operational hallmarks of "stable chaos":
persistence (non-zero motion, high state-space occupancy) and boundedness
(no divergence). They operate on SCM trajectories of shape ``(T, N, 2)`` and on
oscillator phase arrays, and are pure NumPy with no side effects.
"""

from __future__ import annotations

import numpy as np


def node_variance(traj: np.ndarray) -> np.ndarray:
    """Per-tick variance across nodes, averaged over channels.

    ``traj`` has shape ``(T, N, 2)``; the result has shape ``(T,)``.
    """
    arr = np.asarray(traj, dtype=float)
    return np.var(arr, axis=1).mean(axis=1)


def mean_step_size(traj: np.ndarray, window: int | None = None) -> float:
    """Mean per-node step magnitude over the last ``window`` ticks.

    A value near zero indicates a frozen system. When ``window`` is ``None`` all
    steps are used. Returns ``0.0`` for trajectories with fewer than two ticks.
    """
    arr = np.asarray(traj, dtype=float)
    if arr.shape[0] < 2:
        return 0.0
    diffs = arr[1:] - arr[:-1]
    magnitudes = np.linalg.norm(diffs, axis=-1)
    if window is not None:
        magnitudes = magnitudes[-window:]
    return float(magnitudes.mean())


def occupancy_entropy(traj: np.ndarray, bins: int = 16) -> float:
    """Normalized Shannon entropy (nats) of the pooled ``(A, B)`` histogram.

    States are pooled over nodes and time, binned on ``[-1, 1]^2``, and the
    entropy is normalized by ``log(bins**2)`` into ``[0, 1]``. A constant
    trajectory yields ``~0``; uniform occupancy yields ``~1``.
    """
    points = np.asarray(traj, dtype=float).reshape(-1, 2)
    hist, _, _ = np.histogram2d(
        points[:, 0], points[:, 1], bins=bins, range=[[-1.0, 1.0], [-1.0, 1.0]]
    )
    counts = hist.ravel()
    counts = counts[counts > 0]
    total = counts.sum()
    if total == 0 or counts.size <= 1:
        return 0.0
    probs = counts / total
    entropy = -np.sum(probs * np.log(probs))
    return float(entropy / np.log(bins * bins))


def autocorrelation(series: np.ndarray, max_lag: int) -> np.ndarray:
    """Normalized autocorrelation of a 1-D ``series`` up to ``max_lag``.

    The result has shape ``(max_lag + 1,)`` with ``acf[0] == 1``. A constant
    series yields ``acf[0] == 1`` and zeros elsewhere.
    """
    x = np.asarray(series, dtype=float).ravel()
    x = x - x.mean()
    denom = float(np.dot(x, x))
    acf = np.zeros(max_lag + 1, dtype=float)
    acf[0] = 1.0
    if denom == 0.0:
        return acf
    for lag in range(1, max_lag + 1):
        if lag >= x.size:
            break
        acf[lag] = float(np.dot(x[:-lag], x[lag:]) / denom)
    return acf


def kuramoto_order(phases: np.ndarray) -> float | np.ndarray:
    """Kuramoto order parameter ``r = |mean(exp(i*phases))|``.

    Accepts a single frame ``(N,)`` returning a float, or a history ``(T, N)``
    returning an array of shape ``(T,)``.
    """
    arr = np.asarray(phases, dtype=float)
    mean_vector = np.mean(np.exp(1j * arr), axis=-1)
    magnitude = np.abs(mean_vector)
    if magnitude.ndim == 0:
        return float(magnitude)
    return magnitude


def acumen(states: np.ndarray) -> np.ndarray:
    """Global mean state over nodes: ``(N, 2) -> (2,)`` (legacy aggregate)."""
    return np.asarray(states, dtype=float).mean(axis=0)
