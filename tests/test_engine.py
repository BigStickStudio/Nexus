# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tests for stablechaos.engine: validation, shapes, determinism, equivalence,
antipode topology, scm.py-semantics, bounds, ablations, and the measured
fused regime."""

import numpy as np
import pytest

from stablechaos.engine import EngineConfig, StableChaosEngine
from stablechaos.lattice import Lattice, Orientation
from stablechaos.metrics import kuramoto_order, mean_step_size
from stablechaos.oscillator import PhaseConfig, PhaseLattice
from stablechaos.state import STEP, State, sign

SEED = 42
STEPS = 3000
TWO_PI = 2.0 * np.pi


def _scm_reference(a, b, r_a, r_b, opp, left, right, delta, opposition, imitation):
    """Oracle: the exact scm.py per-node rule over given neighbor indices."""
    states = [State(float(a[i]), float(b[i])) for i in range(len(a))]
    out = []
    for i in range(len(a)):
        w = states[i]
        if opposition:
            other = states[opp[i]]
            gap = other.b - w.b
            w = w.moved(delta * sign(w.a - other.a),
                        sign(gap) * min(delta, abs(gap) / 2.0))
        if imitation:
            w = _reference_imitate(w, states[left[i]], states[right[i]],
                                   r_a[i], r_b[i], delta)
        out.append(w.clamped())
    return np.array([s.as_tuple() for s in out])


def _reference_imitate(w, left, right, r_a, r_b, delta):
    """The scm.py imitation branch chain for a single node."""
    if r_a == 1 and r_b == 1:
        return w.moved(-delta, -delta)
    if r_a == -1 and r_b == -1:
        return w.moved(delta, delta)
    if r_a != 0:
        return w.toward(left, delta) if r_a == 1 else w.away(left, delta)
    if r_b != 0:
        return w.toward(right, delta) if r_b == 1 else w.away(right, delta)
    return w


def _local_coherence(engine, phases):
    """Per-node |mean over orthogonal neighbors of exp(i*(phi_j - phi_i))|."""
    src, tgt, deg = engine._classes[Orientation.ORTHOGONAL]
    z = np.exp(1j * (phases[tgt] - phases[src]))
    acc = (np.bincount(src, weights=z.real, minlength=engine.n)
           + 1j * np.bincount(src, weights=z.imag, minlength=engine.n))
    return np.abs(acc / deg)


def _pearson(x, y):
    """Pearson correlation of two 1-D arrays."""
    x = x - x.mean()
    y = y - y.mean()
    denom = np.sqrt(np.sum(x * x) * np.sum(y * y))
    return float(np.sum(x * y) / denom) if denom > 0 else 0.0


def _tail_metrics(config):
    """Run a config and return (r_mean, r_std, live, coherence-vs-A corr)."""
    engine = StableChaosEngine(config)
    phases, states = engine.run(STEPS)
    order = kuramoto_order(phases)
    cut = int(len(order) * 0.75)
    corrs = [_pearson(_local_coherence(engine, phases[k]), states[k, :, 0])
             for k in range(cut, len(order), 50)]
    return (float(np.mean(order[cut:])), float(np.std(order[cut:])),
            mean_step_size(states, window=200), float(np.nanmean(corrs)))


@pytest.fixture(scope="module")
def fused():
    """Fused closed loop: phase drive, full downward gains."""
    return _tail_metrics(EngineConfig(size=6, dim=3, omega_gain=1.0,
                                      frustration_gain=1.0, seed=SEED))


@pytest.fixture(scope="module")
def plain():
    """Downward ablation: gains 0/0, equivalent to a plain frustrated lattice."""
    return _tail_metrics(EngineConfig(size=6, dim=3, omega_gain=0.0,
                                      frustration_gain=0.0, seed=SEED))


@pytest.fixture(scope="module")
def random_drive():
    """Upward ablation: RNG drive replaces the phase field."""
    return _tail_metrics(EngineConfig(size=6, dim=3, omega_gain=1.0,
                                      frustration_gain=1.0, drive="random",
                                      seed=SEED))


def test_odd_size_raises():
    """An odd lattice size has no toroidal antipode."""
    with pytest.raises(ValueError):
        EngineConfig(size=5)


def test_too_small_size_raises():
    """A size below four is degenerate for the ring neighbors."""
    with pytest.raises(ValueError):
        EngineConfig(size=2)


def test_bad_dim_raises():
    """Dimensionality outside {1, 2, 3} is rejected."""
    with pytest.raises(ValueError):
        EngineConfig(dim=4)


def test_bad_drive_raises():
    """An unknown drive mode is rejected."""
    with pytest.raises(ValueError):
        EngineConfig(drive="noise")


def test_frustration_gain_range_raises():
    """frustration_gain must lie in [0, 1]."""
    with pytest.raises(ValueError):
        EngineConfig(frustration_gain=1.5)


def test_run_shapes():
    """run returns (steps+1, n) phases and (steps+1, n, 2) states."""
    engine = StableChaosEngine(EngineConfig(size=4, dim=2, seed=0))
    phases, states = engine.run(50)
    assert phases.shape == (51, 16)
    assert states.shape == (51, 16, 2)


def test_phase_drive_is_deterministic():
    """A phase-driven engine is reproducible from the seed alone."""
    cfg = EngineConfig(size=6, dim=3, seed=7)
    p1, s1 = StableChaosEngine(cfg).run(200)
    p2, s2 = StableChaosEngine(cfg).run(200)
    assert np.array_equal(p1, p2)
    assert np.array_equal(s1, s2)


def test_reset_reproduces():
    """reset(seed) restores an identical starting trajectory."""
    engine = StableChaosEngine(EngineConfig(size=4, dim=2, seed=3))
    first, _ = engine.run(80)
    engine.reset(seed=3)
    second, _ = engine.run(80)
    assert np.array_equal(first, second)


def test_random_drive_determinism_and_reset():
    """The random drive is seed-deterministic and reset restores it bit-for-bit."""
    cfg = EngineConfig(size=6, dim=3, drive="random", seed=17)
    phases_a, states_a = StableChaosEngine(cfg).run(150)
    phases_b, states_b = StableChaosEngine(cfg).run(150)
    assert np.array_equal(phases_a, phases_b)
    assert np.array_equal(states_a, states_b)
    engine = StableChaosEngine(cfg)
    engine.run(150)
    engine.reset(seed=17)
    phases_c, states_c = engine.run(150)
    assert np.array_equal(phases_a, phases_c)
    assert np.array_equal(states_a, states_c)


def test_equivalence_to_plain_lattice():
    """Gains 0/0 make the phase trajectory bit-identical to a PhaseLattice."""
    lattice = Lattice(6, 3, toroidal=True)
    pcfg = PhaseConfig(k_orthogonal=1.0, k_adjacent=0.5, k_polar=-1.0,
                       omega_mean=0.0, omega_spread=0.1, dt=0.05, seed=SEED)
    expected = PhaseLattice(lattice, pcfg).run(300)
    engine = StableChaosEngine(EngineConfig(size=6, dim=3, omega_gain=0.0,
                                            frustration_gain=0.0, seed=SEED))
    phases, _ = engine.run(300)
    assert np.array_equal(expected, phases)


def test_equivalence_holds_under_random_drive():
    """State evolution never perturbs phases when downward gains vanish."""
    lattice = Lattice(6, 3, toroidal=True)
    pcfg = PhaseConfig(k_polar=-1.0, omega_spread=0.1, dt=0.05, seed=SEED)
    expected = PhaseLattice(lattice, pcfg).run(300)
    engine = StableChaosEngine(EngineConfig(size=6, dim=3, omega_gain=0.0,
                                            frustration_gain=0.0, drive="random",
                                            seed=SEED))
    phases, _ = engine.run(300)
    assert np.array_equal(expected, phases)


def test_antipode_ring_dim1():
    """Size-4 1-D antipodes and ring neighbors are the scm.py ring."""
    engine = StableChaosEngine(EngineConfig(size=4, dim=1, seed=0))
    assert engine._antipode.tolist() == [2, 3, 0, 1]
    assert engine._left.tolist() == [1, 2, 3, 0]
    assert engine._right.tolist() == [3, 0, 1, 2]


def test_antipode_dim2_hand_computed():
    """Size-4 2-D antipodes match hand-computed ((x+2)%4, (y+2)%4)."""
    engine = StableChaosEngine(EngineConfig(size=4, dim=2, seed=0))
    assert int(engine._antipode[0]) == 10   # (0,0) -> (2,2)
    assert int(engine._antipode[1]) == 11   # (1,0) -> (3,2)
    assert int(engine._antipode[5]) == 15   # (1,1) -> (3,3)
    assert int(engine._antipode[15]) == 5   # (3,3) -> (1,1)


@pytest.mark.parametrize("opposition,imitation", [(True, True), (True, False),
                                                  (False, True)])
def test_scm_update_matches_scm_semantics(opposition, imitation):
    """The lattice SCM update reproduces the exact scm.py rule."""
    engine = StableChaosEngine(EngineConfig(size=4, dim=1, seed=0,
                                            opposition=opposition,
                                            imitation=imitation))
    opp, left, right = (engine._antipode.tolist(), engine._left.tolist(),
                        engine._right.tolist())
    rng = np.random.default_rng(9)
    for _ in range(200):
        a, b = rng.uniform(-1, 1, 4), rng.uniform(-1, 1, 4)
        r_a = rng.integers(-1, 2, 4).astype(float)
        r_b = rng.integers(-1, 2, 4).astype(float)
        got = engine._scm_update(a.copy(), b.copy(), r_a, r_b)
        want = _scm_reference(a, b, r_a, r_b, opp, left, right, STEP,
                              opposition, imitation)
        assert np.array_equal(got, want)


def test_states_and_phases_bounded():
    """States stay in [-1, 1]^2 and phases in [0, 2*pi)."""
    engine = StableChaosEngine(EngineConfig(size=6, dim=3, seed=SEED))
    phases, states = engine.run(500)
    assert states.min() >= -1.0 - 1e-12
    assert states.max() <= 1.0 + 1e-12
    assert phases.min() >= 0.0
    assert phases.max() < TWO_PI + 1e-9


def test_downward_gains_change_dynamics():
    """Turning the downward coupling on changes the phase trajectory."""
    off, _ = StableChaosEngine(EngineConfig(size=6, dim=3, omega_gain=0.0,
                                            frustration_gain=0.0, seed=SEED)).run(300)
    on, _ = StableChaosEngine(EngineConfig(size=6, dim=3, omega_gain=1.0,
                                           frustration_gain=1.0, seed=SEED)).run(300)
    assert not np.array_equal(off, on)


def test_drive_mode_changes_states():
    """Phase drive and random drive produce different state trajectories."""
    _, phase_states = StableChaosEngine(
        EngineConfig(size=6, dim=3, drive="phase", seed=SEED)).run(300)
    _, random_states = StableChaosEngine(
        EngineConfig(size=6, dim=3, drive="random", seed=SEED)).run(300)
    assert not np.array_equal(phase_states, random_states)


def test_fused_sustains_intermediate_order(fused, plain):
    """The fused loop lifts order from the disordered plain lattice to a
    sustained intermediate band."""
    assert plain[0] < 0.05
    assert 0.12 < fused[0] < 0.4


def test_fused_regulates_order(fused, random_drive):
    """The deterministic phase drive holds order far steadier than RNG drive."""
    assert fused[1] < 0.02
    assert random_drive[1] > 0.03
    assert fused[1] < 0.5 * random_drive[1]


def test_closed_loop_keeps_scm_live(fused, plain):
    """Full downward coupling stops the SCM from freezing under phase drive."""
    assert plain[2] < 0.002
    assert fused[2] > 0.003


def test_coherence_anticorrelates_with_A_field(fused):
    """Local phase coherence anti-correlates with the frozen A pattern."""
    assert fused[3] < -0.05


def test_frustration_off_removes_correlation():
    """Without frustration modulation the A field does not organize coherence."""
    metrics = _tail_metrics(EngineConfig(size=6, dim=3, omega_gain=1.0,
                                         frustration_gain=0.0, seed=SEED))
    assert abs(metrics[3]) < 0.1
