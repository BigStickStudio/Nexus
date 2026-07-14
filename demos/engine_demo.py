# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Fused Stable Chaos engine demo: phase hue field beside the A field.

Run from the repository root::

    python demos/engine_demo.py                 # interactive window
    python demos/engine_demo.py --headless        # render one PNG and exit

The left panel shows the mid-plane phase field (hue), the right panel the frozen
A field (grayscale) that carves the frustration landscape.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stablechaos.engine import EngineConfig, StableChaosEngine
from stablechaos.viz.interactive import Viewer, draw_engine

DEFAULT_OUT = Path(__file__).resolve().parent / "output" / "engine.png"


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the fused engine demo."""
    parser = argparse.ArgumentParser(description="Fused Stable Chaos engine demo.")
    parser.add_argument("--size", type=int, default=6, help="nodes per dimension")
    parser.add_argument("--dim", type=int, default=3, choices=(1, 2, 3),
                        help="lattice dimensionality")
    parser.add_argument("--steps", type=int, default=500,
                        help="steps to advance before a headless snapshot")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--omega-gain", type=float, default=1.0, dest="omega_gain",
                        help="downward frequency-wander gain")
    parser.add_argument("--frustration-gain", type=float, default=1.0,
                        dest="frustration_gain",
                        help="downward frustration-landscape gain in [0, 1]")
    parser.add_argument("--drive", choices=("phase", "random"), default="phase",
                        help="upward SCM drive source")
    parser.add_argument("--fps", type=int, default=15,
                        help="frames per second for the interactive view")
    parser.add_argument("--headless", action="store_true",
                        help="render one PNG snapshot and exit")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output path for the headless snapshot")
    return parser


def build_engine(args: argparse.Namespace) -> StableChaosEngine:
    """Construct a seeded fused engine from parsed arguments."""
    config = EngineConfig(size=args.size, dim=args.dim, omega_gain=args.omega_gain,
                          frustration_gain=args.frustration_gain, drive=args.drive,
                          seed=args.seed)
    return StableChaosEngine(config)


def run_headless(engine: StableChaosEngine, steps: int, out: Path) -> None:
    """Advance ``steps`` steps, then write a single PNG snapshot."""
    out.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(steps):
        engine.step()
    viewer = Viewer(size=(1200, 600), caption="StableChaos Engine")
    viewer.snapshot(lambda surface: draw_engine(surface, engine), str(out))
    print(out)


def run_interactive(engine: StableChaosEngine, fps: int) -> None:
    """Open a window that steps the fused engine and draws both fields."""
    viewer = Viewer(size=(1200, 600), fps=fps, caption="StableChaos Engine")

    def draw(surface) -> None:
        engine.step()
        draw_engine(surface, engine)

    viewer.run(draw)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to headless or interactive mode."""
    args = build_parser().parse_args(argv)
    engine = build_engine(args)
    if args.headless:
        run_headless(engine, args.steps, args.out)
    else:
        run_interactive(engine, args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
