# Database Integration and ETL

Patterns for connecting Dash apps to SQLite and PostgreSQL, running queries, and transforming data for display.

## SQLite Connection

```python
import sqlite3
import pandas as pd

DATABASE_PATH = "data/app.db"

def get_connection():
    """Get a SQLite connection. Use per-request, don't share across threads."""
    return sqlite3.connect(DATABASE_PATH)

def query_df(sql, params=None):
    """Execute a query and return a DataFrame."""
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params or [])

def execute(sql, params=None):
    """Execute a write query."""
    with get_connection() as conn:
        conn.execute(sql, params or [])
        conn.commit()
```

## PostgreSQL with SQLAlchemy

```python
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import pandas as pd

# Use NullPool for gunicorn with --preload to avoid shared connection issues
DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"
engine = create_engine(DATABASE_URL, poolclass=NullPool)

def query_df(sql, params=None):
    """Execute a query and return a DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})

def execute(sql, params=None):
    """Execute a write query."""
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})
```

**Important**: Use `NullPool` when deploying with gunicorn and `--preload`. Standard connection pools are not safe to share across forked worker processes.

## PostgreSQL with psycopg2 (without SQLAlchemy)

```python
import psycopg2
import psycopg2.extras
import pandas as pd

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "mydb",
    "user": "user",
    "password": "pass",
}

def query_df(sql, params=None):
    with psycopg2.connect(**DB_CONFIG) as conn:
        return pd.read_sql_query(sql, conn, params=params)

def query_dicts(sql, params=None):
    """Return list of dicts (ready for DataTable)."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
```

## Server-Side Paging with SQL

Instead of loading the entire table into pandas and slicing, push paging to the database:

```python
@callback(
    Output("table", "data"),
    Output("table", "page_count"),
    Input("table", "page_current"),
    Input("table", "page_size"),
    Input("table", "sort_by"),
    Input("table", "filter_query"),
)
def update_table(page_current, page_size, sort_by, filter_query):
    # Build WHERE clause from filter_query
    where_clause, params = build_where(filter_query)

    # Build ORDER BY from sort_by
    order_clause = build_order(sort_by)

    # Count total matching rows
    count_sql = f"SELECT COUNT(*) FROM my_table {where_clause}"
    total = query_scalar(count_sql, params)
    page_count = max(1, -(-total // page_size))

    # Fetch current page
    data_sql = f"""
        SELECT * FROM my_table
        {where_clause}
        {order_clause}
        LIMIT {page_size} OFFSET {page_current * page_size}
    """
    rows = query_dicts(data_sql, params)
    return rows, page_count
```

### Building WHERE clauses from filter_query

```python
def build_where(filter_query):
    """Convert Dash DataTable filter_query to SQL WHERE clause."""
    if not filter_query:
        return "", {}

    conditions = []
    params = {}
    parts = filter_query.split(" && ")

    for i, part in enumerate(parts):
        col_name, operator, value = split_filter_part(part)
        if col_name is None:
            continue

        param_name = f"p{i}"

        if operator == "contains":
            conditions.append(f'CAST("{col_name}" AS TEXT) ILIKE :{param_name}')
            params[param_name] = f"%{value}%"
        elif operator == "datestartswith":
            conditions.append(f'CAST("{col_name}" AS TEXT) LIKE :{param_name}')
            params[param_name] = f"{value}%"
        elif operator == "=":
            conditions.append(f'"{col_name}" = :{param_name}')
            params[param_name] = value
        elif operator == "!=":
            conditions.append(f'"{col_name}" != :{param_name}')
            params[param_name] = value
        elif operator == ">":
            conditions.append(f'"{col_name}" > :{param_name}')
            params[param_name] = value
        elif operator == ">=":
            conditions.append(f'"{col_name}" >= :{param_name}')
            params[param_name] = value
        elif operator == "<":
            conditions.append(f'"{col_name}" < :{param_name}')
            params[param_name] = value
        elif operator == "<=":
            conditions.append(f'"{col_name}" <= :{param_name}')
            params[param_name] = value

    if conditions:
        return "WHERE " + " AND ".join(conditions), params
    return "", {}

def build_order(sort_by):
    """Convert Dash DataTable sort_by to SQL ORDER BY clause."""
    if not sort_by:
        return ""
    parts = []
    for col in sort_by:
        direction = "ASC" if col["direction"] == "asc" else "DESC"
        parts.append(f'"{col["column_id"]}" {direction}')
    return "ORDER BY " + ", ".join(parts)
```

**Security note**: Always use parameterized queries for values. Column names from sort_by/filter_query should be validated against a whitelist of known columns:

```python
ALLOWED_COLUMNS = {"id", "name", "amount", "date", "category"}

def validate_column(col_name):
    if col_name not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: {col_name}")
    return col_name
```

## ETL Patterns

### Transform after query, before display

```python
def load_and_transform(filters):
    """Query raw data and apply transformations."""
    df = query_df("SELECT * FROM raw_events WHERE date >= :start", {"start": filters["start_date"]})

    # Clean
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    # Transform
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    df["amount_fmt"] = df["amount"].apply(lambda x: f"${x:,.2f}")

    # Aggregate
    summary = df.groupby("category").agg(
        total=("amount", "sum"),
        count=("id", "count"),
        avg=("amount", "mean"),
    ).reset_index()

    return df, summary
```

### Caching expensive queries

```python
from flask_caching import Cache

cache = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})
cache.init_app(server)  # server = app.server

@cache.memoize(timeout=60)
def get_summary_data(date_range, category):
    """Cache query results for 60 seconds."""
    return query_df(
        "SELECT * FROM summary WHERE date BETWEEN :start AND :end AND category = :cat",
        {"start": date_range[0], "end": date_range[1], "cat": category}
    )
```

### Sharing data between callbacks with dcc.Store

```python
app.layout = html.Div([
    dcc.Store(id="query-result"),
    html.Button("Refresh Data", id="refresh-btn"),
    dash_table.DataTable(id="data-table"),
    dcc.Graph(id="data-chart"),
])

@callback(Output("query-result", "data"), Input("refresh-btn", "n_clicks"))
def fetch_data(n_clicks):
    df = query_df("SELECT * FROM current_metrics")
    return df.to_dict("records")

@callback(Output("data-table", "data"), Input("query-result", "data"))
def update_table(records):
    return records or []

@callback(Output("data-chart", "figure"), Input("query-result", "data"))
def update_chart(records):
    if not records:
        return {}
    df = pd.DataFrame(records)
    return px.bar(df, x="category", y="value")
```

## Connection Management Tips

1. **SQLite**: Create connections per-request (they're cheap). Don't share across threads.
2. **PostgreSQL with gunicorn**: Use `NullPool` or ensure pool is created after fork (not with `--preload`).
3. **Connection timeouts**: Set `connect_timeout` and `options` in your connection string.
4. **Read replicas**: Point read-heavy Dash apps at a read replica if available.
5. **Query timeouts**: Set `statement_timeout` for PostgreSQL to prevent long-running queries from blocking workers:
   ```python
   engine = create_engine(DATABASE_URL, connect_args={"options": "-c statement_timeout=30000"})
   ```
