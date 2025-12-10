# Requirements Document v0.2

## METADATA
- **Authors:** Codex
- **Project/Feature Name:** MCP ChatKit Widget
- **Type:** Feature
- **Version:** 0.2
- **Summary:** Formalize requirements for loading curated ChatKit widgets, rendering them via their template field, and shipping the toolkit as an importable Python module.
- **Owner (if different than authors):** Shaojie Jiang
- **Date Started:** 2025-12-10

## RELEVANT LINKS & STAKEHOLDERS
| Document | Link | Owner | Notes |
|----------|------|-------|-------|
| ChatKit Advanced Samples | https://github.com/openai/openai-chatkit-advanced-samples | OpenAI | Official widget and template references |
| Widget definitions corpus | mcp_chatkit_widget/widgets/ | Shaojie Jiang | Current `.widget` files and validation harness |

## PROBLEM DEFINITION
### Objectives
Limit MCP widget generation to explicitly supported definitions while using each `.widget` file's `template` field so generated widgets match the official demo, and expose the tooling as an importable module for downstream applications.

### Target users
Developers building AI Agents with ChatKit UI as the frontend who need curated widget discovery, validation, and rendering.

### User Stories
| As a... | I want to... | So that... | Priority | Acceptance Criteria |
|---------|--------------|------------|----------|---------------------|
| MCP client integrator | pass a single `widgets_dir` argument when configuring the client | only curated and whitelisted widgets are loaded and registered | P0 | The server fails fast if the argument is missing and only discovers widgets under the supplied directory |
| Widget authoring workflow owner | rely on the `template` field inside each `.widget` definition | generated widgets always mirror the official ChatKit layout and styling | P0 | Rendering pipeline renders `template` with validated inputs and produces the same structure as the demo repository |
| Scripting consumer | import the generation helpers directly from the package | I can blend widget creation into other automation without spinning up the MCP server | P1 | Public APIs expose `load_widgets`, validation utilities, and `render_widget` functions with documented signatures |

### Context, Problems, Opportunities
- The previous PRD captured how `.widget` files drove FastMCP tool registration, but clients still rely on a hardcoded directory and ad hoc discovery that risks loading unsupported widgets.
- Official sample code uses the template field to build widgets, so aligning with that workflow ensures fidelity and simplifies debugging.
- Introducing stricter configuration and exporting the tooling as an importable module enables the reference backend, CLI, and other projects to reuse the same rendering logic without duplicating configuration.

### Product goals and Non-goals
**Product goals**
- Centralize widget discovery around an explicit `widgets_dir`.
- Guarantee every generated widget uses its recorded template.
- Surface reusable Python APIs for downstream automation.
**Non-goals**
- Implement MCP-side feature flags or progressive rollout tooling beyond the configuration guardrails described above.

## PRODUCT DEFINITION
### Requirements
The system continues to discover `.widget` files, generate Pydantic validation models, and expose each widget as an MCP tool, but new constraints guide what is considered supported and what tooling is reusable.

#### P0
- Require the MCP client to pass a `widgets_dir` argument; loading widgets without it raises a clear configuration error and the widget loader only walks that directory so agents cannot accidentally import user-defined files from other locations.
- Ensure every `.widget` file's `template` field is the sole source of truth for rendering; the loader must parse `template`, render it with the validated inputs, and convert the resulting JSON to ChatKit widgets exactly as shown in the official demo repository.
- Keep the generated tools' input validation and template rendering consistent with existing behavior, but log warnings and halt registration when `template` is missing or malformed to keep P0 quality strict.

#### P1
- Wrap the widget discovery, schema-to-model conversion, and rendering helpers into a clean, importable Python module; expose functions such as `load_widgets(widgets_dir: Path)`, `render_widget_definition(widget_def, **kwargs)`, and `generate_widget_tools(server, widget_defs)` so external consumers can embed the logic without importing the FastMCP entry point.
- Document the public API surface so that other automation scripts or backends can reuse validation logic and templates without re-implementing the MCP registration flow.

### Designs
Widget rendering should mirror the official `openai-chatkit-advanced-samples` repository where each `.widget` file's `template` block renders to the exact Card/Row/Text hierarchy. The MCP tools remain the primary surface for runtime agent invocation, but the new module-level helpers enable importing the same rendering path for demos, tests, and use cases that require tighter integration with widget generation.

## TECHNICAL CONSIDERATIONS
### Architecture Overview
The existing FastMCP server continues to scan widget definitions and build Pydantic models via `json_schema_to_pydantic`. Rendering widget templates and converting to ChatKit `WidgetComponentBase` instances should now be done via `chatkit.widgets.WidgetTemplate`. The update introduces a configuration boundary (`widgets_dir`) and packages the discovery/rendering logic so that the same components back both the server and any manual workflows.

### Technical Requirements
- Require `uv` for dependency management and rely on `fastmcp>=2.13.0.2` and `openai-chatkit>=1.1.0` as before.
- Validate that the required `widgets_dir` argument points to an existing directory and contains only `.widget` files that include a `template` field before registering MCP tools.
- Ensure template rendering continues to produce valid JSON and surface parsing errors with context so debugging via the official demo is straightforward.
- Document the newly exported module-level helpers and keep public interfaces typed for `mypy --disallow-untyped-defs`.

### AI/ML Considerations
Not applicable for this tooling update.

## LAUNCH/ROLLOUT PLAN
### Success metrics
| KPIs | Target & Rationale |
|------|--------------------|
| Widget loading coverage | 100% of entry widgets load from the user-specified `widgets_dir` without falling back to other locations, verifying the configuration guardrail. |
| Template fidelity | Every generated widget created via the template renderer matches the `openai-chatkit-advanced-samples` reference JSON structure. |
| Module adoption | At least one automation or backend imports the new module-level API and succeeds without invoking the FastMCP entry point. |

### Rollout Strategy
Ship as a minor release: update documentation to note the required `widgets_dir`, verify the loader still discovers existing `.widget` files, and ensure downstream projects switch to importing the new helpers before the change reaches production agent environments.

### Experiment Plan
1. Point `openai-chatkit-advanced-samples` at this MCP server to validate `widgets_dir` enforcement and template rendering for the existing widgets.
2. Import the new module-level helpers into `openai-chatkit-advanced-samples` to verify the widgets can load and render without invoking the FastMCP entry point.

### Estimated Launch Phases
| Phase | Target | Description |
|-------|--------|-------------|
| **Phase 1** | Developer preview | Validate `widgets_dir` enforcement and template rendering via existing tests and add fresh regression tests. |
| **Phase 2** | Internal dogfood | Export the module-level helpers, update one backend or script to consume them, and collect feedback before wider release. |

## HYPOTHESIS & RISKS
- Hypothesis: Requiring a `widgets_dir` and honoring each `.widget` file's `template` field will keep the MCP tools aligned with the official demo layouts while preventing unsupported widgets from loading.
- Risk: Forcing a single directory and template-driven render may break workflows that relied on the previous implicit discovery or on widgets that lacked templates.
- Risk Mitigation: Fail early with actionable errors when `widgets_dir` is missing and log clear schema/template validation failures, allowing teams to fix or migrate their widget definitions before the release.

## APPENDIX
- Include references to `mcp_chatkit_widget/widgets/` for widget authors and `docs/templates/requirements_template.md` for future requirement updates.
