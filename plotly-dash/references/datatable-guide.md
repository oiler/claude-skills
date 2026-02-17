# DataTable Guide

`dash_table.DataTable` is the primary component for displaying tabular data in Dash. For large datasets (>1000 rows), use server-side paging, sorting, and filtering.

## Basic DataTable

```python
from dash import Dash, dash_table
import pandas as pd

df = pd.read_csv("data.csv")

app = Dash(__name__)
app.layout = dash_table.DataTable(
    id="my-table",
    data=df.to_dict("records"),
    columns=[{"name": col, "id": col} for col in df.columns],
    page_size=20,
    style_table={"overflowX": "auto"},
)
```

## Column Configuration

```python
columns = [
    {"name": "ID", "id": "id", "type": "numeric"},
    {"name": "Name", "id": "name", "type": "text"},
    {"name": "Amount", "id": "amount", "type": "numeric",
     "format": {"specifier": "$,.2f"}},
    {"name": "Date", "id": "date", "type": "datetime"},
    {"name": "Active", "id": "active", "type": "any",
     "presentation": "dropdown"},
]
```

Column types: `"text"`, `"numeric"`, `"datetime"`, `"any"`.

## Native (Client-Side) Interactivity

Good for small datasets (<1000 rows) loaded entirely in the browser:

```python
dash_table.DataTable(
    id="interactive-table",
    data=df.to_dict("records"),
    columns=[{"name": i, "id": i, "deletable": True, "selectable": True}
             for i in df.columns],
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    row_selectable="multi",
    page_action="native",
    page_size=20,
    selected_rows=[],
)
```

## Server-Side (Backend) Paging

For large datasets. Only the current page of data is sent to the browser:

```python
from dash import Dash, dash_table, callback, Input, Output
import pandas as pd

PAGE_SIZE = 25

app.layout = dash_table.DataTable(
    id="table-paging",
    columns=[{"name": i, "id": i} for i in df.columns],
    page_current=0,
    page_size=PAGE_SIZE,
    page_count=len(df) // PAGE_SIZE + 1,
    page_action="custom",
)

@callback(
    Output("table-paging", "data"),
    Input("table-paging", "page_current"),
    Input("table-paging", "page_size"),
)
def update_table(page_current, page_size):
    start = page_current * page_size
    end = start + page_size
    return df.iloc[start:end].to_dict("records")
```

## Server-Side Paging + Sorting

```python
app.layout = dash_table.DataTable(
    id="table-sort",
    columns=[{"name": i, "id": i} for i in df.columns],
    page_current=0,
    page_size=PAGE_SIZE,
    page_action="custom",
    sort_action="custom",
    sort_mode="multi",
    sort_by=[],
)

@callback(
    Output("table-sort", "data"),
    Input("table-sort", "page_current"),
    Input("table-sort", "page_size"),
    Input("table-sort", "sort_by"),
)
def update_table(page_current, page_size, sort_by):
    dff = df.copy()
    if sort_by:
        dff = dff.sort_values(
            [col["column_id"] for col in sort_by],
            ascending=[col["direction"] == "asc" for col in sort_by],
        )
    start = page_current * page_size
    return dff.iloc[start:start + page_size].to_dict("records")
```

## Server-Side Paging + Sorting + Filtering

The full pattern for large dataset browsing:

