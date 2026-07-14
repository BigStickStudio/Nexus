# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.state: clamping, STEP constant, toward/away, sign."""

import pytest

from stablechaos.state import STEP, State, sign


def test_step_value_exact() -> None:
    """STEP must retain the legacy constant value exactly."""
    assert STEP == 0.0987


def test_sign_three_way() -> None:
    """sign returns -1.0, 0.0, or 1.0."""
    assert sign(5.0) == 1.0
    assert sign(-3.0) == -1.0
    assert sign(0.0) == 0.0


def test_clamped_both_ends() -> None:
    """clamped saturates both channels at both bounds and leaves interior alone."""
    assert State(2.0, 2.0).clamped().as_tuple() == pytest.approx((1.0, 1.0))
    assert State(-2.0, -2.0).clamped().as_tuple() == pytest.approx((-1.0, -1.0))
    assert State(0.3, -0.4).clamped().as_tuple() == pytest.approx((0.3, -0.4))


def test_moved_clamps_result() -> None:
    """moved returns a clamped new State."""
    assert State(0.99, 0.99).moved(1.0, 1.0).as_tuple() == pytest.approx((1.0, 1.0))
    assert State(-0.99, -0.99).moved(-1.0, -1.0).as_tuple() == pytest.approx((-1.0, -1.0))
    assert State(0.0, 0.0).moved(0.1, -0.2).as_tuple() == pytest.approx((0.1, -0.2))


def test_as_tuple_returns_components() -> None:
    """as_tuple returns the (a, b) pair."""
    assert State(0.3, -0.4).as_tuple() == pytest.approx((0.3, -0.4))


def test_toward_componentwise_signs() -> None:
    """toward moves one step in the sign direction per channel, clamped."""
    assert State(0.0, 0.0).toward(State(1.0, 1.0)).as_tuple() == pytest.approx((STEP, STEP))
    assert State(0.0, 0.0).toward(State(-1.0, -1.0)).as_tuple() == pytest.approx((-STEP, -STEP))
    assert State(0.0, 0.0).toward(State(1.0, -1.0)).as_tuple() == pytest.approx((STEP, -STEP))


def test_away_componentwise_signs() -> None:
    """away moves one step opposite the sign direction per channel."""
    assert State(0.0, 0.0).away(State(1.0, 1.0)).as_tuple() == pytest.approx((-STEP, -STEP))
    assert State(0.0, 0.0).away(State(-1.0, -1.0)).as_tuple() == pytest.approx((STEP, STEP))
    assert State(0.0, 0.0).away(State(1.0, -1.0)).as_tuple() == pytest.approx((-STEP, STEP))


def test_toward_and_away_hold_at_equal() -> None:
    """Equal states produce no movement (sign of a zero difference)."""
    here = State(0.5, -0.25)
    assert here.toward(State(0.5, -0.25)).as_tuple() == pytest.approx((0.5, -0.25))
    assert here.away(State(0.5, -0.25)).as_tuple() == pytest.approx((0.5, -0.25))


def test_toward_custom_step_clamps() -> None:
    """A large custom step advances then clamps to the domain bounds."""
    assert State(0.95, 0.95).toward(State(1.0, 1.0), step=0.5).as_tuple() == pytest.approx((1.0, 1.0))
    assert State(0.0, 0.0).toward(State(1.0, 1.0), step=0.5).as_tuple() == pytest.approx((0.5, 0.5))
