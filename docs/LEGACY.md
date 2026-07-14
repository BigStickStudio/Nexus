<!-- Written by Richard Christopher, Copyright 2026 NeoTec Digital -->
# Legacy Map

StableChaos v1.0 is a clean-room formalization of a set of prototypes built up over the life of the
project. The prototypes were exploratory and are not shipped in the finalized tree, but they are
fully preserved in git history — see commit `a22618d` and its ancestors. This document maps every
legacy path to its new home and records the specific prototype rule quirks the formalization
resolves. The quirks below were productive accidents: each one taught the model something, and each
is stated here precisely so the formal rules are traceable to their origin.

## Path mapping

### Stable Chaos Model (`Stable Chaos Model/`)

| Legacy path | New home | Notes |
| --- | --- | --- |
| `Stable Chaos Model/state.py` | `stablechaos/state.py` | dipole state algebra; `addA/minusA/...` become `moved`/`toward`/`away`; `STEP = 0.0987` kept exact |
| `Stable Chaos Model/node.py` | `stablechaos/scm.py` | per-node update; symmetrized (see quirks 1 and 2) |
| `Stable Chaos Model/sc_engine.py` | `stablechaos/scm.py` + `stablechaos/metrics.py` | synchronous tick; `acumen()` becomes `metrics.acumen` |
| `Stable Chaos Model/position.py` | `stablechaos/viz/interactive.py` | four fixed screen slots become nodes placed evenly on a circle |
| `Stable Chaos Model/main.py` | `demos/scm_demo.py` | runnable entry point |
| `Stable Chaos Model/README.md` | `docs/THEORY.md` + this file | narrative and diagrams |

### Tranception (`Tranception/`)

| Legacy path | New home | Notes |
| --- | --- | --- |
| `Tranception/__init__.py` | `stablechaos/lattice.py` | `Orientation` enum (Self/Orthogonal/Adjacent/Polar) |
| `Tranception/coupling.py` | `stablechaos/lattice.py` | `Coupling`, orientation classification by squared distance |
| `Tranception/reflector.py` | `stablechaos/oscillator.py` | per-node phase state |
| `Tranception/resonator.py` | `stablechaos/oscillator.py` | threshold-chasing feedback replaced by Kuramoto coupling (quirk 3) |
| `Tranception/propagation.py` | `stablechaos/oscillator.py` | `step()` / `run()` integration |
| `Tranception/tranceptor.py` | `stablechaos/lattice.py` + `stablechaos/oscillator.py` | lattice build + phase dynamics; argument-order bug fixed (quirk 4) |
| `Tranception/engine.py` | `stablechaos/viz/interactive.py` + `demos/lattice_demo.py` | rendering split from simulation |
| `Tranception/wave.py` | `stablechaos/waveform.py` | FFT round-trip replaced by exact phasor algebra |
| `Tranception/debug.py` | removed | replaced by standard structured output |
| `Tranception/README.md` | `docs/THEORY.md` | narrative and diagrams |

### Theoretical (`Theoretical/`)

| Legacy path | New home | Notes |
| --- | --- | --- |
| `Theoretical/sine.py` | `stablechaos/waveform.py` | `Waveform.sample` |
| `Theoretical/angular_phase.py` | `demos/waves_demo.py` + `docs/THEORY.md` | forward/backward phase discussion |
| `Theoretical/superposition.py` | `stablechaos/waveform.py` + `demos/waves_demo.py` | `superpose`; phase vs group velocity figure |
| `Theoretical/waveform.py`, `Theoretical/waves.py` | `stablechaos/waveform.py` + `demos/waves_demo.py` | consolidated |
| `Theoretical/emfp.py` | `docs/THEORY.md` (referenced) | EM field propagation is out of v1.0 scope; kept as reference material |
| `Theoretical/*.png` | `paper/figures/` (regenerated) | figures rebuilt deterministically by `demos/generate_figures.py` |
| `Theoretical/README.md` | `docs/THEORY.md` | narrative |

### Shared engine, fragments, web, and root files

| Legacy path | New home | Notes |
| --- | --- | --- |
| `engine/color.py` | `stablechaos/viz/colors.py` | state/phase color mapping |
| `engine/engine.py` | `stablechaos/viz/interactive.py` | windowed loop becomes `Viewer` |
| `engine/camera.py`, `engine/__init__.py` | removed | unused in the finalized package |
| `fragments/` | removed | superseded by `stablechaos/lattice.py` and `viz/` |
| `js/` | `web/` | cleaned Three.js particle-life demo (own README) |
| `main.py` (root) | `demos/lattice_demo.py` | Tranception entry point |
| `fragment_test.py` | `tests/` | replaced by the pytest suite |
| `__init__.py` (root) | removed | package now rooted at `stablechaos/` |
| `README2.md` | `docs/THEORY.md` + `README.md` | HATS narrative |
| `README2.md` merge objective ("merge Stable Chaos Model and Tranception") | `stablechaos/engine.py` (v1.1) | the legacy open item, now realized: a fused closed-loop engine on one torus (see [`THEORY.md`](THEORY.md) §6) |
| `Phases In Nature.md` | `docs/THEORY.md` | phase vs group velocity |
| `README.md` (root) | `README.md` (rewritten) + `LICENSE.md` | Ancillary License moved to `LICENSE.md` verbatim |

