import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.adaptive import adaptive_median_filter
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument, ImageMode


def _gray(data: np.ndarray) -> ImageDocument:
    return ImageDocument(data=data.astype(np.uint8), mode=ImageMode.GRAYSCALE)


@pytest.mark.parametrize("impulse", [0, 255])
def test_adaptive_median_replaces_isolated_salt_or_pepper(impulse: int) -> None:
    pixels = np.full((3, 3), 100, dtype=np.uint8)
    pixels[1, 1] = impulse

    result = adaptive_median_filter(_gray(pixels), maximum_window=3)

    assert result.data[1, 1] == 100


def test_adaptive_median_preserves_a_non_impulsive_pixel_in_stage_b() -> None:
    pixels = np.array([[0, 10, 255], [10, 10, 10], [10, 10, 10]], dtype=np.uint8)

    result = adaptive_median_filter(_gray(pixels), maximum_window=3)

    assert result.data[1, 1] == 10


def test_adaptive_median_grows_window_then_uses_the_valid_median() -> None:
    pixels = np.full((5, 5), 10, dtype=np.uint8)
    pixels[1:4, 1:4] = 0
    pixels[2, 2] = 255

    with_small_limit = adaptive_median_filter(_gray(pixels), maximum_window=3)
    with_growth = adaptive_median_filter(_gray(pixels), maximum_window=5)

    assert with_small_limit.data[2, 2] == 0
    assert with_growth.data[2, 2] == 10


def test_adaptive_median_preserves_rgb_channels_and_border_dimensions() -> None:
    red = np.full((3, 3), 30, dtype=np.uint8)
    red[0, 0] = 255
    green = np.full((3, 3), 60, dtype=np.uint8)
    blue = np.full((3, 3), 90, dtype=np.uint8)
    document = ImageDocument(data=np.stack((red, green, blue), axis=-1), mode=ImageMode.RGB)

    result = adaptive_median_filter(document, maximum_window=3)

    assert result.mode is ImageMode.RGB
    assert result.data.shape == document.data.shape
    assert result.data[0, 0, 0] == 30
    np.testing.assert_array_equal(result.data[..., 1], green)
    np.testing.assert_array_equal(result.data[..., 2], blue)


@pytest.mark.parametrize("maximum_window", [2, 32])
def test_adaptive_median_rejects_invalid_maximum_window(maximum_window: int) -> None:
    with pytest.raises(ValueError, match="janela"):
        adaptive_median_filter(_gray(np.zeros((3, 3))), maximum_window=maximum_window)


def test_adaptive_median_catalog_reports_oversized_window() -> None:
    with pytest.raises(ProcessValidationError, match="dimensões"):
        ProcessController(PROCESS_CATALOG).execute(
            _gray(np.zeros((3, 3))), "adaptive_median_filter", {"maximum_window": 5}
        )
