# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Exact phasor waveform algebra.

Replaces the legacy ``Tranception/wave.py``, which round-tripped every
operation through an FFT and lost precision. Same-frequency combinations use
exact complex-phasor arithmetic; multiplication follows the legacy convention
(amplitude product, phase sum). Cross-frequency combination is handled only by
:func:`superpose`, which sums sampled signals directly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Waveform:
    """A sinusoid ``amplitude * sin(2*pi*frequency*t + phase)``."""

    amplitude: float = 1.0
    frequency: float = 1.0
    phase: float = 0.0

    def sample(
        self, duration: float, sample_rate: int = 44100
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(t, samples)`` over ``[0, duration)`` at ``sample_rate``."""
        times = np.linspace(
            0.0, duration, int(sample_rate * duration), endpoint=False
        )
        samples = self.amplitude * np.sin(
            2.0 * np.pi * self.frequency * times + self.phase
        )
        return times, samples

    def __add__(self, other: "Waveform") -> "Waveform":
        """Exact phasor sum; requires equal frequency."""
        return self._phasor(other, 1.0)

    def __sub__(self, other: "Waveform") -> "Waveform":
        """Exact phasor difference; requires equal frequency."""
        return self._phasor(other, -1.0)

    def __mul__(self, other: "Waveform") -> "Waveform":
        """Legacy product convention: amplitude product, phase sum."""
        self._require_same_frequency(other)
        return Waveform(
            self.amplitude * other.amplitude,
            self.frequency,
            self.phase + other.phase,
        )

    def resonant_frequency(self, other: "Waveform") -> float:
        """Return the shared frequency, else the geometric mean of the two."""
        if self.frequency == other.frequency:
            return float(self.frequency)
        return math.sqrt(self.frequency * other.frequency)

    def reception_level(self, other: "Waveform") -> float:
        """Return ``a1 * a2`` for equal frequency, else ``0.0``."""
        if self.frequency == other.frequency:
            return float(self.amplitude * other.amplitude)
        return 0.0

    def _phasor(self, other: "Waveform", sign: float) -> "Waveform":
        """Combine two equal-frequency phasors with ``+1`` or ``-1`` sign."""
        self._require_same_frequency(other)
        real = self.amplitude * math.cos(self.phase) + sign * (
            other.amplitude * math.cos(other.phase)
        )
        imag = self.amplitude * math.sin(self.phase) + sign * (
            other.amplitude * math.sin(other.phase)
        )
        return Waveform(math.hypot(real, imag), self.frequency, math.atan2(imag, real))

    def _require_same_frequency(self, other: "Waveform") -> None:
        """Raise :class:`ValueError` unless frequencies match exactly."""
        if self.frequency != other.frequency:
            raise ValueError(
                "waveform algebra requires equal frequencies, got "
                f"{self.frequency} and {other.frequency}"
            )


def superpose(
    waves: Sequence[Waveform], duration: float, sample_rate: int = 44100
) -> tuple[np.ndarray, np.ndarray]:
    """Sum the sampled signals of arbitrary-frequency waves over ``duration``."""
    times = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    total = np.zeros_like(times)
    for wave in waves:
        total += wave.amplitude * np.sin(
            2.0 * np.pi * wave.frequency * times + wave.phase
        )
    return times, total
