import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.butterworth import butterworth_frequency_filter, butterworth_mask
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.frequency import maximum_cutoff
from imagelab.core.models import ImageDocument, ImageMode


def _gray(data: np.ndarray) -> ImageDocument:
    return ImageDocument(data=data.astype(np.uint8), mode=ImageMode.GRAYSCALE)


def test_butterworth_mask_has_expected_center_cutoff_and_complement() -> None:
    low_pass = butterworth_mask((12, 12), cutoff=2.0, order=3)
    high_pass = butterworth_mask((12, 12), cutoff=2.0, order=3, high_pass=True)

    assert low_pass[6, 6] == pytest.approx(1.0)
    assert high_pass[6, 6] == pytest.approx(0.0)
    assert low_pass[6, 8] == pytest.approx(0.5)
    np.testing.assert_allclose(low_pass + high_pass, 1.0)


def test_higher_butterworth_order_makes_transition_sharper_without_nonfinite_values() -> None:
    low_order = butterworth_mask((30, 30), cutoff=4.0, order=1)
    high_order = butterworth_mask((30, 30), cutoff=4.0, order=20)

    assert high_order[15, 21] < low_order[15, 21]
    assert np.isfinite(high_order).all()


def test_butterworth_filter_preserves_mode_dimensions_and_rgb_channels() -> None:
    red = np.array([[0, 0, 255], [0, 0, 255], [0, 0, 255]], dtype=np.uint8)
    document = ImageDocument(
        data=np.stack((red, np.zeros_like(red), np.zeros_like(red)), axis=-1), mode=ImageMode.RGB
    )
    result = butterworth_frequency_filter(
        document, cutoff=0.5, normalized_cutoff=True, order=2, high_pass=False
    )

    assert result.mode is ImageMode.RGB
    assert result.data.shape == document.data.shape
    np.testing.assert_array_equal(result.data[..., 1:], 0)


def test_all_frequency_filters_are_exposed_for_gray_and_rgb() -> None:
    identifiers = (
        "gaussian_low_pass_frequency",
        "gaussian_high_pass_frequency",
        "butterworth_low_pass_frequency",
        "butterworth_high_pass_frequency",
    )

    for identifier in identifiers:
        definition = PROCESS_CATALOG.get(identifier)
        assert definition.category == "Filtros de frequência"
        assert definition.compatible_modes == frozenset({ImageMode.GRAYSCALE, ImageMode.RGB})


def test_butterworth_constant_and_sinusoid_have_expected_interior_behavior() -> None:
    constant = _gray(np.full((9, 9), 100, dtype=np.uint8))
    cutoff = maximum_cutoff(constant)
    low_pass = butterworth_frequency_filter(
        constant, cutoff=cutoff, normalized_cutoff=False, order=1, high_pass=False
    )
    high_pass = butterworth_frequency_filter(
        constant, cutoff=cutoff, normalized_cutoff=False, order=1, high_pass=True
    )
    sinusoid = _gray(
        np.tile(((np.sin(np.arange(16) * np.pi / 2) + 1) * 127.5).astype(np.uint8), (16, 1))
    )
    filtered_sinusoid = butterworth_frequency_filter(
        sinusoid, cutoff=0.2, normalized_cutoff=True, order=4, high_pass=False
    )

    np.testing.assert_allclose(low_pass.data[2:-2, 2:-2], 100, atol=1)
    np.testing.assert_allclose(high_pass.data[2:-2, 2:-2], 0, atol=1)
    assert filtered_sinusoid.data.std() < sinusoid.data.std()


@pytest.mark.parametrize("order", [0, 21, 1.5])
def test_butterworth_catalog_rejects_invalid_order(order: object) -> None:
    controller = ProcessController(PROCESS_CATALOG)

    with pytest.raises(ProcessValidationError, match="Ordem"):
        controller.execute(
            _gray(np.zeros((5, 5))),
            "butterworth_low_pass_frequency",
            {"cutoff": 0.5, "normalized_cutoff": True, "order": order},
        )
