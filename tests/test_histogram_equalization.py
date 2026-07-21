import numpy as np

from imagelab.application.processing import ProcessController
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.histogram import equalization_lut, histogram_counts
from imagelab.core.models import ImageDocument, ImageMode


def test_equalization_lut_follows_the_slide_cdf_without_cdf_min() -> None:
    counts = np.zeros(256, dtype=np.int64)
    counts[0] = 1
    counts[10] = 3

    lut = equalization_lut(counts)

    assert lut[0] == 64
    assert lut[10] == 255


def test_constant_image_equalizes_to_white_under_the_adopted_convention() -> None:
    original = ImageDocument(data=np.full((2, 2), 50, dtype=np.uint8), mode=ImageMode.GRAYSCALE)

    report = ProcessController(PROCESS_CATALOG).execute(original, "histogram_equalization", {})

    np.testing.assert_array_equal(report.result.primary.data, np.full((2, 2), 255, dtype=np.uint8))
    assert set(report.result.accessories) == {"Histograma antes", "Histograma depois"}


def test_histogram_counts_all_pixels_in_256_bins() -> None:
    image = np.array([[0, 0, 255]], dtype=np.uint8)
    counts = histogram_counts(image)

    assert counts.shape == (256,)
    assert counts.sum() == 3
    assert counts[0] == 2
    assert counts[255] == 1
