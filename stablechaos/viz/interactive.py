# Written by Richard Christopher, Copyright 2026 NeoTec Digital
"""Pygame interactive views for StableChaos (the only pygame code in the package).

Provides a small windowed :class:`Viewer` loop with a headless ``snapshot``
mode, plus draw callbacks for the Stable Chaos Model and the phase lattice.
"""
from __future__ import annotations

import math
import os
from typing import TYPE_CHECKING, Callable

import numpy as np

# Silence pygame's import banner before importing it.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402  (must follow the env setup above)

from ..metrics import acumen
from .colors import PALETTE, phase_color, state_color

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from ..engine import StableChaosEngine
    from ..lattice import Lattice
    from ..scm import StableChaosModel

DrawFn = Callable[["pygame.Surface"], None]


class Viewer:
    """A minimal pygame window loop with a headless snapshot mode."""

    def __init__(
        self,
        size: tuple[int, int] = (900, 900),
        fps: int = 15,
        caption: str = "StableChaos",
    ) -> None:
        """Store window geometry, frame rate, and caption."""
        self.size = size
        self.fps = fps
        self.caption = caption

    def run(self, draw: DrawFn) -> None:
        """Open a window and call ``draw`` each frame until ESC/close quits."""
        pygame.init()
        screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption(self.caption)
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            screen.fill(PALETTE["BG"])
            draw(screen)
            pygame.display.flip()
            clock.tick(self.fps)
        pygame.quit()

    def snapshot(self, draw: DrawFn, out_path: str) -> None:
        """Render one frame headlessly and save it to ``out_path`` as PNG.

        The SDL driver overrides are scoped to this call: prior values are
        saved and restored in a ``finally`` block (deleted if previously
        unset) so a subsequent :meth:`run` in the same process is unaffected.
        """
        driver_keys = ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER")
        prior = {key: os.environ.get(key) for key in driver_keys}
        try:
            for key in driver_keys:
                os.environ[key] = "dummy"
            if not pygame.get_init():
                pygame.init()
            if not pygame.display.get_init():
                pygame.display.init()
            surface = pygame.Surface(self.size)
            surface.fill(PALETTE["BG"])
            draw(surface)
            pygame.image.save(surface, out_path)
            pygame.display.quit()
        finally:
            for key, value in prior.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def draw_scm(surface: "pygame.Surface", model: "StableChaosModel") -> None:
    """Draw the acumen disc plus one circle per node on an even ring."""
    states = model.states
    if not states:
        return
    width, height = surface.get_size()
    center = (width // 2, height // 2)
    span = min(width, height)
    values = np.array([s.as_tuple() for s in states], dtype=float)
    mean = acumen(values)
    pygame.draw.circle(
        surface, state_color(float(mean[0]), float(mean[1])), center, int(span * 0.42)
    )
    ring_radius = span * 0.30
    node_radius = int(span * 0.07)
    for i, state in enumerate(states):
        angle = 2.0 * math.pi * i / len(states)
        x = int(center[0] + ring_radius * math.cos(angle))
        y = int(center[1] + ring_radius * math.sin(angle))
        a, b = state.as_tuple()
        pygame.draw.circle(surface, PALETTE["OUTLINE"], (x, y), node_radius + 2)
        pygame.draw.circle(surface, state_color(a, b), (x, y), node_radius)


def draw_phase_lattice(
    surface: "pygame.Surface", lattice: "Lattice", phases: np.ndarray
) -> None:
    """Draw a 2-D grid of cells colored by each node's phase."""
    width, height = surface.get_size()
    coords = [lattice.coords(i) for i in range(lattice.n_nodes)]
    grid_w = max(c[0] for c in coords) + 1
    grid_h = max(c[1] for c in coords) + 1
    cell_w = width / grid_w
    cell_h = height / grid_h
    for idx, (cx, cy, _cz) in enumerate(coords):
        color = phase_color(float(phases[idx]))
        rect = (int(cx * cell_w), int(cy * cell_h), int(cell_w) + 1, int(cell_h) + 1)
        pygame.draw.rect(surface, color, rect)


def _draw_field_panel(surface, cells, values, colorize, origin_x, panel_w) -> None:
    """Fill a panel with cells colored by ``colorize(value)`` at a mid slice."""
    grid = max(c[0] for c in cells) + 1
    cell = panel_w / grid
    for (cx, cy), value in zip(cells, values):
        color = colorize(value)
        rect = (int(origin_x + cx * cell), int(cy * cell), int(cell) + 1, int(cell) + 1)
        pygame.draw.rect(surface, color, rect)


def draw_engine(surface: "pygame.Surface", engine: "StableChaosEngine") -> None:
    """Draw the fused engine: phase hue field beside the grayscale A field."""
    width, height = surface.get_size()
    z_mid = engine.config.size // 2 if engine.config.dim == 3 else 0
    cells: list[tuple[int, int]] = []
    node_ids: list[int] = []
    for idx in range(engine.n):
        cx, cy, cz = engine.lattice.coords(idx)
        if cz == z_mid:
            cells.append((cx, cy))
            node_ids.append(idx)
    half = width // 2
    phases = [float(engine.phases[i]) for i in node_ids]
    a_values = [float(engine.states[i, 0]) for i in node_ids]
    _draw_field_panel(surface, cells, phases, phase_color, 0, half)
    _draw_field_panel(surface, cells, a_values, _gray, half, half)


def _gray(value: float) -> tuple[int, int, int]:
    """Map an A value in [-1, 1] to a grayscale RGB triple."""
    level = int((value + 1.0) / 2.0 * 255.0)
    level = max(0, min(255, level))
    return (level, level, level)
