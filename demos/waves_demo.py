# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Waveform demo: same-frequency superposition and phase/group velocity.

Consolidates the legacy ``Theoretical/`` scripts. Pure matplotlib (no pygame).
Defaults to the Agg backend and writes figures under ``demos/output/``; pass
``--show`` to display them interactively instead::

    python demos/waves_demo.py            # save PNG/PDF figures and exit
    python demos/waves_demo.py --show     # open interactive windows
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_OUT = Path(__file__).resolve().parent / "output"


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the waveform demo."""
    parser = argparse.ArgumentParser(description="Waveform superposition demo.")
    parser.add_argument("--show", action="store_true",
                        help="display figures interactively instead of saving")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output directory for saved figures")
    parser.add_argument("--seed", type=int, default=42,
                        help="random seed for the sampled-signal noise floor")
    return parser


def build_phase_group_figure(rng):
    """Return a two-panel figure contrasting phase and group velocity.

    Two close-frequency sinusoids superpose into a carrier (moving at the phase
    velocity) modulated by an envelope (moving at the group velocity), shown at
    two instants with the envelope peak tracked by the dashed marker.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.linspace(0.0, 40.0, 1600)
    k1, k2 = 1.0, 1.15
    w1, w2 = float(np.sqrt(k1)), float(np.sqrt(k2))
    dk, dw = k2 - k1, w2 - w1
    v_phase = ((w1 + w2) / 2.0) / ((k1 + k2) / 2.0)
    v_group = dw / dk
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 5.0), sharex=True)
    for ax, t in zip(axes, (0.0, 6.0)):
        signal = np.cos(k1 * x - w1 * t) + np.cos(k2 * x - w2 * t)
        signal = signal + rng.normal(0.0, 0.03, size=x.shape)
        envelope = 2.0 * np.abs(np.cos((dk * x - dw * t) / 2.0))
        ax.plot(x, signal, color="#1f77b4", lw=0.8, label="superposition")
        ax.plot(x, envelope, color="#d62728", lw=1.5, label="envelope")
        ax.plot(x, -envelope, color="#d62728", lw=1.5)
        ax.axvline(v_group * t, color="#2ca02c", ls="--", lw=1.2,
                   label="envelope peak")
        ax.set_ylabel("amplitude")
        ax.set_title(f"t = {t:.1f}")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[1].set_xlabel("position x")
    fig.suptitle(f"phase velocity {v_phase:.3f}  vs  group velocity {v_group:.3f}")
    fig.tight_layout()
    return fig


def run(args: argparse.Namespace) -> int:
    """Build both figures and either display or save them."""
    import matplotlib
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from stablechaos.viz.figures import fig_wave_superposition

    rng = np.random.default_rng(args.seed)
    if args.show:
        fig_wave_superposition(out=None)
        build_phase_group_figure(rng)
        plt.show()
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / "wave_superposition"
    plt.close(fig_wave_superposition(out=base))
    group_path = out_dir / "wave_phase_group.png"
    fig = build_phase_group_figure(rng)
    fig.savefig(group_path, dpi=200)
    plt.close(fig)
    for path in (base.with_suffix(".pdf"), base.with_suffix(".png"), group_path):
        print(path)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the demo."""
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
