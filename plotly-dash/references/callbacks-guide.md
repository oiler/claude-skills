# Callbacks Guide

Callbacks are the core interactivity mechanism in Dash. A callback is a Python function decorated with `@callback` that automatically fires when specified Input properties change.

## Basic Callback

```python
from dash import Dash, html, dcc, callback, Input, Output

@callback(
    Output("output-div", "children"),
    Input("my-dropdown", "value")
)
def update_output(selected_value):
    return f"You selected: {selected_value}"
```

- **Output**: The component property to update (component_id, property_name)
- **Input**: The component property that triggers the callback
- Arguments arrive in the order Inputs are listed

## Multiple Inputs and Outputs

```python
@callback(
    Output("graph", "figure"),
    Output("summary", "children"),
    Input("year-slider", "value"),
    Input("category-dropdown", "value")
)
def update_dashboard(year, category):
    filtered = df[(df.year == year) & (df.category == category)]
    fig = px.bar(filtered, x="name", y="value")
    summary = f"Showing {len(filtered)} records for {category} in {year}"
    return fig, summary
```

## State (Read Without Triggering)

Use `State` to read a component's value without triggering the callback when it changes:

```python
from dash import State
from dash.exceptions import PreventUpdate

@callback(
    Output("result", "children"),
    Input("submit-btn", "n_clicks"),
    State("text-input", "value"),
    State("number-input", "value")
)
def on_submit(n_clicks, text, number):
    if not n_clicks:
        raise PreventUpdate
    return f"Submitted: {text}, {number}"
```

## PreventUpdate and no_update

```python
from dash import no_update
from dash.exceptions import PreventUpdate

@callback(
    Output("output-a", "children"),
    Output("output-b", "children"),
    Input("my-input", "value")
)
def selective_update(value):
    if value is None:
        raise PreventUpdate  # Skip ALL outputs
    if value == "special":
        return "Special!", no_update  # Update only first output
    return f"Value: {value}", f"Also: {value}"
```

## prevent_initial_call

Stop a callback from firing on page load:

```python
@callback(
    Output("download", "data"),
    Input("export-btn", "n_clicks"),
    prevent_initial_call=True
)
def export_data(n_clicks):
    return dcc.send_data_frame(df.to_csv, "export.csv")
```

## Chained Callbacks

Output of one callback becomes Input of another. Dash resolves the execution order automatically:

```python
@callback(Output("city-dropdown", "options"), Input("state-dropdown", "value"))
def set_cities(state):
    return [{"label": c, "value": c} for c in get_cities(state)]

@callback(Output("city-dropdown", "value"), Input("city-dropdown", "options"))
def set_default_city(options):
    return options[0]["value"] if options else None

@callback(Output("data-table", "data"), Input("city-dropdown", "value"))
def load_data(city):
    if not city:
        raise PreventUpdate
    return query_data(city).to_dict("records")
```

## Partial Property Updates (Patch)

Update part of a property without sending the whole thing back. Useful for large figures:

```python
from dash import Patch

@callback(
    Output("my-graph", "figure"),
    Input("color-picker", "value")
)
def update_title_color(color):
    patched = Patch()
    patched["layout"]["title"]["font"]["color"] = color
    return patched
```

Patch supports assignment, list append/extend, and dict merge.

## dcc.Store (Sharing Data Between Callbacks)

Never modify global variables in callbacks. Use `dcc.Store` for intermediate data:

```python
app.layout = html.Div([
    dcc.Store(id="intermediate-data"),
    dcc.Dropdown(id="query-selector", options=[...]),
    html.Div(id="table-output"),
    dcc.Graph(id="chart-output"),
])

@callback(Output("intermediate-data", "data"), Input("query-selector", "value"))
def fetch_data(query_id):
    df = run_query(query_id)
    return df.to_dict("records")  # Must be JSON-serializable

@callback(Output("table-output", "children"), Input("intermediate-data", "data"))
def update_table(data):
    if not data:
        raise PreventUpdate
    return dash_table.DataTable(data=data, columns=[...])

@callback(Output("chart-output", "figure"), Input("intermediate-data", "data"))
def update_chart(data):
    if not data:
        raise PreventUpdate
    df = pd.DataFrame(data)
    return px.bar(df, x="category", y="total")
```

Store types: `"memory"` (default, lost on refresh), `"session"` (per tab), `"local"` (persistent).

## Background Callbacks

For long-running tasks (>30s or CPU-intensive), use background callbacks to avoid blocking:

```python
import diskcache
from dash import DiskcacheManager

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = Dash(__name__, background_callback_manager=background_callback_manager)

@callback(
    Output("result", "children"),
    Input("run-btn", "n_clicks"),
    background=True,
    running=[
        (Output("run-btn", "disabled"), True, False),
        (Output("status", "children"), "Running...", ""),
    ],
    progress=[Output("progress-bar", "value")],
    prevent_initial_call=True
)
def long_computation(set_progress, n_clicks):
    for i in range(100):
        time.sleep(0.1)
        set_progress(str(i))
    return "Done!"
```

For production, use Celery instead of DiskCache:
```python
from dash import CeleryManager
from celery import Celery

celery_app = Celery(__name__, broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")
background_callback_manager = CeleryManager(celery_app)
```

## Clientside Callbacks

Run JavaScript in the browser to avoid round-trips for simple transformations:

```python
from dash import clientside_callback

clientside_callback(
    """
    function(value) {
        return value ? value.toUpperCase() : '';
    }
    """,
    Output("upper-output", "children"),
    Input("text-input", "value")
)
```

## Common Callback Patterns for Data Browsing

### Filter chain (dropdown -> table -> detail view)
```python
@callback(Output("main-table", "data"), Input("filter-dropdown", "value"))
def filter_table(filter_val):
    return query_filtered(filter_val).to_dict("records")

@callback(
    Output("detail-panel", "children"),
    Input("main-table", "active_cell"),
    State("main-table", "data")
)
def show_detail(active_cell, data):
    if not active_cell:
        raise PreventUpdate
    row = data[active_cell["row"]]
    return html.Pre(json.dumps(row, indent=2))
```

### Debounced search input
```python
dcc.Input(id="search", type="text", debounce=True, placeholder="Search...")

@callback(Output("results", "data"), Input("search", "value"))
def search(term):
    if not term or len(term) < 2:
        raise PreventUpdate
    return search_database(term).to_dict("records")
```

## Gotchas

1. **Callbacks must be defined before `app.run()`** — all callbacks are introspected at startup
2. **Callback outputs cannot overlap** — two callbacks cannot write to the same Output
3. **Don't modify global state** — use `dcc.Store` or caching instead
4. **Circular callbacks** — allowed within a single callback (Dash 1.19+), not across callbacks
5. **Dynamic components** — set `suppress_callback_exceptions=True` if callbacks reference components created by other callbacks
