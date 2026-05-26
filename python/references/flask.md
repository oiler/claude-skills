# Flask Development

Use this reference when the user is building or modifying a Flask web app or simple API.

## When to choose Flask vs FastAPI

| Factor | Flask | FastAPI |
|---|---|---|
| Best for | Server-rendered HTML, simple APIs, prototypes | API-first backends, high-performance services |
| Async | Possible but not native (use Quart if needed) | Built-in, first-class async/await |
| Validation | Manual or with Flask-WTF / Marshmallow | Automatic via Pydantic models |
| Docs | Manual (add Swagger via flask-smorest) | Auto-generated OpenAPI/Swagger UI |
| Learning curve | Lower — minimal conventions | Moderate — requires Pydantic understanding |

If the user doesn't specify, ask. If they say "API", default to FastAPI. If they say "web app" or "website", default to Flask.

## Project Setup

```bash
uv init my-flask-app && cd my-flask-app
uv add flask
```

Structure for anything beyond a single file:

```
my-flask-app/
├── pyproject.toml
├── app/
│   ├── __init__.py        # create_app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── models.py
│   ├── templates/
│   │   └── base.html
│   └── static/
└── tests/
    └── test_routes.py
```

## Application Factory

Always use the factory pattern — never a global `app` object:

```python
# app/__init__.py
from flask import Flask

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE_URL="sqlite:///app.db",
    )
    if config:
        app.config.from_mapping(config)

    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
```

## Blueprints for Organization

```python
# app/routes/main.py
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/api/items", methods=["GET"])
def list_items():
    page = request.args.get("page", 1, type=int)
    # ... fetch items ...
    return jsonify({"items": items, "page": page})

@bp.route("/api/items", methods=["POST"])
def create_item():
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "name is required"}), 400
    # ... create item ...
    return jsonify(item), 201
```

## Error Handling

```python
# In create_app or a blueprint
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "not found"}), 404
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Server error: {e}")
    return jsonify({"error": "internal server error"}), 500
```

## Database with SQLAlchemy

```bash
uv add flask-sqlalchemy
```

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    db.init_app(app)
    return app

# models.py
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def to_dict(self):
        return {"id": self.id, "name": self.name}
```

## Testing Flask

```python
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite://"})
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_create_item(client):
    resp = client.post("/api/items", json={"name": "Widget"})
    assert resp.status_code == 201
    assert resp.json["name"] == "Widget"
```

## Key Flask Rules

- Always use an application factory — never a global `app` object
- Separate routes into blueprints once you have more than ~5 endpoints
- Use environment variables for configuration (secrets, database URLs, debug flags)
- Return consistent error response shapes across all endpoints
- Use the framework test client, not a running server
- For production, use gunicorn — never the dev server
