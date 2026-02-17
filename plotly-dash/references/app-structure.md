# App Structure and Project Layout

## Standard Project Structure

```
my-dash-app/
├── app.py                 # Main entry point
├── server.py              # Optional: Flask server config
├── requirements.txt       # Dependencies
├── Procfile               # For gunicorn: web: gunicorn app:server
├── assets/                # Auto-served static files
│   ├── style.css          # Custom CSS (auto-loaded)
│   ├── favicon.ico
│   └── logo.png
├── pages/                 # Multi-page app pages
│   ├── home.py
│   ├── data_browser.py
│   └── analytics.py
├── components/            # Reusable UI components
│   ├── navbar.py
│   └── data_table.py
├── data/                  # Data access layer
│   ├── database.py        # Connection helpers
│   └── queries.py         # SQL queries
└── utils/                 # Shared utilities
    └── etl.py             # Transform functions
```

## Minimal Single-File App

```python
from dash import Dash, html, dcc, callback, Input, Output

app = Dash(__name__)
server = app.server  # Expose Flask server for gunicorn

app.layout = [
    html.H1("My Dashboard"),
    dcc.Dropdown(id="selector", options=["Option A", "Option B"], value="Option A"),
    html.Div(id="content")
]

@callback(Output("content", "children"), Input("selector", "value"))
def update_content(value):
    return f"You selected: {value}"

if __name__ == "__main__":
    app.run(debug=True)
```

Run dev: `python app.py`
Run prod: `gunicorn app:server -b 0.0.0.0:8050 -w 4`

## Multi-Page App Setup

```python
# app.py
import dash
from dash import Dash, html, dcc

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server

app.layout = html.Div([
    html.Nav([
        html.H2("My App"),
        html.Div([
            dcc.Link(page["name"], href=page["relative_path"], style={"margin": "0 10px"})
            for page in dash.page_registry.values()
        ])
    ]),
    html.Hr(),
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)
```

```python
# pages/home.py
import dash
from dash import html

dash.register_page(__name__, path="/", name="Home")

layout = html.Div([
    html.H1("Welcome"),
    html.P("Select a page from the navigation above.")
])
```

```python
# pages/data_browser.py
import dash
from dash import html, dcc, callback, Input, Output, dash_table

dash.register_page(__name__, path="/browse", name="Data Browser")

layout = html.Div([
    html.H1("Data Browser"),
    # components here
])
```

## Flask Configuration (via underlying server)

Dash wraps Flask. Access the Flask app with `app.server`:

```python
app = Dash(__name__)
server = app.server

# Flask config
server.config["SECRET_KEY"] = "your-secret-key"
server.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB upload limit

# Add Flask routes alongside Dash
@server.route("/api/health")
def health_check():
    return {"status": "ok"}
```

## Custom CSS and Assets

Place CSS/JS files in `assets/` — Dash auto-loads them alphabetically.

```css
/* assets/style.css */
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.dash-table-container { margin: 20px 0; }
```

## Styling with Open-Source Libraries

Use `dash-bootstrap-components` for responsive layouts:

```python
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard"), width=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="filter", options=[...]), width=4),
        dbc.Col(html.Div(id="table-container"), width=8),
    ])
], fluid=True)
```

Or `dash-mantine-components` for a modern component system:

```python
import dash_mantine_components as dmc

app.layout = dmc.MantineProvider([
    dmc.Container([
        dmc.Title("Dashboard", order=1),
        dmc.SimpleGrid(cols={"base": 1, "md": 2}, children=[...])
    ])
])
```

## Deployment: Self-Hosted with Gunicorn + Nginx

### Gunicorn

```bash
# Basic
gunicorn app:server -b 0.0.0.0:8050 -w 4

# With gevent for async support (recommended for Dash)
pip install gevent
gunicorn app:server -b 0.0.0.0:8050 -w 4 --worker-class gevent

# With timeout for long callbacks
gunicorn app:server -b 0.0.0.0:8050 -w 4 --timeout 120
```

Key: `app:server` means the `server` variable in `app.py`. Set `server = app.server` in your code.

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name dash.example.com;

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (needed for hot-reload in dev, optional in prod)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8050
CMD ["gunicorn", "app:server", "-b", "0.0.0.0:8050", "-w", "4", "--worker-class", "gevent"]
```

### URL Prefix (sub-path deployment)

When serving under a sub-path like `/dashboard/`:

```python
app = Dash(
    __name__,
    requests_pathname_prefix="/dashboard/",
    routes_pathname_prefix="/dashboard/",
)
```

Nginx:
```nginx
location /dashboard/ {
    proxy_pass http://127.0.0.1:8050/dashboard/;
}
```

## Requirements File

```
dash>=3.0
pandas
sqlalchemy
psycopg2-binary  # for PostgreSQL
dash-bootstrap-components
gunicorn
gevent
```
