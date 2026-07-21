"""Command-line entry point for ImageLab PDI."""

from imagelab.app import run


def main() -> None:
    """Launch ImageLab as a Python module or console script."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
