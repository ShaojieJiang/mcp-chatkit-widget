# Project Plan

## For MCP ChatKit Widget Rendering Module

- **Version:** 0.2
- **Author:** Codex
- **Date:** 2025-12-10
- **Status:** Draft

---

## Overview

Formalize the MCP ChatKit widget loader so it enforces a curated `widgets_dir`, treats each `.widget` file's `template` field as the single source of truth, and packages discovery/rendering helpers into an importable module. The updated tooling must keep FastMCP tool registration unchanged while exposing the same validation and template rendering logic for downstream automation and demos.

**Related Documents:**
- Requirements: `docs/requirements.md`
- Design: `docs/design.md`

---

## Milestones

### Milestone 1: Controlled Widget Discovery

**Description:** Guard the loader behind an explicit `widgets_dir` so MCP tooling only walks curated definitions and fails fast when configuration or templates are missing.

#### Task Checklist

- [ ] Task 1.1: Require `widgets_dir` in MCP configuration, validate it exists, and raise a clear error when it is omitted.
  - Dependencies: None
- [ ] Task 1.2: Restrict discovery to `.widget` files beneath `widgets_dir` and skip any files outside that directory.
  - Dependencies: Task 1.1
- [ ] Task 1.3: Enforce that each `.widget` definition embeds a `template` block, logging helpfully and halting registration when the block is absent or malformed.
  - Dependencies: Task 1.2

---

### Milestone 2: Template-Faithful Rendering Module

**Description:** Build reusable schema and template helpers that render the curated templates via `chatkit.widgets.WidgetTemplate` and expose them as module-level APIs.

#### Task Checklist

- [ ] Task 2.1: Implement schema parsing utilities that turn `jsonSchema` into typed Pydantic models and load templates through `WidgetTemplate.from_file`.
  - Dependencies: Milestone 1
- [ ] Task 2.2: Create `render_widget_definition` and related helpers that validate inputs, render the stored template, and convert the JSON to `WidgetRoot` instances (matching the official demo layout).
  - Dependencies: Task 2.1
- [ ] Task 2.3: Expose and document the module-level API (`load_widgets`, `render_widget_definition`, `generate_widget_tools`) so downstream consumers can import the same helpers without running FastMCP.
  - Dependencies: Task 2.2

---

### Milestone 3: Server Integration, Tests, and Rollout Prep

**Description:** Wire the new helpers into FastMCP, add regression tests for the curated workflows, and update docs so downstream teams know how to adopt the new APIs.

#### Task Checklist

- [ ] Task 3.1: Use `generate_widget_tools` to register sanitized FastMCP tools based on the validated definitions while reusing the shared rendering helpers.
  - Dependencies: Milestone 2
- [ ] Task 3.2: Add unit/integration tests that cover `load_widgets`, template rendering fidelity, and tool registration, plus fresh checks that `widgets_dir` enforcement raises clear errors.
  - Dependencies: Task 3.1
- [ ] Task 3.3: Update the documentation (including `README.md` and release notes) with the new `widgets_dir` requirement, exported helpers, and testing guidance.
  - Dependencies: Task 3.2

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-10 | Codex | Initial draft aligned with v0.2 requirements and design |
