# Design Document

## For MCP ChatKit Widget Rendering Module

- **Version:** 0.2
- **Author:** Shaojie Jiang
- **Date:** 2025-12-10
- **Status:** In Review

---

## Overview

This design describes how the MCP ChatKit Widget toolkit explicitly loads curated `.widget` definitions via `chatkit.widgets.WidgetTemplate.from_file`, enforces each file's `template` field as the rendering source of truth, and exposes the discovery/rendering helpers as an importable Python module. The templates are converted to `WidgetRoot` instances with each `.build()` call so downstream automation and backends get the same Card/Row/Text hierarchy as the reference repository without spinning up the FastMCP entry point.

The widget loader now requires a `widgets_dir` path, aborts on missing or malformed definitions, and renders every widget by parsing its template with the validated inputs so that agents always receive the same Card/Row/Text hierarchy as the reference repository. Downstream consumers may still generate widgets through the MCP tools, but they can also import the new module-level API (`load_widgets`, `render_widget_definition`, `generate_widget_tools`) for tests, demos, or tooling that does not need the full MCP server lifecycle.

Keeping the rendering path deterministic and packaged as a module also ensures that new automation scripts and integration tests can call the same helpers that power the FastMCP tools, reducing duplication and strengthening fidelity guarantees before the release reaches production environments.

## Components

- **Configuration & Widget Discovery (`widget_loader.py`)**
  - Responsibility: validate the required `widgets_dir`, walk it exclusively for `.widget` files, and fail fast when the argument is missing, when the directory is absent, or when files lack the required `template` block.
  - Interfaces: `load_widgets(widgets_dir: Path)` returns a list of `WidgetDefinition` objects, and `load_widget(widget_path: Path)` parses an individual file while raising helpful errors.

- **Schema & Template Rendering (`pydantic_conversion.py` + renderer helpers)**
  - Responsibility: load each curated template via `chatkit.widgets.WidgetTemplate.from_file`, generate Pydantic models from the widget's `jsonSchema`, render the stored `template` with validated data, and call the template's `.build()` helper so the resulting JSON becomes `chatkit.widgets.WidgetRoot` instances matching the official ChatKit layout.
  - Interfaces: `json_schema_to_pydantic(schema, model_name, schema_title)` for validation and `render_widget_definition(widget_def, **kwargs)` for rendering templates and returning a `WidgetRoot`.

- **Server Integration & Module API (`server.py` + module exports)**
  - Responsibility: orchestrate tool generation for FastMCP (naming conventions, signature creation, tool registration) while simultaneously exposing modular helpers (`load_widgets`, `render_widget_definition`, `generate_widget_tools`) so external scripts can call the same rendering pipeline without importing FastMCP.
  - Interfaces: `generate_widget_tools(server, widget_defs)` wires FastMCP tools to widget definitions, and the exported helpers hide server-specific setup from automation consumers.

## Request Flows

### Flow 1: Controlled Server Startup and Tool Registration

1. Operator invokes the MCP server (`uv run mcp-chatkit-widget`) with `widgets_dir` configured.
2. Widget loader validates `widgets_dir`, enumerates `.widget` files inside it, and raises a configuration error if the argument is missing or the path is invalid.
3. For each widget definition, schema utilities generate a Pydantic model, the loader calls `WidgetTemplate.from_file` on the template, the renderer validates inputs and renders the template, and the `.build()` call converts the rendered JSON into ChatKit components.
4. `generate_widget_tools` wires each widget into FastMCP using sanitized snake_case names while `render_widget_definition` stays available for downstream usage.
5. MCP clients receive the tools, each guaranteed to deliver the same structure as the official demo because the template field is the single source of truth.

### Flow 2: Manual Rendering via the Importable Module

