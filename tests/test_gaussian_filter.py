import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.spatial import gaussian_kernel


def test_gaussian_kernel_is_symmetric_nonnegative_and_normalized() -> None:
    kernel = gaussian_kernel(window=5, sigma=1.2)

    assert np.all(kernel >= 0)
    assert kernel.sum() == pytest.approx(1.0)
    np.testing.assert_allclose(kernel, np.flip(kernel))


def test_gaussian_filter_preserves_a_constant_rgb_image() -> None:
    original = ImageDocument(data=np.full((7, 7, 3), 80, dtype=np.uint8), mode=ImageMode.RGB)
    report = ProcessController(PROCESS_CATALOG).execute(
        original, "gaussian_blur", {"window": 3, "sigma": 1.0}
    )

    np.testing.assert_array_equal(report.result.primary.data, original.data)


def test_gaussian_filter_rejects_even_or_oversized_windows() -> None:
    original = ImageDocument(data=np.zeros((3, 3), dtype=np.uint8), mode=ImageMode.GRAYSCALE)
    controller = ProcessController(PROCESS_CATALOG)

    with pytest.raises(ProcessValidationError, match="janela"):
        controller.execute(original, "gaussian_blur", {"window": 4, "sigma": 1.0})
    with pytest.raises(ProcessValidationError, match="dimensões"):
        controller.execute(original, "gaussian_blur", {"window": 5, "sigma": 1.0})
