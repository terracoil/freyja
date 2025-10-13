"""Version utility functions for Freyja CLI framework."""

import importlib.metadata
import tomllib
from pathlib import Path


def get_freyja_version() -> str:
    """
    Get the current Freyja version.

    :return: Version string in format 'v1.0.15'
    """
    version = None

    # Try to get version from installed package metadata first
    try:
        version = importlib.metadata.version("freyja")
    except importlib.metadata.PackageNotFoundError:
        # Fallback to reading from pyproject.toml (development mode)
        try:
            freyja_root = Path(__file__).parent.parent.parent
            pyproject_path = freyja_root / "pyproject.toml"

            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                version = pyproject_data.get("tool", {}).get("poetry", {}).get("version")
        except Exception:
            # Final fallback
            version = "unknown"

    return f"v{version}" if version else "v0.0.0"


def format_title_with_version(title: str) -> str:
    """
    Format title with Freyja version information.

    :param title: Original application title
    :return: Title formatted with version (e.g., "My App - freyja v1.0.15")
    """
    freyja_version = get_freyja_version()
    return f"{title} (freyja {freyja_version})"
