# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Visualization subpackage: colors, matplotlib figures, and pygame views.

Matplotlib figure builders and color helpers are import-safe anywhere; the
pygame :class:`Viewer` and draw callbacks are the only pygame-backed code.
"""
from __future__ import annotations

from .colors import PALETTE, lerp_rgb, phase_color, state_color
from .figures import (
    fig_lattice_order,
    fig_lattice_phases,
    fig_lattice_sweep,
    fig_neighborhood,
    fig_scm_ablation,
    fig_scm_occupancy,
    fig_scm_phase_portrait,
    fig_scm_trajectories,
    fig_wave_superposition,
)
from .interactive import Viewer, draw_phase_lattice, draw_scm

__all__ = [
    "PALETTE",
    "lerp_rgb",
    "phase_color",
    "state_color",
    "Viewer",
    "draw_scm",
    "draw_phase_lattice",
    "fig_scm_trajectories",
    "fig_scm_phase_portrait",
    "fig_scm_ablation",
    "fig_scm_occupancy",
    "fig_lattice_order",
    "fig_lattice_sweep",
    "fig_lattice_phases",
    "fig_neighborhood",
    "fig_wave_superposition",
]
