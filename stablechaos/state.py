# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Two-channel node state for the Stable Chaos Model.

Each node carries a state ``(a, b)`` confined to the square ``[-1, 1]^2``.
The :class:`State` value object is immutable in spirit: every transformation
returns a new, clamped :class:`State`. This formalizes the legacy
``Stable Chaos Model/state.py`` prototype (``addA``/``minusB``/``repel``) with
a single ``STEP`` increment and componentwise ``sign`` logic.
"""

from __future__ import annotations

from dataclasses import dataclass

STEP: float = 0.0987
"""Legacy per-tick increment constant, preserved exactly."""


def sign(x: float) -> float:
    """Return the sign of ``x`` as ``-1.0``, ``0.0`` or ``1.0``."""
    if x > 0.0:
        return 1.0
    if x < 0.0:
        return -1.0
    return 0.0


def _clamp(value: float) -> float:
    """Clamp a scalar to the closed interval ``[-1, 1]``."""
    return max(-1.0, min(1.0, value))


@dataclass
class State:
    """A node state ``(a, b)`` in the square ``[-1, 1]^2``."""

    a: float = 0.0
    b: float = 0.0

    def clamped(self) -> "State":
        """Return a copy with both channels clamped to ``[-1, 1]``."""
        return State(_clamp(self.a), _clamp(self.b))

    def moved(self, da: float, db: float) -> "State":
        """Return a new clamped state offset by ``(da, db)``."""
        return State(_clamp(self.a + da), _clamp(self.b + db))

    def toward(self, other: "State", step: float = STEP) -> "State":
        """Move ``step`` toward ``other`` componentwise (sign of difference)."""
        return self.moved(
            step * sign(other.a - self.a),
            step * sign(other.b - self.b),
        )

    def away(self, other: "State", step: float = STEP) -> "State":
        """Move ``step`` away from ``other`` componentwise (sign of difference)."""
        return self.moved(
            step * sign(self.a - other.a),
            step * sign(self.b - other.b),
        )

    def as_tuple(self) -> tuple[float, float]:
        """Return the state as a plain ``(a, b)`` tuple."""
        return (self.a, self.b)
