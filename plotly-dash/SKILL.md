---
name: plotly-dash-expert
description: Expert guidance for building Plotly Dash web applications. Use when user asks to create dashboards, interactive tables, data browsers, Dash apps, or mentions "Dash", "plotly", "DataTable", "dash callbacks", "dcc", or "dash_table". Covers app structure, callbacks, layouts, DataTable with server-side paging/sorting/filtering, database integration (SQLite/Postgres), multi-page apps, and self-hosted deployment with gunicorn/nginx. Focused on open-source Dash (not Dash Enterprise).
---

# Plotly Dash Expert

Expert guidance for building self-hosted Plotly Dash applications focused on browsing large datasets with interactive tables, callbacks, and database-backed ETL pipelines.

## Important: Scope and Constraints

This skill targets **open-source Dash** deployed self-hosted. The following are **Enterprise-only** and must never be used or recommended:
- `dash-design-kit` (DDK) — Enterprise styling library
- `dash-snapshots` / Snapshot Engine — PDF/link sharing
- `dash-enterprise-auth` — Enterprise authentication
- `EnterpriseDash()` constructor
- Dashboard Engine / Dashboard Toolkit
- Job Queue (Enterprise managed) — use `background=True` callbacks with DiskCache or Celery instead
- Plotly Cloud publishing via dev tools — deploy with gunicorn instead
- Data Science Workspaces

For styling, use open-source alternatives: `dash-bootstrap-components`, `dash-mantine-components`, or custom CSS in the `assets/` folder.

## Instructions

### Step 1: Understand the Request

Identify what the user needs:
- **New app from scratch** — scaffold the full app structure
- **Add a feature** — callbacks, new page, table, filter controls
- **Database integration** — SQLite or Postgres connection, ETL
- **Deployment** — gunicorn, nginx, Docker setup
- **Debug/fix** — callback issues, layout problems, performance

### Step 2: Scaffold or Modify the App

For new apps, consult `references/app-structure.md` for the standard project layout and boilerplate.

For callbacks, consult `references/callbacks-guide.md` for patterns including chained callbacks, State, PreventUpdate, Patch, background callbacks, and clientside callbacks.

For DataTable with server-side operations on large datasets, consult `references/datatable-guide.md` for backend paging, sorting, and filtering patterns.

For database integration and ETL, consult `references/database-etl.md` for SQLite/Postgres connection patterns, query helpers, and data transformation pipelines.

### Step 3: Validate

Before delivering code:
1. Verify all imports use current Dash 3.x/4.x syntax (`from dash import Dash, html, dcc, callback, Input, Output, State`)
2. Confirm no Enterprise-only imports or features are used
3. Check that callbacks have proper error handling (PreventUpdate for missing inputs)
4. For DataTable: ensure backend paging/sorting/filtering when dataset exceeds ~1000 rows
5. For deployment: verify gunicorn command references `app.server` (the Flask instance)

## Key Dash Concepts (Quick Reference)

**Current version**: Dash 3.3.0+ (docs say 3.3.0, PyPI has 4.0.0). Built on Flask.

**Core imports**:
```python
from dash import Dash, html, dcc, dash_table, callback, Input, Output, State, Patch, no_update
from dash.exceptions import PreventUpdate
```

**App initialization**:
```python
app = Dash(__name__)
server = app.server  # Flask instance — needed for gunicorn
```

**Layout**: A list or tree of components. Since Dash 2.17, layout can be a plain list:
```python
app.layout = [
    html.H1("Title"),
    dcc.Dropdown(id="my-dropdown", options=["A", "B", "C"], value="A"),
    html.Div(id="output")
]
```

**Callbacks**: Reactive functions that fire when Input properties change:
```python
@callback(
    Output("output", "children"),
    Input("my-dropdown", "value")
)
def update(value):
    return f"Selected: {value}"
```

**State**: Read a property without triggering the callback:
```python
@callback(
    Output("output", "children"),
    Input("submit-btn", "n_clicks"),
    State("my-input", "value")
)
def on_submit(n_clicks, value):
    if not n_clicks:
        raise PreventUpdate
    return f"Submitted: {value}"
```

**Multi-page apps**: Use `dash.register_page` and `pages/` directory:
```python
# app.py
app = Dash(__name__, use_pages=True)
app.layout = html.Div([dash.page_container])

# pages/home.py
import dash
dash.register_page(__name__, path="/")
layout = html.Div("Home page")
```

## Troubleshooting

### Callback not firing
- Check component `id` matches between layout and callback decorator
- Verify the component exists in the initial layout (or set `suppress_callback_exceptions=True`)
- For dynamic layouts, IDs must be defined before app starts

### DataTable shows no data
- Ensure `data` is a list of dicts: `df.to_dict('records')`
- Ensure `columns` is `[{"name": col, "id": col} for col in df.columns]`

### Gunicorn shows static page with no interactivity
- Serve `app.server`, not `app`: `gunicorn app:server` where `server = app.server`
- Do NOT use `app.run()` in production — that starts the dev server

### Callbacks modify global state
- Never modify variables outside callback scope
- Use `dcc.Store` to share data between callbacks
- For expensive computations, use caching (`flask_caching` or `diskcache`)

### Performance with large datasets
- Use backend paging/sorting/filtering (see `references/datatable-guide.md`)
- Avoid sending full dataframe to browser — paginate server-side
- Use `Patch()` for partial property updates instead of rebuilding entire figures
