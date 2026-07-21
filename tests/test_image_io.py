from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from imagelab.core.models import ImageMode
from imagelab.infrastructure.image_io import ImageLoadError, ImageSaveError, load_png, save_png


def test_load_png_preserves_grayscale_uint8_mode_and_values(tmp_path: Path) -> None:
    pixels = np.array([[0, 127], [200, 255]], dtype=np.uint8)
    path = tmp_path / "gray.png"
    Image.fromarray(pixels).save(path)

    document = load_png(path)

    assert document.mode is ImageMode.GRAYSCALE
    assert document.data.dtype == np.uint8
    assert not document.data.flags.writeable
    np.testing.assert_array_equal(document.data, pixels)


def test_load_png_preserves_rgb_channel_order(tmp_path: Path) -> None:
    pixels = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]]], dtype=np.uint8)
    path = tmp_path / "rgb.png"
    Image.fromarray(pixels).save(path)

    document = load_png(path)

    assert document.mode is ImageMode.RGB
    np.testing.assert_array_equal(document.data, pixels)


@pytest.mark.parametrize(
    ("name", "mode"),
    [("palette.png", "P"), ("alpha.png", "RGBA"), ("high-depth.png", "I;16")],
)
def test_load_png_rejects_unsupported_png_modes(tmp_path: Path, name: str, mode: str) -> None:
    path = tmp_path / name
    if mode == "P":
        Image.fromarray(np.array([[0, 1]], dtype=np.uint8)).convert("P").save(path)
    elif mode == "RGBA":
        Image.fromarray(np.zeros((1, 1, 4), dtype=np.uint8)).save(path)
    else:
        Image.fromarray(np.array([[65535]], dtype=np.uint16)).save(path)

    with pytest.raises(ImageLoadError, match="compatível"):
        load_png(path)


def test_load_png_rejects_non_png_paths(tmp_path: Path) -> None:
    path = tmp_path / "other.jpg"
    Image.fromarray(np.array([[1]], dtype=np.uint8)).save(path)

    with pytest.raises(ImageLoadError, match="PNG"):
        load_png(path)


def test_load_png_rejects_jpeg_content_with_a_png_extension(tmp_path: Path) -> None:
    path = tmp_path / "disguised.png"
    Image.fromarray(np.array([[1]], dtype=np.uint8)).save(path, format="JPEG")

    with pytest.raises(ImageLoadError, match="PNG válido"):
        load_png(path)


def test_save_png_round_trips_without_overwriting_source(tmp_path: Path) -> None:
    pixels = np.array([[0, 127], [200, 255]], dtype=np.uint8)
    source = tmp_path / "source.png"
    destination = tmp_path / "result.png"
    Image.fromarray(pixels).save(source)
    document = load_png(source)

    save_png(destination, document, protected_source=source)

    assert destination.exists()
    np.testing.assert_array_equal(load_png(destination).data, pixels)
    with pytest.raises(ValueError, match="sobrescrever"):
        save_png(source, document, protected_source=source)

    with pytest.raises(ImageSaveError, match="extensão"):
        save_png(tmp_path / "result.jpg", document)
