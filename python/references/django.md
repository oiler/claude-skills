# Django Development

Use this reference when the user is building or modifying a Django project. Covers project setup, models, views, templates, Django REST Framework APIs, admin customization, and production patterns.

## Project Setup

Start new Django projects with this structure:

```bash
uv init my-project && cd my-project
uv add django
uv run django-admin startproject config .
uv run python manage.py startapp core
```

This gives you a `pyproject.toml`-managed project with uv. The project config lives in `config/` and apps go alongside it:

```
my-project/
├── pyproject.toml
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── models.py
│   ├── views.py
│   ├── urls.py          # Create this — app-level URLs
│   ├── admin.py
│   └── tests.py
└── templates/
    └── base.html
```

### Settings Patterns

Split settings for different environments:

```python
# config/settings.py — base settings
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Use environment variables for secrets, never hardcode
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "myapp"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
```

For development, use SQLite by default and let the user switch to PostgreSQL when ready.

## Models

### Design Principles

- Every model gets a `__str__` method
- Use `Meta` class for ordering, constraints, and verbose names
- Add `created_at` / `updated_at` timestamps to most models
- Use `related_name` on all ForeignKey and M2M fields
- Prefer `TextField` over `CharField` unless you need a max length for validation

```python
from django.db import models
from django.utils import timezone

class TimestampMixin(models.Model):
    """Reusable mixin for created/updated timestamps."""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Article(TimestampMixin):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    author = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="articles",
    )
    tags = models.ManyToManyField("Tag", blank=True, related_name="articles")
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["author", "slug"],
                name="unique_author_slug",
            )
        ]

    def __str__(self):
        return self.title
```

### Querysets and Managers

Use custom managers for common queries:

```python
class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published=True)

    def by_author(self, user):
        return self.filter(author=user)

class Article(TimestampMixin):
    # ... fields ...
    objects = ArticleQuerySet.as_manager()

# Usage: Article.objects.published().by_author(user)
```

## Views

### Class-Based Views for CRUD

```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

class ArticleListView(ListView):
    model = Article
    queryset = Article.objects.published()
    paginate_by = 20

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ["title", "body", "tags"]

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
```

### Function-Based Views for Simple Cases

Use function views when a class-based view would be overkill:

```python
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def article_detail_api(request, slug):
    article = get_object_or_404(Article.objects.published(), slug=slug)
    return JsonResponse({
        "title": article.title,
        "body": article.body,
        "author": article.author.username,
    })
```

## Django REST Framework (DRF)

When the user needs an API, add DRF:

```bash
uv add djangorestframework
```

### Serializers

```python
from rest_framework import serializers

class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "slug", "body", "author", "tags", "created_at"]
        read_only_fields = ["slug", "created_at"]
```

### ViewSets

```python
from rest_framework import viewsets, permissions

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.published()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

### URL Configuration

```python
# core/urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("articles", views.ArticleViewSet)

urlpatterns = router.urls
```

## Admin Customization

Always customize admin for better usability:

```python
from django.contrib import admin

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "published", "created_at"]
    list_filter = ["published", "created_at"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]
```

## Testing Django

```python
import pytest
from django.test import Client

@pytest.fixture
def api_client():
    return Client()

@pytest.mark.django_db
def test_article_list(api_client):
    resp = api_client.get("/api/articles/")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_create_article(api_client, django_user_model):
    user = django_user_model.objects.create_user("testuser", password="pass")
    api_client.force_login(user)
    resp = api_client.post("/api/articles/", {"title": "Test", "body": "Content"})
    assert resp.status_code == 201
```

Use `pytest-django` and configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["tests.py", "test_*.py"]
```

## Key Rules

- Always use `timezone.now()` not `datetime.now()` — Django is timezone-aware
- Use `get_object_or_404` instead of manual try/except on queries
- Always add `on_delete` explicitly to ForeignKey fields
- Use migrations: `python manage.py makemigrations` then `migrate`, never edit migration files by hand unless squashing
- For new projects, use `uv` for dependency management rather than pip directly
- Use environment variables for all secrets and config that varies per environment
