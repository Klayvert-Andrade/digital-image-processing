import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.frequency import (
    gaussian_frequency_filter,
    gaussian_frequency_mask,
    maximum_cutoff,
    padded_shape,
)
from imagelab.core.models import ImageDocument, ImageMode


def _gray(data: np.ndarray) -> ImageDocument:
    return ImageDocument(data=data.astype(np.uint8), mode=ImageMode.GRAYSCALE)


def test_gaussian_frequency_mask_is_centered_and_high_pass_is_its_complement() -> None:
    low_pass = gaussian_frequency_mask((8, 10), cutoff=2.0)
    high_pass = gaussian_frequency_mask((8, 10), cutoff=2.0, high_pass=True)

    assert low_pass[4, 5] == pytest.approx(1.0)
    assert high_pass[4, 5] == pytest.approx(0.0)
    np.testing.assert_allclose(low_pass + high_pass, 1.0)


def test_frequency_filter_uses_doubled_shape_and_normalized_cutoff_is_equivalent() -> None:
    document = _gray(np.arange(15).reshape(3, 5))
    cutoff = maximum_cutoff(document) * 0.4

    in_bins = gaussian_frequency_filter(
        document, cutoff=cutoff, normalized_cutoff=False, high_pass=False
    )
    normalized = gaussian_frequency_filter(
        document, cutoff=0.4, normalized_cutoff=True, high_pass=False
    )

    assert padded_shape(document) == (6, 10)
    assert in_bins.data.shape == document.data.shape
    np.testing.assert_array_equal(in_bins.data, normalized.data)


def test_frequency_filters_preserve_rgb_channels_independently() -> None:
    red = np.array([[0, 0, 255], [0, 0, 255], [0, 0, 255]], dtype=np.uint8)
    document = ImageDocument(
        data=np.stack((red, np.zeros_like(red), np.zeros_like(red)), axis=-1), mode=ImageMode.RGB
    )
    result = gaussian_frequency_filter(
        document, cutoff=1.0, normalized_cutoff=True, high_pass=False
    )

    assert result.mode is ImageMode.RGB
    assert result.data.shape == document.data.shape
    np.testing.assert_array_equal(result.data[..., 1:], 0)


def test_frequency_filter_reconstructs_an_impulse_without_rescaling() -> None:
    impulse = np.zeros((5, 5), dtype=np.uint8)
    impulse[2, 2] = 255
    result = gaussian_frequency_filter(
        _gray(impulse), cutoff=1.0, normalized_cutoff=True, high_pass=False
    )

    assert result.data.shape == impulse.shape
    assert result.data.dtype == np.uint8
    assert 0 < result.data[2, 2] < 255


def test_constant_image_behaves_as_expected_away_from_zero_padding_boundary() -> None:
    document = _gray(np.full((9, 9), 100, dtype=np.uint8))
    cutoff = maximum_cutoff(document)
    low_pass = gaussian_frequency_filter(
        document, cutoff=cutoff, normalized_cutoff=False, high_pass=False
    )
    high_pass = gaussian_frequency_filter(
        document, cutoff=cutoff, normalized_cutoff=False, high_pass=True
    )

    np.testing.assert_allclose(low_pass.data[2:-2, 2:-2], 100, atol=1)
    np.testing.assert_allclose(high_pass.data[2:-2, 2:-2], 0, atol=1)


def test_frequency_catalog_validates_dynamic_cutoff_bounds() -> None:
    document = _gray(np.zeros((3, 3), dtype=np.uint8))
    controller = ProcessController(PROCESS_CATALOG)

    with pytest.raises(ProcessValidationError, match="frequência"):
        controller.execute(
            document,
            "gaussian_low_pass_frequency",
            {"cutoff": maximum_cutoff(document) + 1, "normalized_cutoff": False},
        )
    with pytest.raises(ProcessValidationError, match="normalizada"):
        controller.execute(
            document,
            "gaussian_high_pass_frequency",
            {"cutoff": 1.1, "normalized_cutoff": True},
        )
