# Refactor Large Scripts

Each script should have fewer than 250 LOC; special cases may extend but must stay under 300 LOC.

## Refactoring Checklist (2025-11-06)

- [x] `tests/test_widget_integration.py` — 612 LOC
- [x] `tests/test_widget_loader.py` — 410 LOC
- [x] `examples/run_widget/run_widget.py` — 315 LOC
- [x] `tests/test_schema_utils.py` — 277 LOC
- [ ] `mcp_chatkit_widget/schema_utils.py` — 275 LOC


## Wrap up

- [x] Tell coding agents to respect the LOC limit in future commits
