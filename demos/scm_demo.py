# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Stable Chaos Model demo: interactive ring viewer or headless PNG snapshot.

Run from the repository root::

    python demos/scm_demo.py                 # interactive window
    python demos/scm_demo.py --headless       # render one PNG and exit
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stablechaos.scm import SCMConfig, StableChaosModel
from stablechaos.viz.interactive import Viewer, draw_scm

DEFAULT_OUT = Path(__file__).resolve().parent / "output" / "scm.png"


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the SCM demo."""
    parser = argparse.ArgumentParser(description="Stable Chaos Model ring demo.")
    parser.add_argument("--nodes", type=int, default=4,
                        help="number of ring nodes (even, >= 4)")
    parser.add_argument("--fps", type=int, default=15,
                        help="frames per second for the interactive view")
    parser.add_argument("--ticks", type=int, default=500,
                        help="ticks to advance before a headless snapshot")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--headless", action="store_true",
                        help="render one PNG snapshot and exit")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output path for the headless snapshot")
    return parser


def build_model(args: argparse.Namespace) -> StableChaosModel:
    """Construct a seeded model from parsed arguments."""
    config = SCMConfig(n_nodes=args.nodes, seed=args.seed)
    return StableChaosModel(config)


def run_headless(model: StableChaosModel, ticks: int, out: Path) -> None:
    """Advance ``ticks`` steps, then write a single PNG snapshot."""
    out.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(ticks):
        model.tick()
    viewer = Viewer(caption="StableChaos SCM")
    viewer.snapshot(lambda surface: draw_scm(surface, model), str(out))
    print(out)


def run_interactive(model: StableChaosModel, fps: int) -> None:
    """Open a window that ticks and draws the model each frame."""
    viewer = Viewer(fps=fps, caption="StableChaos SCM")

    def draw(surface) -> None:
        model.tick()
        draw_scm(surface, model)

    viewer.run(draw)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to headless or interactive mode."""
    args = build_parser().parse_args(argv)
    model = build_model(args)
    if args.headless:
        run_headless(model, args.ticks, args.out)
    else:
        run_interactive(model, args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
