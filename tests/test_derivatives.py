import cv2
import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.derivatives import laplacian_response, sobel_response
from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.spatial import gaussian_blur_values


def _gray(values: list[list[int]]) -> ImageDocument:
    return ImageDocument(data=np.array(values, dtype=np.uint8), mode=ImageMode.GRAYSCALE)


def test_unsharp_mask_uses_the_documented_float_mask_formula() -> None:
    document = _gray([[0, 0, 0], [0, 100, 0], [0, 0, 0]])
    result = (
        ProcessController(PROCESS_CATALOG)
        .execute(document, "unsharp_mask", {"window": 3, "sigma": 1.0, "gain": 1.5})
        .result.primary
    )

    blurred = gaussian_blur_values(document, window=3, sigma=1.0)
    expected = np.floor(np.clip(document.data + 1.5 * (document.data - blurred), 0, 255) + 0.5)

    np.testing.assert_array_equal(result.data, expected.astype(np.uint8))


def test_laplacian_enhancement_uses_signed_response_and_adjusts_it() -> None:
    document = _gray([[0, 0, 0], [0, 100, 0], [0, 0, 0]])
    report = ProcessController(PROCESS_CATALOG).execute(document, "laplacian", {"window": 3})
    response = laplacian_response(document, window=3)
    expected = np.floor(np.clip(document.data.astype(np.float64) - response, 0, 255) + 0.5)
    adjusted = report.result.accessories["Laplaciano ajustado"].data

    np.testing.assert_array_equal(report.result.primary.data, expected.astype(np.uint8))
    np.testing.assert_array_equal(
        adjusted,
        np.floor(
            255 * (response - response.min()) / (response.max() - response.min()) + 0.5
        ).astype(np.uint8),
    )
    assert response.dtype == np.float64


def test_constant_laplacian_adjustment_is_zero() -> None:
    document = _gray([[40, 40, 40], [40, 40, 40], [40, 40, 40]])
    report = ProcessController(PROCESS_CATALOG).execute(document, "laplacian", {"window": 3})

    np.testing.assert_array_equal(report.result.primary.data, document.data)
    np.testing.assert_array_equal(report.result.accessories["Laplaciano ajustado"].data, 0)


def test_sobel_matches_cv64f_l1_magnitude_and_clips_without_normalization() -> None:
    document = _gray([[0, 0, 255], [0, 0, 255], [0, 0, 255]])
    report = ProcessController(PROCESS_CATALOG).execute(document, "sobel", {"window": 3})
    response = sobel_response(document, window=3)
    expected = np.floor(np.clip(response.magnitude, 0, 255) + 0.5).astype(np.uint8)

    np.testing.assert_array_equal(report.result.primary.data, expected)
    assert np.any(response.magnitude[:, 1] > 0)
    assert response.horizontal.dtype == np.float64
    assert response.vertical.dtype == np.float64
    assert report.result.primary_label == "Magnitude de Sobel"


def test_rgb_derivatives_are_independent_per_channel_and_sobel_is_named() -> None:
    red_step = np.array([[0, 0, 255], [0, 0, 255], [0, 0, 255]], dtype=np.uint8)
    pixels = np.stack((red_step, np.zeros_like(red_step), np.zeros_like(red_step)), axis=-1)
    document = ImageDocument(data=pixels, mode=ImageMode.RGB)
    report = ProcessController(PROCESS_CATALOG).execute(document, "sobel", {"window": 3})
    laplacian = ProcessController(PROCESS_CATALOG).execute(document, "laplacian", {"window": 3})

    assert report.result.primary.mode is ImageMode.RGB
    assert report.result.primary_label == "Composição RGB das magnitudes de Sobel"
    assert np.any(report.result.primary.data[..., 0] > 0)
    np.testing.assert_array_equal(report.result.primary.data[..., 1:], 0)
    assert laplacian.result.accessories["Laplaciano ajustado"].mode is ImageMode.RGB


@pytest.mark.parametrize("identifier", ["laplacian", "sobel"])
@pytest.mark.parametrize("window", [4, 9])
def test_derivatives_accept_only_documented_windows(identifier: str, window: int) -> None:
    controller = ProcessController(PROCESS_CATALOG)

    with pytest.raises(ProcessValidationError, match="[Jj]anela"):
        controller.execute(_gray([[0] * 7 for _ in range(7)]), identifier, {"window": window})


def test_unsharp_rejects_negative_gain() -> None:
    with pytest.raises(ProcessValidationError, match="[Gg]anho"):
        ProcessController(PROCESS_CATALOG).execute(
            _gray([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
            "unsharp_mask",
            {"window": 3, "sigma": 1.0, "gain": -0.1},
        )


def test_laplacian_matches_opencv_reference_at_borders() -> None:
    document = _gray([[10, 20, 30], [40, 50, 60], [70, 80, 90]])

    actual = laplacian_response(document, window=3)
    expected = cv2.Laplacian(document.data, cv2.CV_64F, ksize=3, borderType=cv2.BORDER_REFLECT_101)

    np.testing.assert_array_equal(actual, expected)
