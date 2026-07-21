import numpy as np

from imagelab.application.processing import ProcessController
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument, ImageMode


def rgb_document(pixels: np.ndarray) -> ImageDocument:
    return ImageDocument(data=pixels.astype(np.uint8), mode=ImageMode.RGB)


def test_rgb_decomposition_returns_each_channel_as_grayscale() -> None:
    original = rgb_document(np.array([[[1, 2, 3], [4, 5, 6]]]))

    result = ProcessController(PROCESS_CATALOG).execute(original, "decompose_rgb", {})

    assert result.result.primary.mode is ImageMode.GRAYSCALE
    np.testing.assert_array_equal(result.result.accessories["R"].data, [[1, 4]])
    np.testing.assert_array_equal(result.result.accessories["G"].data, [[2, 5]])
    np.testing.assert_array_equal(result.result.accessories["B"].data, [[3, 6]])


def test_hsv_decomposition_uses_conventional_value_and_deterministic_hue_mapping() -> None:
    original = rgb_document(np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]]]))

    result = ProcessController(PROCESS_CATALOG).execute(original, "decompose_hsv", {})

    np.testing.assert_array_equal(result.result.accessories["H"].data, [[0, 85, 170, 0]])
    np.testing.assert_array_equal(result.result.accessories["S"].data, [[255, 255, 255, 0]])
    np.testing.assert_array_equal(result.result.accessories["V"].data, [[255, 255, 255, 255]])


def test_color_decompositions_are_available_only_for_rgb() -> None:
    gray = ImageDocument(data=np.zeros((1, 1), dtype=np.uint8), mode=ImageMode.GRAYSCALE)

    assert not PROCESS_CATALOG.is_compatible("decompose_rgb", gray.mode)
    assert not PROCESS_CATALOG.is_compatible("decompose_hsv", gray.mode)
