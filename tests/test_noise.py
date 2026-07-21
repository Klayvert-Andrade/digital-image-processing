import numpy as np
import pytest

from imagelab.application.processing import ProcessController, ProcessValidationError
from imagelab.core.catalog import PROCESS_CATALOG
from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.noise import ImpulseKind, gaussian_noise, impulse_noise


def _gray(shape: tuple[int, int] = (4, 5), value: int = 100) -> ImageDocument:
    return ImageDocument(data=np.full(shape, value, dtype=np.uint8), mode=ImageMode.GRAYSCALE)


def test_zero_gaussian_noise_is_identity() -> None:
    document = _gray()

    result = gaussian_noise(document, mu=0, sigma=0, rng=np.random.default_rng(1))

    np.testing.assert_array_equal(result.data, document.data)


def test_gaussian_noise_uses_injected_generator_and_expected_statistics() -> None:
    document = _gray((200, 200), value=100)
    result = gaussian_noise(document, mu=10, sigma=4, rng=np.random.default_rng(17))

    delta = result.data.astype(np.float64) - document.data
    assert delta.mean() == pytest.approx(10, abs=0.15)
    assert delta.std() == pytest.approx(4, abs=0.15)


@pytest.mark.parametrize(("kind", "value"), [("salt", 255), ("pepper", 0)])
def test_single_impulse_noise_changes_the_exact_rounded_coordinate_count(
    kind: ImpulseKind, value: int
) -> None:
    document = _gray((3, 4))
    result = impulse_noise(
        document,
        density=0.25,
        kind=kind,
        rng=np.random.default_rng(3),
    )

    assert np.count_nonzero(result.data == value) == 3
    assert np.count_nonzero(result.data != 100) == 3


def test_salt_and_pepper_divides_exact_selection_without_replacement() -> None:
    document = _gray((2, 5))
    result = impulse_noise(
        document,
        density=0.5,
        salt_proportion=0.4,
        kind="salt_pepper",
        rng=np.random.default_rng(4),
    )

    assert np.count_nonzero(result.data == 255) == 2
    assert np.count_nonzero(result.data == 0) == 3
    assert np.count_nonzero(result.data != 100) == 5


@pytest.mark.parametrize(("kind", "value"), [("salt", 255), ("pepper", 0)])
@pytest.mark.parametrize("density", [0.0, 1.0])
def test_impulsive_density_extremes_are_exact(
    kind: ImpulseKind, value: int, density: float
) -> None:
    document = _gray((2, 3))
    result = impulse_noise(
        document,
        density=density,
        kind=kind,
        rng=np.random.default_rng(5),
    )

    expected = 0 if density == 0 else document.data.size
    assert np.count_nonzero(result.data == value) == expected


def test_rgb_impulses_change_entire_pixels_not_individual_components() -> None:
    document = ImageDocument(
        data=np.full((2, 2, 3), [10, 20, 30], dtype=np.uint8), mode=ImageMode.RGB
    )
    result = impulse_noise(
        document, density=0.5, kind="salt_pepper", salt_proportion=0.5, rng=np.random.default_rng(9)
    )

    changed = np.any(result.data != document.data, axis=-1)
    assert changed.sum() == 2
    for pixel in result.data[changed]:
        assert np.all(pixel == 0) or np.all(pixel == 255)


def test_noise_catalog_rejects_invalid_parameters() -> None:
    controller = ProcessController(PROCESS_CATALOG)

    with pytest.raises(ProcessValidationError, match="Média"):
        controller.execute(_gray(), "gaussian_noise", {"mu": 256, "sigma": 1})
    with pytest.raises(ProcessValidationError, match="Densidade"):
        controller.execute(_gray(), "salt_noise", {"density": 1.1})
