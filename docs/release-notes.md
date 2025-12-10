# Release Notes v0.2

## Highlights

- **Curated widget discovery:** Running `mcp-chatkit-widget` now requires the
  `--widgets-dir` argument so the loader only resolves `.widget` files from a
  curated path and fails fast when the directory is missing or malformed.
- **Exported helpers:** `load_widgets`, `render_widget_definition`, and
  `generate_widget_tools` are documented as importable APIs so other scripts,
  demos, and backend services can reuse the same validation/rendering pipeline
  without bootstrapping FastMCP.
- **Regression coverage:** New tests cover `load_widgets` error handling and tool
  registration, reinforcing the curated discovery guardrails, sanitized tool
  naming, and template fidelity.

## Testing

- `uv run make lint`
- `uv run make test`
