<!-- Written by Richard Christopher, Copyright 2026 NeoTec Digital -->
# StableChaos Web Demo

A browser particle-life demonstration of the Stable Chaos thesis. Eight particle
types `a..h` are placed at the vertices of a 3-bit cube. Every ordered pair of
types is classified by Hamming distance into a relationship class — the web
analogue of the lattice orientation classes used elsewhere in this repository:

| Hamming distance | Relationship | Cube geometry |
| ---------------- | ------------ | ------------- |
| 0 | `sameType`   | same vertex   |
| 1 | `orthogonal` | edge (adjacent) |
| 2 | `diagonal`   | face diagonal |
| 3 | `polar`      | body diagonal (opposite) |

Each class carries its own attraction and repulsion strength, and particles
stochastically switch type toward whichever type dominates their local
neighborhood (type-contagion). Antagonistic (repulsive) and imitative
(attractive/contagious) couplings act together: the initially chaotic cloud
condenses into persistent, wandering ordered domains that never freeze and never
disperse — the browser-side picture of bounded, non-converging "stable chaos".

## Controls

The controls live in the on-screen dat.GUI panel (top right) and the interactive
3-bit cube rendered inside it.

| Control | Effect |
| ------- | ------ |
| Camera drag / scroll | Orbit and zoom the 3-D scene (OrbitControls). |
| Core Settings, particlesPerType | Particles per type; total is `particlesPerType * 8`. |
| Core Settings, Global Attraction / Repulsion | Uniform bias applied to every pair. |
| Attraction Settings | Base attraction per relationship class (Same Type, Adjacent, Diagonal, Polar). |
| Repulsion Settings | Base repulsion per relationship class. |
| Reset | Apply the built-in ordered-domain preset. |
| Type Biases | Per-type color plus per-type attraction and repulsion bias for each class. |
| Type Matrix | Per-pair attraction and repulsion (`ab attraction`, `ab repulsion`, ...). |
| Cube: click a node | Select a type; highlights it and its relationship connections. |
| Cube: drag | Rotate the 3-bit cube diagram. |

Connection color and thickness in the cube diagram encode the current attraction
value for each pair (blue attractive, red repulsive).

## Running

The demo uses native ES modules and loads Three.js from a CDN, so it must be
served over HTTP (opening `index.html` directly with a `file://` URL will not
work) and the machine needs internet access for the CDN.

```
cd web
python -m http.server 8000
```

Then open `http://localhost:8000/` in a modern browser.

## Dependencies

- [Three.js](https://unpkg.com/three@0.112) (`0.112`) and its `OrbitControls`
  and `dat.gui` example modules, loaded from unpkg. No local build step and no
  npm dependencies.
