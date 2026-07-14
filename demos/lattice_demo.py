# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Tranception phase-lattice demo: animated phase colors or headless snapshot.

Run from the repository root::

    python demos/lattice_demo.py                 # interactive window
    python demos/lattice_demo.py --headless        # render one PNG and exit
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stablechaos.lattice import Lattice
from stablechaos.oscillator import PhaseConfig, PhaseLattice
from stablechaos.viz.interactive import Viewer, draw_phase_lattice

DEFAULT_OUT = Path(__file__).resolve().parent / "output" / "lattice.png"


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the lattice demo."""
    parser = argparse.ArgumentParser(description="Tranception phase-lattice demo.")
    parser.add_argument("--size", type=int, default=16, help="nodes per dimension")
    parser.add_argument("--dim", type=int, default=2, choices=(1, 2, 3),
                        help="lattice dimensionality")
    parser.add_argument("--k-polar", type=float, default=-1.0, dest="k_polar",
                        help="polar coupling strength (frustration; 0 disables)")
    parser.add_argument("--toroidal", action="store_true",
                        help="wrap coordinates modulo size")
    parser.add_argument("--fps", type=int, default=15,
                        help="frames per second for the interactive view")
    parser.add_argument("--steps", type=int, default=500,
                        help="steps to advance before a headless snapshot")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--headless", action="store_true",
                        help="render one PNG snapshot and exit")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output path for the headless snapshot")
    return parser


def build_lattice(args: argparse.Namespace) -> tuple[Lattice, PhaseLattice]:
    """Construct the geometric lattice and its seeded phase dynamics."""
    lattice = Lattice(size=args.size, dim=args.dim, toroidal=args.toroidal)
    config = PhaseConfig(k_polar=args.k_polar, seed=args.seed)
    return lattice, PhaseLattice(lattice, config)


def run_headless(lattice: Lattice, plat: PhaseLattice, steps: int, out: Path) -> None:
    """Advance ``steps`` steps, then write a single PNG snapshot."""
    out.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(steps):
        plat.step()
    viewer = Viewer(caption="StableChaos Lattice")
    viewer.snapshot(lambda surface: draw_phase_lattice(surface, lattice, plat.phases),
                    str(out))
    print(out)


def run_interactive(lattice: Lattice, plat: PhaseLattice, fps: int) -> None:
    """Open a window that steps the dynamics and draws phase colors each frame."""
    viewer = Viewer(fps=fps, caption="StableChaos Lattice")

    def draw(surface) -> None:
        plat.step()
        draw_phase_lattice(surface, lattice, plat.phases)

    viewer.run(draw)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to headless or interactive mode."""
    args = build_parser().parse_args(argv)
    if args.dim < 3 and args.k_polar != 0:
        print("Note: the polar orientation class is empty below 3-D, "
              "so --k-polar has no effect here.")
    lattice, plat = build_lattice(args)
    if args.headless:
        run_headless(lattice, plat, args.steps, args.out)
    else:
        run_interactive(lattice, plat, args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
