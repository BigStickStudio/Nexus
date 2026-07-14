<!-- Written by Richard Christopher, Copyright 2026 NeoTec Digital -->
# Theory

This document collects the conceptual narrative that motivated StableChaos and maps each idea to the
formal model implemented in `stablechaos/`. It absorbs the three legacy READMEs (HATS,
Stable Chaos Model, Tranception) and the wave-mechanics notes from `Phases In Nature.md`, rewritten
cleanly. The historical prototypes are preserved in git history; see [`LEGACY.md`](LEGACY.md).

## 1. HATS: a self-stabilizing system that leans toward chaos

The original framing called the project **HATS — Hybrid Abstract Transitory State**. The goal was to
model wave behavior across a network of nodes (reflectors), studying interference, induction, and
divergence: the net flow of wave properties such as phase and amplitude across a network, and where
that flow converges or diverges. The recurring intuition was that a system could be *self-guiding,
self-actuating, and self-stabilizing* while still leaning toward a controlled level of chaos —
borrowing the language of the Uncertainty Principle to describe states known only within broad and
narrow bounds.

The formalization keeps the intuition and drops the mysticism. "Self-stabilizing yet chaotic"
becomes a precise, measurable claim: the dynamics have **no fixed point**, stay **bounded**, and
occupy their state space with **high entropy**. Those three properties are what we measure in
[`stablechaos/metrics.py`](../stablechaos/metrics.py).

## 2. Tranception: one degree of freedom, first principles

Tranception starts from a single degree of freedom — one axis, an infinite range of values,
independent of other observables (credited in the legacy notes to the observation by EatThePath).
That axis is read as an angle, theta, computed as `atan2(sin, cos)`, so the state is cyclic and can
be observed across any delta. From this the legacy work derived a small rule set for **resonance,
threshold, induction, and interference** and a connection type between two resonant reflectors.

The connection type is the load-bearing idea. Two nodes are coupled by their **geometric orientation
class**, determined by the squared distance of their lattice offset:

| Class | Squared distance | 3-D interior count |
| --- | --- | --- |
| Orthogonal | 1 | 6 |
| Adjacent (diagonal) | 2 | 12 |
| Polar | 3 | 8 |

These decompose the 26-neighbor cube as `26 = 6 + 12 + 8`. In the formal model each class carries a
signed coupling constant, and the ad-hoc resonance/threshold feedback is replaced by standard phase
coupling. This lives in [`stablechaos/lattice.py`](../stablechaos/lattice.py) (classification and
neighborhoods) and [`stablechaos/oscillator.py`](../stablechaos/oscillator.py) (signed Kuramoto phase
dynamics on the lattice). The legacy 1-D/2-D/3-D "iterations" become the `dim` argument, and the
long-standing toroidal wrap-around, previously left on the wish list, is completed as the
`toroidal` flag.

### Figures (legacy diagrams)

The orientation classes and their higher-order connectivity were illustrated in the original
Tranception README. Those diagrams remain informative:

- 1st dimension in 3D — https://github.com/user-attachments/assets/d31b184b-93be-4e72-b213-9fe567ba7f70
- 2nd dimension, fully connected — https://github.com/BigStickStudio/StableChaos/assets/87874714/77c2bd0e-bcee-4e17-87ba-9db02cdae66a
- 2nd dimension, single node — https://github.com/BigStickStudio/StableChaos/assets/87874714/37af4ce5-b436-48db-8fea-d80c2cfb9262
- 3rd iteration, full 3D — https://github.com/user-attachments/assets/ce7efe85-3f4a-4a5f-b6f3-e5f08708408d
- 3rd iteration, connectivity — https://github.com/user-attachments/assets/2a9cba50-b3c9-49bf-949d-9defd8c6324a
- 3rd iteration, connectivity — https://github.com/user-attachments/assets/f86d375f-9d77-46c7-9879-d711aee7eea6
- Dual di-pole connection — https://github.com/user-attachments/assets/a0c100bc-6e85-4c2c-bfd7-905efe70e514
- Dual di-pole connection — https://github.com/user-attachments/assets/fce30df8-7bf0-44e7-ad56-8252a70a7ebb
- Dual di-pole connection — https://github.com/user-attachments/assets/332a0c74-5c9e-43e1-a83a-e1f6cdff2408
- Single di-pole iteration — https://github.com/user-attachments/assets/5a1817fd-0aa1-42f1-8e2e-0f3cdb9d6972
- Single node by network — https://github.com/user-attachments/assets/78958573-b080-4328-aaf0-86de41aca22a

The reproducible analogue of the 26-neighborhood diagram is generated as `fig_neighborhood` by
`demos/generate_figures.py`.

