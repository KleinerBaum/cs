"""Command-line runner for the deterministic vacancy pipeline."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Mapping

from core.schemas import RawInput
from pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the pipeline runner."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic pipeline locally to extract, validate, and "
            "optionally enrich vacancy data."
        )
    )
    parser.add_argument(
        "--content",
        required=True,
        help=(
            "Raw vacancy text or description to feed into the deterministic "
            "pipeline."
        ),
    )
    parser.add_argument(
        "--source-type",
        default="text",
        help="Optional source type identifier (default: text).",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language hint passed through to the pipeline.",
    )
    parser.add_argument(
        "--payload",
        type=Path,
        default=None,
        help=(
            "Path to a JSON file providing validation payload fields (e.g., "
            "company_name, job_title)."
        ),
    )
    return parser.parse_args()


def _serialize(value: Any) -> Any:
    """Recursively convert BaseModel instances to plain data structures."""

    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, Mapping):
        return {key: _serialize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def _load_payload(path: Path | None) -> dict[str, Any] | None:
    """Load a JSON payload from disk if a path is provided."""

    if path is None:
        return None
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    """Entry point for running the vacancy pipeline via CLI."""

    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    payload = _load_payload(args.payload)
    raw_input = RawInput(
        content=args.content, source_type=args.source_type, language=args.language
    )

    result = run_pipeline(raw_input, payload)
    print(json.dumps(_serialize(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
