"""File and data-loading helpers.

The demo uses local files as the source of truth. These helpers centralize file
loading and controlled fallback handling so tools can report data quality issues
in a consistent way.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_DATA_DIR = PROJECT_ROOT / "data" / "demo"


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of dictionaries.

    Missing files are surfaced to callers as FileNotFoundError so tools can
    decide whether to use a fallback path or fail loudly.
    """

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    """Read a JSON file from disk."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    """Write JSON data to disk with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file into a dictionary."""

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return loaded


def missing_fields(rows: list[dict[str, Any]], required_fields: list[str]) -> list[str]:
    """Return required field names that are absent from any row mapping."""

    if not rows:
        return required_fields[:]

    field_names = set(rows[0].keys())
    return [field for field in required_fields if field not in field_names]


def demo_path(*parts: str) -> Path:
    """Resolve a path relative to the deterministic demo dataset."""

    return DEMO_DATA_DIR.joinpath(*parts)
