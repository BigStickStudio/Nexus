# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.waveform: phasor algebra, resonance, superposition."""

import numpy as np
import pytest

from stablechaos.waveform import Waveform, superpose


def _phasor(wave: Waveform) -> complex:
    """Complex phasor amplitude * exp(i * phase) of a waveform."""
    return complex(wave.amplitude * np.exp(1j * wave.phase))


def _assert_complex_close(actual: complex, expected: complex) -> None:
    """Assert two phasors agree in real and imaginary parts."""
    assert actual.real == pytest.approx(expected.real)
    assert actual.imag == pytest.approx(expected.imag)


def test_equal_frequency_addition_is_phasor_sum() -> None:
    """Same-frequency addition follows exact phasor (hypot/atan2) algebra."""
    w1 = Waveform(amplitude=1.0, frequency=2.0, phase=0.3)
    w2 = Waveform(amplitude=0.7, frequency=2.0, phase=1.1)
    result = w1 + w2
    expected = _phasor(w1) + _phasor(w2)
    assert result.frequency == pytest.approx(2.0)
    assert result.amplitude == pytest.approx(np.hypot(expected.real, expected.imag))
    _assert_complex_close(_phasor(result), expected)


def test_equal_frequency_subtraction_is_phasor_difference() -> None:
    """Same-frequency subtraction follows exact phasor algebra."""
    w1 = Waveform(amplitude=1.2, frequency=3.0, phase=0.4)
    w2 = Waveform(amplitude=0.5, frequency=3.0, phase=2.0)
    result = w1 - w2
    expected = _phasor(w1) - _phasor(w2)
    assert result.frequency == pytest.approx(3.0)
    _assert_complex_close(_phasor(result), expected)


def test_multiplication_convention() -> None:
    """Same-frequency product multiplies amplitudes and sums phases."""
    w1 = Waveform(amplitude=1.5, frequency=4.0, phase=0.3)
    w2 = Waveform(amplitude=2.0, frequency=4.0, phase=0.4)
    result = w1 * w2
    assert result.frequency == pytest.approx(4.0)
    assert result.amplitude == pytest.approx(3.0)
    _assert_complex_close(_phasor(result), complex(3.0 * np.exp(1j * 0.7)))


def test_mismatched_frequency_add_raises() -> None:
    """Adding waves of different frequency is undefined and raises."""
    with pytest.raises(ValueError):
        Waveform(frequency=1.0) + Waveform(frequency=2.0)


def test_mismatched_frequency_sub_raises() -> None:
    """Subtracting waves of different frequency raises."""
    with pytest.raises(ValueError):
        Waveform(frequency=1.0) - Waveform(frequency=2.0)


def test_resonant_frequency() -> None:
    """Equal frequency resonates at f; otherwise the geometric mean."""
    equal = Waveform(frequency=5.0).resonant_frequency(Waveform(frequency=5.0))
    assert equal == pytest.approx(5.0)
    mixed = Waveform(frequency=2.0).resonant_frequency(Waveform(frequency=8.0))
    assert mixed == pytest.approx(np.sqrt(2.0 * 8.0))


def test_reception_level() -> None:
    """Equal frequency couples as an amplitude product; otherwise zero."""
    matched = Waveform(amplitude=1.5, frequency=3.0)
    other = Waveform(amplitude=2.0, frequency=3.0)
    assert matched.reception_level(other) == pytest.approx(3.0)
    assert matched.reception_level(Waveform(amplitude=2.0, frequency=4.0)) == pytest.approx(0.0)


def test_sample_shape_and_bound() -> None:
    """A single waveform samples to matched-length arrays bounded by amplitude."""
    wave = Waveform(amplitude=0.8, frequency=5.0, phase=0.0)
    t, y = wave.sample(0.05, sample_rate=8000)
    assert len(t) == len(y)
    assert len(y) > 0
    assert np.max(np.abs(y)) <= 0.8 + 1e-9


def test_superpose_length_and_amplitude_bound() -> None:
    """Superposition length matches the grid and stays within summed amplitudes."""
    w1 = Waveform(amplitude=0.6, frequency=3.0, phase=0.0)
    w2 = Waveform(amplitude=0.5, frequency=7.0, phase=1.0)
    t, y = superpose([w1, w2], 0.1, sample_rate=8000)
    assert len(t) == len(y)
    assert len(y) > 0
    assert np.max(np.abs(y)) <= 0.6 + 0.5 + 1e-9