1. Automation script calls `load_widgets(Path(...))` with the curated directory, receiving typed `WidgetDefinition` objects.
2. The script optionally filters widget definitions (e.g., by feature flag) and calls `render_widget_definition(widget_def, **kwargs)` for specific payloads.
3. Rendered JSON is converted into ChatKit components via the template's `.build()` method; the helper can be reused for demos, tests, or backend integrations without FastMCP.
4. If needed, `generate_widget_tools` is invoked with a custom server-like object to reuse the same validation/rendering logic in other contexts.

## API Contracts

```
def load_widgets(widgets_dir: Path) -> list[WidgetDefinition]
```
- Validates that `widgets_dir` exists and contains only supported `.widget` files with a `template`.
- Raises a clear `ValueError` when the argument is missing or points outside the curated directory.

```
def render_widget_definition(widget_def: WidgetDefinition, **kwargs: Any) -> WidgetRoot
```
- Validates inputs via the dynamically generated Pydantic model and renders the stored Jinja2 template.
- Parses the resulting JSON and converts it to `chatkit.widgets.WidgetRoot`, raising detailed errors when rendering fails.

```
def generate_widget_tools(server: FastMCP, widget_defs: list[WidgetDefinition]) -> None
```
- Creates FastMCP tools with sanitized names, camel-case function identifiers, and fully annotated signatures.
- Registers each tool with the provided `server`, allowing shared logic between the reference backend and any other FastMCP instance.

## Data Models / Schemas

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable widget name used in logs and tool docs |
| `version` | `str` | Widget schema version, currently `1.0` |
| `jsonSchema` | `dict` | Parameter schema converted to a Pydantic model |
| `template` | `str` | Jinja2 template string rendered with validated inputs |
| `outputJsonPreview` | `dict` | Reference payload used for schema validation and examples |
| `encodedWidget` | `Optional[str]` | Optional base64-encoded widget content for metadata consumers |
| `file_path` | `Path` | Source path used for error reporting |

## Security Considerations

- Enforce curated discovery by requiring `widgets_dir`; refuse to walk any other location so that downstream agents can never load arbitrary `.widget` files.
- Treat Jinja2 templates as trusted artifact controlled by maintainers and stop registration when a template is missing or produces invalid JSON (Jinja2 `UndefinedError` or `json.JSONDecodeError`).
- Surface parsing/rendering errors with context (widget name, file path, line) so debugging mirrors the official demo repository.

## Performance Considerations

- Cache generated Pydantic models once per widget so repeated requests during a process reuse the same models and incur only rendering cost.
- Keep template rendering and JSON parsing lean by using `json.loads` on deterministic strings; future work may evaluate `orjson` for micro-optimizations.
- Discovery happens at startup, but helper APIs allow prewarming widgets in downstream scripts to avoid first-request spikes.

## Testing Strategy

- **Unit tests:** cover `load_widgets` enforcing `widgets_dir`, schema-to-model conversion, template rendering errors, and FastMCP tool generation including name sanitization.
- **Integration tests:** load the actual `.widget` files, render their templates with canonical inputs, and assert the resulting `WidgetRoot` matches expectations from `openai-chatkit-advanced-samples`.
- **Manual checklist:** run `uv run make lint` and `uv run make test`, plus `make demo-*` targets when touching UI demos to ensure module helpers do not regress server behavior.

## Rollout Plan

1. **Phase 1 – Developer preview:** Ship documentation updates, enforce `widgets_dir`, and add regression tests for template fidelity.
2. **Phase 2 – Internal dogfood:** Import the new module helpers in an internal backend (e.g., `openai-chatkit-advanced-samples`) to validate rendering without FastMCP.
3. **Phase 3 – General availability:** Release the package, update downstream consumers, and monitor adoption metrics (widget coverage, template fidelity, module adoption).

## Open Issues

- [ ] Decide whether to expose the `encodedWidget` metadata via MCP resources or keep it internal to widget definitions.

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-10 | Shaojie Jiang | Align design with requirements v0.2 and template-defined rendering |