## Prototype rule quirks resolved by the formalization

These are prototype quirks, not bugs to be ashamed of. They are documented so the symmetrized rules
in `scm.py`, `oscillator.py`, and `waveform.py` are fully traceable.

### 1. Iteration-order-dependent updates (`Stable Chaos Model/node.py`)

The prototype `Node.update(nodes)` looped over the other nodes and `return`ed on the **first**
branch it matched. Because the opposite-node check came first and short-circuited, and because the
imitation branches fired against whichever left/right neighbor was encountered first, a node applied
**exactly one** interaction per tick, and which interaction it applied depended on the order the
nodes happened to sit in the list. The dynamics were therefore heterogeneous across nodes and
sensitive to list ordering rather than to topology.

**Formalization.** `scm.py` applies both the opposition and the imitation term to every node on the
same synchronous tick (all nodes read tick-`t`, write tick-`t+1`), with the opposite/left/right
neighbors defined purely by ring index. The behaviour no longer depends on iteration order, and the
opposition and imitation contributions become independent, switchable terms.

### 2. `repel()` opposes on A but follows on B (`Stable Chaos Model/state.py`)

The prototype `State.repel(node)` was asymmetric across the two degrees of freedom. On the `A`
channel it moved **away** from the other node (`node.A > self.A` decreased `A`), while on the `B`
channel it moved **toward** the other node (`node.B > self.B` increased `B`). Opposition on one axis,
imitation on the other — the two coupling mechanisms were already entangled inside a single method.

**Formalization.** The opposition term in `scm.py` keeps this exact split as its defining feature,
written symmetrically as `A_i += delta * sign(A_i - A_o)` (A opposes its opposite) and, on the B
channel, a follow step toward the opposite that is capped at half the gap,
`B_i += sign(B_o - B_i) * min(delta, abs(B_o - B_i) / 2)` (B follows, but only to the midpoint). The
cap is what lets a diametric pair meet and rest instead of overshooting into a permanent `±delta`
limit cycle, so opposition-only truly freezes; it coincides with the plain `delta * sign(B_o - B_i)`
step whenever `abs(B_o - B_i) > 2 * delta`. See `scm.py`
(`_apply_opposition`). The prototype's accidental asymmetry is promoted to the deliberate structural
asymmetry that makes the model interesting.

### 3. The resonator threshold-chasing loop (`Tranception/resonator.py`)

The prototype `Resonator.resonate()` maintained a `threshold` that chased `theta`, a
`resonant_frequency` that chased the `set_frequency`, and a `theta` derived back from the threshold —
a three-way mutual chase, each update rescaled by dividing by the sample rate (44100). The intent was
a self-tuning resonance that trails its own phase, but the coupled quantities had no clean fixed
point and the rescaling drove the threshold toward zero; a `latency` term for zeroing `theta` was
left commented out.

**Formalization.** `oscillator.py` replaces the ad-hoc threshold chase with a standard signed
Kuramoto update: each node integrates `d(phi_i) = omega_i + sum_c (K_c / |N_c(i)|) * sum_j sin(phi_j
- phi_i)`, summed over orientation classes `c` with signed constants `K_c`. Resonance and threshold
tracking are recovered as genuine phase synchronization, with a well-defined order parameter
`r = |mean(exp(i*phi))|` in `metrics.kuramoto_order`.

### 4. The TCEngine argument-order swap (`main.py`, `Tranception/engine.py`)

The prototype call chain swapped two enum arguments positionally. Root `main.py` called
`TCEngine(screen_size, grid_size, configuration, dimensionality, directionality)`, but
`TCEngine.__init__` declared its parameters as
`(self, screen_size, grid_size, dimensionality, configuration, directionality)` and forwarded them to
`Tranceptor(grid_size, configuration, dimensionality, directionality)`. Because `configuration` and
`dimensionality` were passed in one order and received in the other, a `Configuration` value landed
in the `dimensionality` slot and vice versa — the constructed lattice did not match the requested
`Dimensionality.Linear` / `Configuration.Adjacency`.

**Formalization.** `Lattice(size, dim, toroidal)` takes explicit, unambiguous, keyword-friendly
parameters, and the demos pass them by name, so the geometry always matches the request.
