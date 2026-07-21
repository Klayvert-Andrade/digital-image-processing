"""Generate deterministic PNG samples used in the ImageLab presentation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def save_samples(output_directory: Path) -> None:
    """Create compact grayscale and RGB examples covering all demonstration cases."""
    output_directory.mkdir(parents=True, exist_ok=True)
    constant = np.full((128, 128), 128, dtype=np.uint8)
    impulse = constant.copy()
    impulse[64, 64] = 255
    step = np.zeros((128, 128), dtype=np.uint8)
    step[:, 64:] = 255
    gradient = np.tile(np.arange(128, dtype=np.uint8) * 2, (128, 1))
    rgb_blocks = np.zeros((128, 128, 3), dtype=np.uint8)
    rgb_blocks[:64, :64] = (255, 0, 0)
    rgb_blocks[:64, 64:] = (0, 255, 0)
    rgb_blocks[64:, :64] = (0, 0, 255)
    rgb_blocks[64:, 64:] = (255, 255, 0)
    rng = np.random.default_rng(2026)
    noisy = np.clip(gradient.astype(np.float64) + rng.normal(0, 20, gradient.shape), 0, 255).astype(
        np.uint8
    )
    noisy[::11, ::13] = 255
    noisy[::13, ::11] = 0
    for name, pixels in {
        "constant.png": constant,
        "impulse.png": impulse,
        "step.png": step,
        "gradient.png": gradient,
        "rgb-blocks.png": rgb_blocks,
        "noisy-gradient.png": noisy,
    }.items():
        Image.fromarray(pixels).save(output_directory / name)


if __name__ == "__main__":
    save_samples(Path(__file__).resolve().parents[1] / "assets" / "samples")