```python
app.layout = dash_table.DataTable(
    id="table-full",
    columns=[{"name": i, "id": i} for i in df.columns],
    page_current=0,
    page_size=PAGE_SIZE,
    page_action="custom",
    sort_action="custom",
    sort_mode="multi",
    sort_by=[],
    filter_action="custom",
    filter_query="",
)

# Filter parsing operators
OPERATORS = [
    ["ge ", ">="],
    ["le ", "<="],
    ["lt ", "<"],
    ["gt ", ">"],
    ["ne ", "!="],
    ["eq ", "="],
    ["contains "],
    ["datestartswith "],
]

def split_filter_part(filter_part):
    """Parse a single filter expression like '{column} ge 100'."""
    for op_type in OPERATORS:
        for op in op_type:
            if op in filter_part:
                name_part, value_part = filter_part.split(op, 1)
                name = name_part[name_part.find("{") + 1:name_part.rfind("}")]
                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace("\\" + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part
                return name, op_type[0].strip(), value
    return [None] * 3

@callback(
    Output("table-full", "data"),
    Output("table-full", "page_count"),
    Input("table-full", "page_current"),
    Input("table-full", "page_size"),
    Input("table-full", "sort_by"),
    Input("table-full", "filter_query"),
)
def update_table(page_current, page_size, sort_by, filter_query):
    dff = df.copy()

    # Apply filters
    if filter_query:
        filtering_expressions = filter_query.split(" && ")
        for expr in filtering_expressions:
            col_name, operator, value = split_filter_part(expr)
            if operator == "contains":
                dff = dff[dff[col_name].astype(str).str.contains(str(value), case=False)]
            elif operator == "datestartswith":
                dff = dff[dff[col_name].astype(str).str.startswith(str(value))]
            elif operator == "=":
                dff = dff[dff[col_name] == value]
            elif operator == "!=":
                dff = dff[dff[col_name] != value]
            elif operator == ">":
                dff = dff[dff[col_name] > value]
            elif operator == ">=":
                dff = dff[dff[col_name] >= value]
            elif operator == "<":
                dff = dff[dff[col_name] < value]
            elif operator == "<=":
                dff = dff[dff[col_name] <= value]

    # Apply sorting
    if sort_by:
        dff = dff.sort_values(
            [col["column_id"] for col in sort_by],
            ascending=[col["direction"] == "asc" for col in sort_by],
        )

    page_count = max(1, -(-len(dff) // page_size))  # ceiling division
    start = page_current * page_size
    return dff.iloc[start:start + page_size].to_dict("records"), page_count
```

## Styling

```python
dash_table.DataTable(
    style_header={
        "backgroundColor": "#f8f9fa",
        "fontWeight": "bold",
        "border": "1px solid #dee2e6",
    },
    style_cell={
        "textAlign": "left",
        "padding": "8px 12px",
        "border": "1px solid #dee2e6",
        "fontFamily": "-apple-system, sans-serif",
        "fontSize": "14px",
    },
    style_data_conditional=[
        {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
        {"if": {"state": "active"}, "backgroundColor": "#e3f2fd", "border": "1px solid #90caf9"},
    ],
    style_table={"overflowX": "auto"},
)
```

## Conditional Formatting

```python
style_data_conditional=[
    # Highlight negative values
    {
        "if": {"filter_query": "{amount} < 0", "column_id": "amount"},
        "color": "#dc3545",
        "fontWeight": "bold",
    },
    # Color scale by value
    {
        "if": {"filter_query": "{score} >= 90"},
        "backgroundColor": "#d4edda",
    },
    {
        "if": {"filter_query": "{score} < 50"},
        "backgroundColor": "#f8d7da",
    },
]
```

## Cell Click Callbacks

```python
@callback(
    Output("detail-view", "children"),
    Input("my-table", "active_cell"),
    State("my-table", "data"),
)
def display_cell_detail(active_cell, data):
    if not active_cell:
        return "Click a cell to see details"
    row = data[active_cell["row"]]
    col = active_cell["column_id"]
    return f"Row {active_cell['row']}, Column '{col}': {row[col]}"
```

## Row Selection

```python
dash_table.DataTable(
    id="selectable-table",
    row_selectable="multi",  # or "single"
    selected_rows=[],
)

@callback(
    Output("selection-output", "children"),
    Input("selectable-table", "selected_rows"),
    State("selectable-table", "data"),
)
def handle_selection(selected_rows, data):
    if not selected_rows:
        return "No rows selected"
    selected = [data[i] for i in selected_rows]
    return f"Selected {len(selected)} rows"
```

## Export / Download

```python
dash_table.DataTable(
    export_format="csv",   # or "xlsx"
    export_headers="display",
)
```

## Fixed Headers and Columns

```python
dash_table.DataTable(
    fixed_rows={"headers": True},
    fixed_columns={"headers": True, "data": 1},  # freeze first column
    style_table={"minWidth": "100%", "height": "400px", "overflowY": "auto"},
)
```

## Virtualization (alternative to paging)

For very large client-side datasets, render only visible rows:

```python
dash_table.DataTable(
    virtualization=True,
    page_action="none",
    style_table={"height": "500px", "overflowY": "auto"},
)
```

Note: Virtualization loads all data to the browser but only renders visible rows. For truly large datasets (>50k rows), use server-side paging instead.

## Filter Syntax (for users)

In the native filter UI, users type expressions in column header boxes:
- Text: `contains value`, `= exact`, `!= not_this`
- Numeric: `> 100`, `<= 50`, `= 42`
- Date: `datestartswith 2024-01`
- Combined (across columns): Each column filter is ANDed together