## 3. The Stable Chaos Model: superposition of dipole states

The Stable Chaos Model asks whether an abstract "super state" can persist as a transient object —
something that holds a stateful and a stateless form at once, representing many possible states
simultaneously. Concretely, each node carries two degrees of freedom, `A` and `B`, each in
`[-1, 1]`, so a node is a superposition of `A | B | !A | !B`.

The rules were stated simply: a node tries to align with one neighbor and take the inverse of its
opposing neighbor, while holding an opposing motion to its own opposite. The striking observation
from the prototype was the source of the project's name:

> It is a system's own inversion or opposition that creates stability, and its own likeness to its
> neighbors that introduces a constant state of chaos.

This is exactly the thesis the formal model isolates. **Opposition freezes; likeness wanders;
together they produce bounded persistent motion.** The formalization symmetrizes the heterogeneous
prototype rules into a single synchronous update over an even ring of `N` nodes, with independent
ablation switches for the opposition and imitation terms, in
[`stablechaos/scm.py`](../stablechaos/scm.py) and the underlying state algebra in
[`stablechaos/state.py`](../stablechaos/state.py). The exact rule differences between prototype and
formalization are catalogued in [`LEGACY.md`](LEGACY.md).

### Figures (legacy diagrams)

- Neighbor/opposition relationship — https://github.com/alephpt/HATS/assets/87874714/70f12062-4cba-45ec-8c22-718742c881ad
- Two degrees of freedom — https://github.com/alephpt/HATS/assets/87874714/1db6fdc9-057e-41a1-8212-747bf69b0edb
- State snapshots — https://github.com/alephpt/HATS/assets/87874714/52474074-1779-49d7-8d72-f0c840cc4f7c
- State snapshots — https://github.com/alephpt/HATS/assets/87874714/f258792f-20cc-4cb9-8388-ba8eb582640e
- State snapshots — https://github.com/alephpt/HATS/assets/87874714/912b984e-380b-4b63-b19a-b45a9848d140

The state-to-color mapping (`-1` to black, `+1` to white, with the second channel toward red/blue)
is preserved in [`stablechaos/viz/colors.py`](../stablechaos/viz/colors.py).

## 4. Phase versus group velocity

The wave notes underpin the waveform algebra and the paper's discussion of forward/backward
apparent motion. Two aspects of a wave must be distinguished.

**Phase.** The phase locates a point within its cycle relative to a reference,
`phi = omega * t + phi_0`, where `omega` is the angular frequency and `phi_0` the initial phase. It
is a property of an individual frequency component. **Phase velocity** `v_phase` measures how fast
that phase advances through space.

**Group (packet envelope).** When several frequency components superpose, their envelope localizes
energy or information in space and time. **Group velocity** `v_group` measures how fast that envelope
moves. Phase and group velocity generally differ, which is why a component can appear to slide
backward inside an envelope that advances forward — the phenomenon that motivated the "backwards
movement of waves" note.

These distinctions appear across optics, acoustics, water waves, quantum mechanics, and biological
rhythm synchronization. In the formal model they are made exact: same-frequency waves combine by
**phasor addition** (amplitude and phase from `hypot`/`atan2`), and multi-frequency superposition is
sampled directly rather than round-tripped through an FFT. See
[`stablechaos/waveform.py`](../stablechaos/waveform.py) and the `demos/waves_demo.py` figure.

## 5. Mapping to the formal model

| Concept (legacy) | Formal home |
| --- | --- |
| HATS self-stabilizing chaos | operational metrics: no fixed point, bounded, high occupancy entropy (`metrics.py`) |
| Dipole node `A \| B \| !A \| !B` | `State` and the ring update (`state.py`, `scm.py`) |
| Opposition stabilizes, likeness destabilizes | ablation switches `opposition` / `imitation` in `SCMConfig` |
| Tranception orientation classes | `Orientation`, `classify`, `Lattice` (`lattice.py`) |
| Resonance / threshold / induction feedback | signed Kuramoto phase coupling (`oscillator.py`) |
| Resonant frequency and reception level | `Waveform.resonant_frequency`, `Waveform.reception_level` |
| Phase vs group velocity notes | `waveform.py` phasor algebra + `demos/waves_demo.py` |
| Toroidal / higher-dimensional wish-list items | `Lattice(toroidal=True)`, `dim in {1, 2, 3}` |

The relationship between the two models is the thesis itself: the Stable Chaos Model realizes
antagonistic-plus-imitative coupling on a minimal ring, while the Tranception lattice realizes the
same competition between alignment and frustration on an extended geometry. Both are bounded and
persistent; neither converges.
