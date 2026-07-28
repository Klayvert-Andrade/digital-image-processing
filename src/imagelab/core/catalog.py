"""The canonical catalog of ImageLab processes and parameter contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import log
from numbers import Integral, Real
from types import MappingProxyType
from typing import TypeAlias

from imagelab.core.models import ImageDocument, ImageMode
from imagelab.core.noise import ImpulseKind
from imagelab.core.results import ProcessResult

ParameterValue: TypeAlias = bool | float | int | str
ProcessExecutor: TypeAlias = Callable[[ImageDocument, Mapping[str, ParameterValue]], ProcessResult]


class ParameterKind(StrEnum):
    """Control types understood by the desktop parameter form."""

    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CHOICE = "choice"


class CatalogValidationError(ValueError):
    """Raised when a process definition or supplied parameter is invalid."""


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """A typed, user-facing parameter accepted by a process."""

    key: str
    label: str
    kind: ParameterKind
    default: ParameterValue
    minimum: float | int | None = None
    maximum: float | int | None = None
    unit: str | None = None
    choices: tuple[str, ...] = ()

    def validate(self, value: object) -> ParameterValue:
        """Validate and normalize one externally supplied parameter value."""
        if self.kind is ParameterKind.INTEGER:
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise CatalogValidationError(f"{self.label} deve ser um número inteiro.")
            return self._validate_number(int(value))
        if self.kind is ParameterKind.NUMBER:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise CatalogValidationError(f"{self.label} deve ser um número.")
            return self._validate_number(float(value))

        if self.kind is ParameterKind.BOOLEAN:
            if not isinstance(value, bool):
                raise CatalogValidationError(f"{self.label} deve ser verdadeiro ou falso.")
            return value
        if not isinstance(value, str) or value not in self.choices:
            choices = ", ".join(self.choices)
            raise CatalogValidationError(f"{self.label} deve ser uma das opções: {choices}.")
        return value

    def _validate_number(self, value: int | float) -> int | float:
        if self.minimum is not None and value < self.minimum:
            raise CatalogValidationError(f"{self.label} deve ser maior ou igual a {self.minimum}.")
        if self.maximum is not None and value > self.maximum:
            raise CatalogValidationError(f"{self.label} deve ser menor ou igual a {self.maximum}.")
        return value


@dataclass(frozen=True, slots=True)
class ProcessDefinition:
    """Metadata and executable behavior for one selectable PDI process."""

    identifier: str
    label: str
    category: str
    compatible_modes: frozenset[ImageMode]
    parameters: tuple[ParameterSpec, ...]
    executor: ProcessExecutor
    description: str = ""

    def validate_parameters(self, values: Mapping[str, object]) -> Mapping[str, ParameterValue]:
        """Require exactly the declared parameter keys and validate every value."""
        expected_keys = {parameter.key for parameter in self.parameters}
        supplied_keys = set(values)
        missing_keys = expected_keys - supplied_keys
        unknown_keys = supplied_keys - expected_keys
        if missing_keys:
            raise CatalogValidationError(f"Parâmetro ausente: {sorted(missing_keys)[0]}.")
        if unknown_keys:
            raise CatalogValidationError(f"Parâmetro desconhecido: {sorted(unknown_keys)[0]}.")
        return MappingProxyType(
            {
                parameter.key: parameter.validate(values[parameter.key])
                for parameter in self.parameters
            }
        )


class ProcessCatalog:
    """Immutable lookup and compatibility API for all process definitions."""

    def __init__(self, definitions: tuple[ProcessDefinition, ...]) -> None:
        by_identifier = {definition.identifier: definition for definition in definitions}
        if len(by_identifier) != len(definitions):
            raise CatalogValidationError("Cada processo deve ter um identificador único.")
        self._definitions = MappingProxyType(by_identifier)

    def get(self, identifier: str) -> ProcessDefinition:
        try:
            return self._definitions[identifier]
        except KeyError as error:
            raise CatalogValidationError(f"Processo desconhecido: {identifier}.") from error

    def all(self) -> tuple[ProcessDefinition, ...]:
        return tuple(self._definitions.values())

    def is_compatible(self, identifier: str, mode: ImageMode) -> bool:
        return mode in self.get(identifier).compatible_modes


def _threshold_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.intensity import threshold

    return ProcessResult(primary=threshold(document, k=int(parameters["k"])))


def _rgb_decomposition_executor(
    document: ImageDocument, _: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.color import decompose_rgb

    return decompose_rgb(document)


def _hsv_decomposition_executor(
    document: ImageDocument, _: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.color import decompose_hsv

    return decompose_hsv(document)


def _logarithmic_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.intensity import logarithmic

    return ProcessResult(primary=logarithmic(document, c=float(parameters["c"])))


def _power_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.intensity import power

    return ProcessResult(
        primary=power(document, c=float(parameters["c"]), gamma=float(parameters["gamma"]))
    )


def _intensity_slicing_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.intensity import intensity_slicing

    return ProcessResult(
        primary=intensity_slicing(
            document,
            a=int(parameters["a"]),
            b=int(parameters["b"]),
            preserve_background=bool(parameters["preserve_background"]),
        )
    )


def _histogram_equalization_executor(
    document: ImageDocument, _: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.histogram import histogram_equalization

    return histogram_equalization(document)


def _gaussian_blur_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.spatial import gaussian_blur

    return ProcessResult(
        primary=gaussian_blur(
            document, window=int(parameters["window"]), sigma=float(parameters["sigma"])
        )
    )


def _order_filter_executor(operation: str) -> ProcessExecutor:
    def execute(document: ImageDocument, parameters: Mapping[str, ParameterValue]) -> ProcessResult:
        from imagelab.core.spatial import order_filter

        return ProcessResult(
            primary=order_filter(document, window=int(parameters["window"]), operation=operation)
        )

    return execute


def _unsharp_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.derivatives import unsharp_mask

    return ProcessResult(
        primary=unsharp_mask(
            document,
            window=int(parameters["window"]),
            sigma=float(parameters["sigma"]),
            gain=float(parameters["gain"]),
        )
    )


def _laplacian_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.derivatives import laplacian

    return laplacian(document, window=int(parameters["window"]))


def _sobel_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.derivatives import sobel

    return sobel(document, window=int(parameters["window"]))


def _gaussian_frequency_executor(high_pass: bool) -> ProcessExecutor:
    def execute(document: ImageDocument, parameters: Mapping[str, ParameterValue]) -> ProcessResult:
        from imagelab.core.frequency import gaussian_frequency_filter

        return ProcessResult(
            primary=gaussian_frequency_filter(
                document,
                cutoff=float(parameters["cutoff"]),
                normalized_cutoff=bool(parameters["normalized_cutoff"]),
                high_pass=high_pass,
            )
        )

    return execute


def _butterworth_frequency_executor(high_pass: bool) -> ProcessExecutor:
    def execute(document: ImageDocument, parameters: Mapping[str, ParameterValue]) -> ProcessResult:
        from imagelab.core.butterworth import butterworth_frequency_filter

        return ProcessResult(
            primary=butterworth_frequency_filter(
                document,
                cutoff=float(parameters["cutoff"]),
                normalized_cutoff=bool(parameters["normalized_cutoff"]),
                order=int(parameters["order"]),
                high_pass=high_pass,
            )
        )

    return execute


def _adaptive_median_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.adaptive import adaptive_median_filter

    return ProcessResult(
        primary=adaptive_median_filter(document, maximum_window=int(parameters["maximum_window"]))
    )


def _gaussian_noise_executor(
    document: ImageDocument, parameters: Mapping[str, ParameterValue]
) -> ProcessResult:
    from imagelab.core.noise import gaussian_noise

    return ProcessResult(
        primary=gaussian_noise(
            document, mu=float(parameters["mu"]), sigma=float(parameters["sigma"])
        )
    )


def _impulse_noise_executor(kind: ImpulseKind) -> ProcessExecutor:
    def execute(document: ImageDocument, parameters: Mapping[str, ParameterValue]) -> ProcessResult:
        from imagelab.core.noise import impulse_noise

        if kind == "salt_pepper":
            return ProcessResult(
                primary=impulse_noise(
                    document,
                    density=float(parameters["density"]),
                    kind=kind,
                    salt_proportion=float(parameters["salt_proportion"]),
                )
            )
        return ProcessResult(
            primary=impulse_noise(document, density=float(parameters["density"]), kind=kind)
        )

    return execute

_WINDOWS_3_TO_31 = tuple(str(i) for i in range(3, 33, 2))
_WINDOWS_3_TO_7 = ("3", "5", "7")

PROCESS_CATALOG = ProcessCatalog(
    (
        ProcessDefinition(
            identifier="gaussian_noise",
            label="Ruído gaussiano",
            category="Ruídos",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec("mu", "Média μ", ParameterKind.NUMBER, 0.0, -255, 255, "níveis"),
                ParameterSpec(
                    "sigma", "Desvio padrão σ", ParameterKind.NUMBER, 10.0, 0, 255, "níveis"
                ),
            ),
            executor=_gaussian_noise_executor,
        ),
        ProcessDefinition(
            identifier="salt_noise",
            label="Ruído sal",
            category="Ruídos",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("density", "Densidade", ParameterKind.NUMBER, 0.05, 0, 1),),
            executor=_impulse_noise_executor("salt"),
        ),
        ProcessDefinition(
            identifier="pepper_noise",
            label="Ruído pimenta",
            category="Ruídos",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("density", "Densidade", ParameterKind.NUMBER, 0.05, 0, 1),),
            executor=_impulse_noise_executor("pepper"),
        ),
        ProcessDefinition(
            identifier="salt_pepper_noise",
            label="Ruído sal e pimenta",
            category="Ruídos",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec("density", "Densidade", ParameterKind.NUMBER, 0.05, 0, 1),
                ParameterSpec(
                    "salt_proportion", "Proporção de sal", ParameterKind.NUMBER, 0.5, 0, 1
                ),
            ),
            executor=_impulse_noise_executor("salt_pepper"),
        ),
        ProcessDefinition(
            identifier="butterworth_low_pass_frequency",
            label="Passa-baixa Butterworth (frequência)",
            category="Filtros de frequência",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec(
                    "cutoff",
                    "Frequência de corte",
                    ParameterKind.NUMBER,
                    10.0,
                    0.0001,
                    100000,
                    "bins",
                ),
                ParameterSpec(
                    "normalized_cutoff", "Usar corte normalizado", ParameterKind.BOOLEAN, False
                ),
                ParameterSpec("order", "Ordem n", ParameterKind.INTEGER, 1, 1, 20),
            ),
            executor=_butterworth_frequency_executor(False),
            description=(
                "Usa o mesmo padding zero 2× da frequência gaussiana; o corte pode ser "
                "informado em bins FFT ou normalizado por Dmax."
            ),
        ),
        ProcessDefinition(
            identifier="butterworth_high_pass_frequency",
            label="Passa-alta Butterworth (frequência)",
            category="Filtros de frequência",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec(
                    "cutoff",
                    "Frequência de corte",
                    ParameterKind.NUMBER,
                    10.0,
                    0.0001,
                    100000,
                    "bins",
                ),
                ParameterSpec(
                    "normalized_cutoff", "Usar corte normalizado", ParameterKind.BOOLEAN, False
                ),
                ParameterSpec("order", "Ordem n", ParameterKind.INTEGER, 1, 1, 20),
            ),
            executor=_butterworth_frequency_executor(True),
            description=(
                "Usa o mesmo padding zero 2× da frequência gaussiana; o corte pode ser "
                "informado em bins FFT ou normalizado por Dmax."
            ),
        ),
        ProcessDefinition(
            identifier="gaussian_low_pass_frequency",
            label="Passa-baixa gaussiano (frequência)",
            category="Filtros de frequência",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec(
                    "cutoff",
                    "Frequência de corte",
                    ParameterKind.NUMBER,
                    10.0,
                    0.0001,
                    100000,
                    "bins",
                ),
                ParameterSpec(
                    "normalized_cutoff", "Usar corte normalizado", ParameterKind.BOOLEAN, False
                ),
            ),
            executor=_gaussian_frequency_executor(False),
            description=(
                "Usa padding zero 2× para reduzir, mas não eliminar, wraparound. "
                "Informe D0 em bins FFT ou marque o corte normalizado (D0/Dmax)."
            ),
        ),
        ProcessDefinition(
            identifier="gaussian_high_pass_frequency",
            label="Passa-alta gaussiano (frequência)",
            category="Filtros de frequência",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec(
                    "cutoff",
                    "Frequência de corte",
                    ParameterKind.NUMBER,
                    10.0,
                    0.0001,
                    100000,
                    "bins",
                ),
                ParameterSpec(
                    "normalized_cutoff", "Usar corte normalizado", ParameterKind.BOOLEAN, False
                ),
            ),
            executor=_gaussian_frequency_executor(True),
            description=(
                "Usa padding zero 2× para reduzir, mas não eliminar, wraparound. "
                "Informe D0 em bins FFT ou marque o corte normalizado (D0/Dmax)."
            ),
        ),
        ProcessDefinition(
            identifier="unsharp_mask",
            label="Aguçamento por máscara",
            category="Realce e bordas",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_31, unit="px"),
                ParameterSpec("sigma", "Sigma", ParameterKind.NUMBER, 1.0, 0.001, 100, "px"),
                ParameterSpec("gain", "Ganho", ParameterKind.NUMBER, 1.0, 0, 100),
            ),
            executor=_unsharp_executor,
        ),
        ProcessDefinition(
            identifier="laplacian",
            label="Laplaciano",
            category="Realce e bordas",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_7, unit="px"),),
            executor=_laplacian_executor,
        ),
        ProcessDefinition(
            identifier="sobel",
            label="Sobel",
            category="Realce e bordas",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_7, unit="px"),),
            executor=_sobel_executor,
        ),
        ProcessDefinition(
            identifier="adaptive_median_filter",
            label="Filtro de mediana adaptativa",
            category="Filtros espaciais",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec(
                    "maximum_window", "Janela máxima", ParameterKind.CHOICE, "7", choices=_WINDOWS_3_TO_31, unit="px"
                ),
            ),
            executor=_adaptive_median_executor,
        ),
        ProcessDefinition(
            identifier="median_filter",
            label="Filtro de mediana",
            category="Filtros espaciais",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_31, unit="px"),),
            executor=_order_filter_executor("median"),
        ),
        ProcessDefinition(
            identifier="minimum_filter",
            label="Filtro mínimo",
            category="Filtros espaciais",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_31, unit="px"),),
            executor=_order_filter_executor("minimum"),
        ),
        ProcessDefinition(
            identifier="maximum_filter",
            label="Filtro máximo",
            category="Filtros espaciais",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_31, unit="px"),),
            executor=_order_filter_executor("maximum"),
        ),
        ProcessDefinition(
            identifier="gaussian_blur",
            label="Filtro de média gaussiana",
            category="Filtros espaciais",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec("window", "Janela", ParameterKind.CHOICE, "3", choices=_WINDOWS_3_TO_31, unit="px"),
                ParameterSpec("sigma", "Sigma", ParameterKind.NUMBER, 1.0, 0.001, 100, "px"),
            ),
            executor=_gaussian_blur_executor,
        ),
        ProcessDefinition(
            identifier="histogram_equalization",
            label="Equalização de histograma",
            category="Transformações de intensidade",
            compatible_modes=frozenset({ImageMode.GRAYSCALE}),
            parameters=(),
            executor=_histogram_equalization_executor,
        ),
        ProcessDefinition(
            identifier="logarithmic",
            label="Transformação logarítmica",
            category="Transformações de intensidade",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec("c", "Ganho c", ParameterKind.NUMBER, 255 / log(256), 0.001, 1000),
            ),
            executor=_logarithmic_executor,
        ),
        ProcessDefinition(
            identifier="power",
            label="Transformação de potência",
            category="Transformações de intensidade",
            compatible_modes=frozenset({ImageMode.GRAYSCALE, ImageMode.RGB}),
            parameters=(
                ParameterSpec("c", "Ganho c", ParameterKind.NUMBER, 1.0, 0.001, 1000),
                ParameterSpec("gamma", "Gama", ParameterKind.NUMBER, 1.0, 0.001, 100),
            ),
            executor=_power_executor,
        ),
        ProcessDefinition(
            identifier="intensity_slicing",
            label="Fatiamento por intensidade",
            category="Transformações de intensidade",
            compatible_modes=frozenset({ImageMode.GRAYSCALE}),
            parameters=(
                ParameterSpec("a", "A", ParameterKind.INTEGER, 64, 0, 255),
                ParameterSpec("b", "B", ParameterKind.INTEGER, 192, 0, 255),
                ParameterSpec(
                    "preserve_background", "Preservar fundo", ParameterKind.BOOLEAN, True
                ),
            ),
            executor=_intensity_slicing_executor,
        ),
        ProcessDefinition(
            identifier="threshold",
            label="Limiarização",
            category="Transformações de intensidade",
            compatible_modes=frozenset({ImageMode.GRAYSCALE}),
            parameters=(
                ParameterSpec(
                    key="k",
                    label="Limiar k",
                    kind=ParameterKind.INTEGER,
                    default=128,
                    minimum=0,
                    maximum=255,
                    unit="nível",
                ),
            ),
            executor=_threshold_executor,
        ),
        ProcessDefinition(
            identifier="decompose_rgb",
            label="Decomposição RGB",
            category="Decomposições de cor",
            compatible_modes=frozenset({ImageMode.RGB}),
            parameters=(),
            executor=_rgb_decomposition_executor,
        ),
        ProcessDefinition(
            identifier="decompose_hsv",
            label="Decomposição HSV",
            category="Decomposições de cor",
            compatible_modes=frozenset({ImageMode.RGB}),
            parameters=(),
            executor=_hsv_decomposition_executor,
        ),
    )
)
