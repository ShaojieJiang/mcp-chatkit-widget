# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides ChatKit widget functionality. The project uses FastMCP for the server implementation and is designed to integrate UI components with AI agents. 

## Development Environment

**Python Version:** 3.12+ (specified in `.python-version`)
**Package Manager:** `uv` (modern Python package manager)
**Build System:** hatchling

Install dependencies:
```bash
uv sync --all-groups
```

## Common Commands

**Linting and Type Checking:**
```bash
make lint              # Run ruff, mypy, and format checks
uv run make lint       # Same but with uv prefix (CI style)
```

**Formatting:**
```bash
make format            # Auto-fix imports, format Python and React code
ruff format .          # Format Python code only
```

**Testing:**
```bash
make test                                          # Run all tests with coverage
pytest --cov --cov-report term-missing tests/      # Explicit test command
pytest tests/path/to/test_file.py::test_name      # Run single test
uv run coverage run -m pytest                      # CI-style coverage
```

**Running Demos:**
```bash
make demo-backend      # Start LangGraph backend (requires langgraph.json)
make demo-react        # Start React demo (port in package.json)
make demo-streamlit    # Start Streamlit demo
```

**Documentation:**
```bash
make doc               # Serve docs locally on 0.0.0.0:8080
```

## Project Architecture

### Core Server (`mcp_chatkit_widget/`)
- `server.py`: Defines the FastMCP server instance named "mcp-chatkit-widget"
- `__init__.py`: Exports the server and provides `main()` entry point
- Entry point via console script: `mcp-chatkit-widget` command runs `main()`

### Examples Structure
The `examples/` directory is currently empty but structured for:
- `backend/`: Reference LangGraph agent implementation (configured in `langgraph.json`)
- `frontend/react/`: React-based UI demo
- `frontend/streamlit/`: Streamlit-based UI demo

### LangGraph Integration
`langgraph.json` points to `examples/backend/agent.py:agent` as the graph definition, indicating this project bridges MCP servers with LangGraph-based agents.

## Code Style

**Linter:** Ruff (replaces flake8, isort, black)
- Line length: 88 characters
- Import style: Absolute imports only (no relative imports via TID252)
- Two blank lines after imports (isort config)
- Google-style docstrings (pydocstyle convention)

**Type Checking:** mypy with strict mode
- `disallow_untyped_defs = true`: All functions must have type annotations
- Python 3.12 syntax

**Pre-commit Hooks:**
Run automatically via `.pre-commit-config.yaml`:
- Trailing whitespace, end-of-file fixes
- YAML/JSON validation
- Ruff formatting and linting
- TOML formatting

## Testing Requirements

**Framework:** pytest with pytest-asyncio for async tests
**Coverage Target:** 95% overall, 100% diff coverage for new changes
**Location:** Tests mirror source structure in `tests/` directory

When adding tests:
- Name files `test_<feature>.py`
- Use descriptive test names: `test_<scenario>`
- Mark async tests with `@pytest.mark.asyncio`
- Tests directory excludes pydocstyle checks (per-file ignore)

## CI/CD Pipeline

**Triggers:** PRs to main, pushes to main, and version tags
**Jobs:**
1. `lint`: Runs `make lint` (ruff + mypy + format check)
2. `coverage`: Runs tests, enforces 95% coverage + 100% diff coverage
3. `build-and-release`: Publishes to PyPI on version tags (trusted publishing)

## Version Management

Uses `bump2version` (configured in `.bumpversion.cfg`)
- Current version: 0.1.0 (in `pyproject.toml`)
- Update version before tagging releases

## Distribution

**Build command:** `uv build`
**PyPI package:** `mcp-chatkit-widget`
**Wheel excludes:** examples/, tests/, docs/, .github/, markdown files

## Key Dependencies

**Runtime:** Currently no external dependencies (will grow as features are added)
**Dev:** ruff, mypy, pytest, pytest-asyncio, pytest-cov, pre-commit
**Docs:** mkdocs with material theme, mkdocstrings for API docs
