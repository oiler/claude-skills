---
name: python-expert
description: Expert guidance for Python programming covering modern best practices, standard library usage, popular frameworks (Flask, Django, FastAPI), data science libraries (pandas, numpy), async programming, testing, type hints, packaging, debugging, and performance optimization.
---

# Python Expert

Provides expert guidance on Python programming across all domains and skill levels.

## Core Expertise Areas

### Language Fundamentals

**Modern Python Features**
- Use type hints for better code clarity and IDE support
- Leverage dataclasses for data-oriented classes
- Apply f-strings for string formatting
- Use match-case statements (Python 3.10+)
- Implement context managers with contextlib

**Object-Oriented Programming**
- Design classes with clear responsibilities
- Use properties for controlled attribute access
- Implement special methods (__init__, __str__, __repr__, etc.)
- Apply inheritance and composition appropriately
- Follow SOLID principles

**Functional Programming**
- Use comprehensions (list, dict, set, generator)
- Apply map, filter, reduce when appropriate
- Create and use decorators
- Implement higher-order functions
- Use functools and itertools modules

### Standard Library Mastery

**Essential Modules**
- collections: defaultdict, Counter, deque, namedtuple
- itertools: chain, combinations, groupby, islice
- functools: lru_cache, partial, wraps
- pathlib: modern file path operations
- datetime: time and date handling
- json/csv: data serialization
- logging: application logging
- argparse/click: CLI argument parsing

### Async Programming

**async/await Pattern**
```python
import asyncio

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    results = await asyncio.gather(
        fetch_data(url1),
        fetch_data(url2)
    )
```

**Key Concepts**
- Use async/await for I/O-bound operations
- Leverage asyncio.gather for concurrent tasks
- Apply aiohttp for async HTTP requests
- Understand event loops and coroutines

### Popular Frameworks

**Web Frameworks**
- Flask: lightweight, flexible micro-framework
- Django: full-featured framework with ORM
- FastAPI: modern, high-performance API framework

**Data Science**
- pandas: data manipulation and analysis
- numpy: numerical computing
- matplotlib/seaborn: data visualization
- scikit-learn: machine learning

**Testing**
- pytest: powerful testing framework
- unittest: standard library testing
- mock/unittest.mock: mocking dependencies

### Best Practices

**Code Quality**
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Keep functions small and focused
- Add docstrings for modules, classes, functions
- Use type hints for function signatures

**Error Handling**
```python
def process_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except PermissionError:
        logger.error(f"Permission denied: {filepath}")
        raise
```

**Virtual Environments**
- Use venv or virtualenv for isolation
- Maintain requirements.txt or pyproject.toml
- Use pip-tools for dependency management
- Consider poetry or pipenv for modern workflows

### Performance Optimization

**Profiling & Optimization**
- Use timeit for micro-benchmarks
- Apply cProfile for performance profiling
- Leverage memory_profiler for memory analysis
- Use line_profiler for line-by-line profiling

**Common Optimizations**
- Use generators for large datasets
- Apply set operations for membership tests
- Cache expensive computations with lru_cache
- Use appropriate data structures (list vs deque vs set)
- Employ list comprehensions over loops when readable

## Common Patterns

**Context Manager**
```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    resource = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource)
```

**Decorator with Arguments**
```python
from functools import wraps

def retry(max_attempts=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
        return wrapper
    return decorator
```

**Property with Validation**
```python
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius
    
    @property
    def celsius(self):
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("Temperature below absolute zero")
        self._celsius = value
```

## Troubleshooting Approach

1. Read error messages carefully - Python errors are descriptive
2. Use print statements or debugger (pdb, ipdb) for flow analysis
3. Check variable types with type() and isinstance()
4. Verify import paths and module availability
5. Test with minimal reproducible examples
6. Check Python version compatibility
7. Review virtual environment and dependencies
8. Use linters (pylint, flake8) for code issues