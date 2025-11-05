# Repository Guidelines

## Project Structure & Module Organization
The `mcp_chatkit_widget/` package contains the MCP server implementation and integration utilities. Tests live in `tests/` and mirror the source layout (`tests/<module>/test_*.py`). Demo clients and reference backends are under `examples/` with separate folders for `frontend/react`, `frontend/streamlit`, and `backend`. Documentation artifacts are generated from `docs/` via `mkdocs.yml`, while automation shortcuts reside in the project `Makefile`.

## Build, Test, and Development Commands
Use `make lint` to run Ruff linting, type checks (`mypy mcp_chatkit_widget`), and format validation in one step. Apply project formatting with `make format`, which fixes Ruff import/style issues and formats the React example. Execute the Python test suite and coverage reporting with `make test` (equivalent to `pytest --cov --cov-report term-missing tests/`). Spin up the reference backend with `make demo-backend`, or launch UI demos using `make demo-react` and `make demo-streamlit`.

## Coding Style & Naming Conventions
Python code follows Ruff defaults with an 88-character limit and 4-space indentation; enable Ruff’s fixer before opening PRs. Keep public symbols and modules typed, as `mypy` enforces `disallow_untyped_defs`. Prefer explicit module imports (no relative imports) and snake_case for functions, CamelCase for classes, and uppercase for constants. Run `ruff format .` before committing to preserve consistent spacing in both Python and generated files.

## Testing Guidelines
Write tests with `pytest`, covering synchronous and async behavior via `pytest-asyncio`. Name files `test_<feature>.py` and individual tests `test_<scenario>`. Maintain meaningful coverage for new modules and review the `pytest --cov` output for gaps; add regression tests for any bug fixes. For UI demos, complement unit tests with short smoke runs of the relevant `make demo-*` target when feasible.

## Commit & Pull Request Guidelines
Commit messages should start with a short imperative summary (<60 characters) followed by optional detail lines explaining implementation or referencing trackers (e.g., `Refs #123`). Group commits logically—formatting changes can stay separate from functional updates. Pull requests should describe the change, outline testing performed (`make lint`, `make test`, demo commands), and attach screenshots or GIFs when altering UI flows in `examples/frontend`. Link related issues or discussion threads so reviewers can trace context quickly.
