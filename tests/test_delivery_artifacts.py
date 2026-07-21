from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def test_windows_launch_script_targets_the_documented_module() -> None:
    script = (ROOT / "scripts" / "run.ps1").read_text(encoding="utf-8")

    assert ".venv\\Scripts\\python.exe" in script
    assert "-m imagelab" in script


def test_synthetic_samples_cover_gray_and_rgb_demonstrations() -> None:
    samples = ROOT / "assets" / "samples"
    expected = {
        "constant.png",
        "impulse.png",
        "step.png",
        "gradient.png",
        "rgb-blocks.png",
        "noisy-gradient.png",
    }

    assert {path.name for path in samples.glob("*.png")} == expected
    assert Image.open(samples / "rgb-blocks.png").mode == "RGB"
    assert Image.open(samples / "gradient.png").mode == "L"


def test_readme_documents_execution_conventions_and_quality_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for text in (
        "## Requisitos e execução no Windows",
        "HSV convencional",
        "BORDER_REFLECT_101",
        "CDF_min",
        "D0",
        "Ruídos",
        "ruff check",
        "mypy src",
        "pytest --cov",
    ):
        assert text in readme


def test_detailed_usage_and_validation_guide_is_available() -> None:
    guide = (ROOT / "docs" / "guia-de-uso-e-testes.md").read_text(encoding="utf-8")

    for text in (
        "## 2. Abrir e navegar pelas imagens",
        "## 5. Testar a aplicação manualmente",
        "## 6. Executar os testes automatizados",
        "scripts\\run.ps1",
        "ruff check",
        "pytest --cov",
    ):
        assert text in guide
