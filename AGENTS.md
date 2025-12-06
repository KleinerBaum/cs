# AGENTS.md (Repo root)

## Repo map (current)
- Entry point: `app.py` (Streamlit)
- Main modules: `src/*.py`
- Subpackages: `src/schema/*`, `src/wizard/*`

## Setup / run
- Install: `pip install -r requirements.txt`
- Run app: `streamlit run app.py`

## Verification (run before finishing)
- `python -m compileall .`
- `ruff check .` (if available)
- `pyright` (optional, if installed)

## Import conventions (important)
- `src/` is a Python package (has `src/__init__.py`).
- Prefer absolute imports like: `from src.ui import ...`
- If you find legacy imports (e.g. `cogstaff.*`), update to `src.*` consistently.

## Output expectations
- Make coherent, minimal diffs.
- Do not add new top-level modules in repo root; put new code in `src/`.
