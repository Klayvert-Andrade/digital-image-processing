import numpy as np
import pytest

from imagelab.core.models import ImageDocument, ImageMode, ImageValidationError


def test_supported_modes_are_named_for_the_user() -> None:
    assert ImageMode.GRAYSCALE.label == "Escala de cinza (8 bits)"
    assert ImageMode.RGB.label == "RGB (24 bits)"


@pytest.mark.parametrize(
    "data",
    [np.array([[1]], dtype=np.int16), np.zeros((1, 1, 2), dtype=np.uint8)],
)
def test_document_rejects_non_supported_image_arrays(data: np.ndarray) -> None:
    with pytest.raises(ImageValidationError):
        ImageDocument(data=data, mode=ImageMode.GRAYSCALE)
