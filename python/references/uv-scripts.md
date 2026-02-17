# uv Scripts — One-Off Tools and Inline Dependencies

Use this reference when the user wants to write a quick script, CLI tool, or one-off utility without setting up a full project. uv's inline dependency metadata lets you declare deps inside the script itself — no virtualenv, no requirements.txt, no pyproject.toml.

## When to Use uv Scripts

- User says "quick script", "one-off", "just run this", "CLI tool", "utility"
- Task is self-contained in a single file
- User wants to share a script that others can run without setup
- Prototyping before committing to a full project

## The Inline Metadata Pattern

Place a PEP 723 metadata block at the top of your script:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
#     "rich>=13.0",
# ]
# ///

"""Fetch and display GitHub user info."""

import httpx
from rich.console import Console
from rich.table import Table
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: github-user.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    resp = httpx.get(f"https://api.github.com/users/{username}")
    resp.raise_for_status()
    user = resp.json()

    console = Console()
    table = Table(title=f"GitHub: {username}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Name", user.get("name", "N/A"))
    table.add_row("Bio", user.get("bio", "N/A"))
    table.add_row("Public Repos", str(user["public_repos"]))
    table.add_row("Followers", str(user["followers"]))
    console.print(table)

if __name__ == "__main__":
    main()
```

Run it with: `uv run script.py <args>`

uv automatically creates an isolated environment, installs the declared dependencies, and runs the script. No prior setup needed.

## Running uv Scripts in Claude's Environment

When executing uv scripts inside Claude's sandbox:

```bash
# Install uv first (if not already available)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Run the script — uv handles deps automatically
uv run script.py
```

Always check if uv is available before installing:
```bash
which uv || (curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH")
```

## Script Structure Rules

1. **Shebang line** — always include `#!/usr/bin/env -S uv run --script` so the script is directly executable
2. **Metadata block** — must be the PEP 723 `# /// script` format, placed before any imports
3. **Docstring** — brief description right after the metadata block
4. **`__main__` guard** — always include, even for simple scripts
5. **`sys.exit()`** — return meaningful exit codes (0 = success, 1 = user error, 2 = runtime error)
6. **Type hints** — use them even in scripts, they help readability

## CLI Argument Patterns

For simple scripts (1-3 args), use `sys.argv` directly:

```python
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: script.py <input-file>", file=sys.stderr)
        sys.exit(1)
    input_path = Path(sys.argv[1])
```

For anything more complex, add `click` to dependencies:

```python
# /// script
# dependencies = ["click>=8.1"]
# ///

import click

@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="out.json", help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(input_file: str, output: str, verbose: bool):
    """Process INPUT_FILE and write results to output."""
    ...
```

## Common One-Off Script Patterns

### File processor
```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas>=2.2"]
# ///

"""Clean and transform a CSV file."""
import pandas as pd
import sys
from pathlib import Path

def main():
    src = Path(sys.argv[1])
    df = pd.read_csv(src)
    # ... transformations ...
    out = src.with_stem(f"{src.stem}_cleaned")
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")

if __name__ == "__main__":
    main()
```

### API client
```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "rich>=13.0"]
# ///

"""Query an API and display results."""
import httpx
from rich import print as rprint
import sys

def main():
    query = " ".join(sys.argv[1:]) or "python"
    resp = httpx.get("https://api.example.com/search", params={"q": query})
    resp.raise_for_status()
    for item in resp.json()["results"]:
        rprint(f"[bold]{item['name']}[/bold]: {item['description']}")

if __name__ == "__main__":
    main()
```

### Data converter
```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0"]
# ///

"""Convert YAML to JSON."""
import json, yaml, sys
from pathlib import Path

def main():
    src = Path(sys.argv[1])
    data = yaml.safe_load(src.read_text())
    out = src.with_suffix(".json")
    out.write_text(json.dumps(data, indent=2))
    print(f"Converted {src} -> {out}")

if __name__ == "__main__":
    main()
```

## Key Rules

- Never create a virtualenv or pyproject.toml for a uv one-off script
- Always pin minimum versions in dependencies (`"httpx>=0.27"` not just `"httpx"`)
- Prefer `rich` for terminal output when the script has any display complexity
- Prefer `click` over `argparse` for CLI args (cleaner API, better help output)
- Prefer `httpx` over `requests` (modern, async-capable, better defaults)
- If the user later wants to turn a script into a full project, that's a separate workflow — don't preemptively add project structure
