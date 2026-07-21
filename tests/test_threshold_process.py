import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.metrics import calculate_metrics
from imagelab.core.models import ImageDocument, ImageMode


def grayscale_document(values: list[list[int]]) -> ImageDocument:
    return ImageDocument(data=np.array(values, dtype=np.uint8), mode=ImageMode.GRAYSCALE)


def test_threshold_catalog_declares_its_parameter_and_gray_compatibility() -> None:
    definition = PROCESS_CATALOG.get("threshold")

    assert definition.category == "Transformações de intensidade"
    assert definition.compatible_modes == frozenset({ImageMode.GRAYSCALE})
    assert definition.parameters[0].key == "k"
    assert definition.parameters[0].minimum == 0
    assert definition.parameters[0].maximum == 255


def test_threshold_is_inclusive_at_k() -> None:
    controller = ProcessController(PROCESS_CATALOG)
    original = grayscale_document([[0, 127, 128, 255]])

    execution = controller.execute(original, "threshold", {"k": 128})

    np.testing.assert_array_equal(execution.result.primary.data, [[0, 0, 255, 255]])
    assert execution.result.primary.mode is ImageMode.GRAYSCALE
    assert execution.duration_ms >= 0


def test_threshold_uses_the_original_again_on_each_execution() -> None:
    controller = ProcessController(PROCESS_CATALOG)
    original = grayscale_document([[50, 200]])

    first = controller.execute(original, "threshold", {"k": 100})
    second = controller.execute(original, "threshold", {"k": 220})

    np.testing.assert_array_equal(first.result.primary.data, [[0, 255]])
    np.testing.assert_array_equal(second.result.primary.data, [[0, 0]])
    np.testing.assert_array_equal(original.data, [[50, 200]])


@pytest.mark.parametrize("invalid_k", [-1, 256, 12.5, "128"])
def test_threshold_rejects_invalid_parameter_values(invalid_k: object) -> None:
    controller = ProcessController(PROCESS_CATALOG)

    with pytest.raises(ProcessValidationError, match="k"):
        controller.execute(grayscale_document([[1]]), "threshold", {"k": invalid_k})


def test_threshold_is_incompatible_with_rgb() -> None:
    controller = ProcessController(PROCESS_CATALOG)
    rgb = ImageDocument(data=np.zeros((1, 1, 3), dtype=np.uint8), mode=ImageMode.RGB)

    assert not PROCESS_CATALOG.is_compatible("threshold", rgb.mode)
    with pytest.raises(ProcessValidationError, match="não é compatível"):
        controller.execute(rgb, "threshold", {"k": 128})


def test_metrics_are_reported_per_channel_for_rgb() -> None:
    rgb = ImageDocument(
        data=np.array([[[0, 10, 20], [100, 110, 120]]], dtype=np.uint8), mode=ImageMode.RGB
    )

    metrics = calculate_metrics(rgb)

    assert metrics.mode is ImageMode.RGB
    assert metrics.width == 2
    assert metrics.height == 1
    assert metrics.channels["R"].minimum == 0
    assert metrics.channels["G"].maximum == 110
    assert metrics.channels["B"].mean == 70.0
