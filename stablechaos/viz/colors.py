# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Color utilities for StableChaos visualizations.

Provides the legacy state->RGB mapping, a phase->RGB HSV wheel, an RGB
interpolation helper, and a named palette shared by matplotlib figures and the
pygame interactive views.
"""
from __future__ import annotations

import colorsys
import math

RGB = tuple[int, int, int]

PALETTE: dict[str, RGB] = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "OUTLINE": (33, 33, 33),
    "BG": (222, 222, 222),
}


def _clamp01(t: float) -> float:
    """Clamp ``t`` into the closed interval [0, 1]."""
    if t < 0.0:
        return 0.0
    if t > 1.0:
        return 1.0
    return t


def lerp_rgb(c1: RGB, c2: RGB, t: float) -> RGB:
    """Linearly interpolate between two RGB colors.

    ``t`` is clamped to [0, 1]; ``t=0`` yields ``c1`` and ``t=1`` yields ``c2``.
    """
    t = _clamp01(t)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def state_color(a: float, b: float) -> RGB:
    """Map a node state ``(a, b)`` in ``[-1, 1]^2`` to an RGB color.

    Reproduces the legacy mapping: blend a WHITE->BLUE ramp on ``a`` with a
    BLACK->RED ramp on ``b``, mixed by the mean of the two channels.
    """
    a_color = lerp_rgb(PALETTE["WHITE"], PALETTE["BLUE"], (a + 1.0) / 2.0)
    b_color = lerp_rgb(PALETTE["BLACK"], PALETTE["RED"], (b + 1.0) / 2.0)
    return lerp_rgb(a_color, b_color, (a + b + 2.0) / 4.0)


def phase_color(phi: float) -> RGB:
    """Map a phase angle (radians) to an RGB color on the HSV wheel.

    Hue is ``phi / (2*pi)`` wrapped to [0, 1); saturation and value are 1.
    """
    hue = (phi / (2.0 * math.pi)) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))
