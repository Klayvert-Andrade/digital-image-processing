import math

import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument, ImageMode


def document(values: np.ndarray, mode: ImageMode) -> ImageDocument:
    return ImageDocument(data=values.astype(np.uint8), mode=mode)


def test_logarithmic_default_maps_255_to_255() -> None:
    original = document(np.array([[0, 255]]), ImageMode.GRAYSCALE)
    result = ProcessController(PROCESS_CATALOG).execute(
        original, "logarithmic", {"c": 255 / math.log(256)}
    )

    np.testing.assert_array_equal(result.result.primary.data, [[0, 255]])


def test_power_identity_preserves_rgb() -> None:
    pixels = np.array([[[0, 10, 255], [128, 64, 32]]])
    original = document(pixels, ImageMode.RGB)
    result = ProcessController(PROCESS_CATALOG).execute(original, "power", {"c": 1.0, "gamma": 1.0})

    np.testing.assert_array_equal(result.result.primary.data, pixels)


def test_intensity_slicing_honors_inclusive_range_and_background_policy() -> None:
    original = document(np.array([[9, 10, 20, 21]]), ImageMode.GRAYSCALE)
    controller = ProcessController(PROCESS_CATALOG)

    preserved = controller.execute(
        original, "intensity_slicing", {"a": 10, "b": 20, "preserve_background": True}
    )
    zeroed = controller.execute(
        original, "intensity_slicing", {"a": 10, "b": 20, "preserve_background": False}
    )

    np.testing.assert_array_equal(preserved.result.primary.data, [[9, 255, 255, 21]])
    np.testing.assert_array_equal(zeroed.result.primary.data, [[0, 255, 255, 0]])


def test_slicing_rejects_inverted_range() -> None:
    original = document(np.array([[10]]), ImageMode.GRAYSCALE)

    with pytest.raises(ProcessValidationError, match="A"):
        ProcessController(PROCESS_CATALOG).execute(
            original, "intensity_slicing", {"a": 20, "b": 10, "preserve_background": True}
        )
