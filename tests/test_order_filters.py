import numpy as np
import pytest
from scipy import ndimage

from imagelab.application.processing import ProcessController
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.spatial import order_filter


def test_order_filters_handle_predictable_impulses() -> None:
    salt = ImageDocument(
        data=np.array([[10, 10, 10], [10, 255, 10], [10, 10, 10]], dtype=np.uint8),
        mode=ImageMode.GRAYSCALE,
    )
    pepper = ImageDocument(
        data=np.array([[200, 200, 200], [200, 0, 200], [200, 200, 200]], dtype=np.uint8),
        mode=ImageMode.GRAYSCALE,
    )
    controller = ProcessController(PROCESS_CATALOG)

    assert controller.execute(salt, "median_filter", {"window": 3}).result.primary.data[1, 1] == 10
    assert controller.execute(salt, "minimum_filter", {"window": 3}).result.primary.data[1, 1] == 10
    assert (
        controller.execute(pepper, "maximum_filter", {"window": 3}).result.primary.data[1, 1] == 200
    )


def test_order_filter_processes_rgb_channels_independently() -> None:
    pixels = np.array(
        [
            [[1, 20, 255], [100, 30, 0], [2, 40, 100]],
            [[3, 50, 200], [90, 60, 10], [5, 70, 90]],
            [[8, 80, 180], [80, 90, 20], [9, 100, 80]],
        ],
        dtype=np.uint8,
    )
    original = ImageDocument(data=pixels, mode=ImageMode.RGB)

    result = ProcessController(PROCESS_CATALOG).execute(original, "minimum_filter", {"window": 3})

    assert result.result.primary.mode is ImageMode.RGB
    assert result.result.primary.data.shape == pixels.shape


@pytest.mark.parametrize(
    ("operation", "reference"),
    [
        ("median", ndimage.median_filter),
        ("minimum", ndimage.minimum_filter),
        ("maximum", ndimage.maximum_filter),
    ],
)
def test_order_filters_match_scipy_mirror_at_borders(
    operation: str,
    reference: object,
) -> None:
    pixels = np.array(
        [
            [[20, 4, 99], [3, 100, 7], [18, 1, 60]],
            [[8, 90, 2], [255, 40, 35], [5, 200, 3]],
            [[70, 6, 80], [1, 120, 4], [50, 9, 220]],
        ],
        dtype=np.uint8,
    )
    document = ImageDocument(data=pixels, mode=ImageMode.RGB)

    actual = order_filter(document, window=3, operation=operation)
    expected = reference(pixels, size=(3, 3, 1), mode="mirror")

    np.testing.assert_array_equal(actual.data, expected)


@pytest.mark.parametrize("window", [2, 32])
def test_order_filters_reject_invalid_window(window: int) -> None:
    document = ImageDocument(data=np.full((3, 3), 20, dtype=np.uint8), mode=ImageMode.GRAYSCALE)

    with pytest.raises(ValueError, match="janela"):
        order_filter(document, window=window, operation="median")


def test_order_filters_reject_window_larger_than_image() -> None:
    document = ImageDocument(data=np.full((2, 2), 20, dtype=np.uint8), mode=ImageMode.GRAYSCALE)

    with pytest.raises(ValueError, match="dimensões"):
        order_filter(document, window=3, operation="median")
