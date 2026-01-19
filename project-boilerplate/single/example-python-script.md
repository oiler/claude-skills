# RSS Feed Generator

Scrape web content and generate RSS feeds for sites that don't provide them.

---

## Basic Information

**Project:** RSS Feed Generator  
**Type:** ☑ Python Script  
**Purpose:** Automated scraping and RSS feed generation for content monitoring  
**Status:** ☑ Active Development

---

## Tech Stack

**Primary:**
- Python 3.11+
- BeautifulSoup4 for HTML parsing
- Requests for HTTP
- feedgen for RSS generation

**Build Tools:**
- UV for dependency management (inline metadata)

**Runtime:**
- Python 3.11+ (standalone script, no virtual env needed with UV)
- Runs on cron/schedule for automation

**Dependencies Management:**
```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "beautifulsoup4>=4.12.0",
#     "requests>=2.31.0",
#     "feedgen>=1.0.0",
#     "python-dateutil>=2.8.0",
# ]
# ///
```

---

## Code Standards

### Python
- PEP 8 compliance
- Type hints for function signatures
- Docstrings for all public functions
- Use context managers (`with` statements)
- List comprehensions for readability
- Meaningful error messages
- No global variables (except configuration constants)

### Error Handling
- Catch specific exceptions (not bare `except`)
- Log errors with context
- Graceful degradation when possible
- Retry logic for network requests

### File Handling
- Always use `pathlib.Path` (not string concatenation)
- Context managers for file operations
- UTF-8 encoding explicit

### Git
- Atomic commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Interactive rebase for clean history
- Force push with `--force-with-lease` only

---

## Project Structure

```
rss-generator/
├── src/
│   ├── main.py                  # Entry point
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── scraper.py           # Web scraping logic
│   │   ├── parser.py            # Content extraction
│   │   ├── feed_generator.py   # RSS generation
│   │   └── cache.py             # Caching mechanism
│   └── utils/
│       ├── __init__.py
│       ├── logger.py            # Logging setup
│       ├── validators.py        # URL/data validation
│       └── file_handler.py      # File I/O utilities
├── tests/
│   ├── unit/
│   │   ├── test_scraper.py
│   │   ├── test_parser.py
│   │   └── test_validators.py
│   └── fixtures/
│       └── sample_page.html
├── data/
│   ├── cache/                   # Cached HTML (git-ignored)
│   └── feeds/                   # Generated RSS files (git-ignored)
├── logs/                        # Log files (git-ignored)
├── config.json                  # Configuration (git-ignored)
├── config.example.json          # Config template
└── README.md
```

---

## Key Patterns & Conventions

### Main Entry Point with UV Metadata
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "beautifulsoup4>=4.12.0",
#     "requests>=2.31.0",
#     "feedgen>=1.0.0",
# ]
# ///

"""
RSS Feed Generator - Main entry point
Scrapes configured websites and generates RSS feeds
"""

from pathlib import Path
import logging
from modules.scraper import scrape_content
from modules.feed_generator import generate_feed
from utils.logger import setup_logger

def main() -> None:
    """Main execution function"""
    logger = setup_logger()
    
    try:
        content = scrape_content(TARGET_URL)
        feed_path = generate_feed(content)
        logger.info(f"Feed generated: {feed_path}")
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
```

### Error Handling with Retries
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional

def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch URL content with retry logic
    
    Args:
        url: Target URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        HTML content or None on failure
    """
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None
```

### Content Parsing with BeautifulSoup
```python
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

def extract_articles(html: str) -> List[Dict[str, str]]:
    """
    Extract article data from HTML
    
    Args:
        html: HTML content to parse
        
    Returns:
        List of article dictionaries with title, link, date, description
    """
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    for article in soup.select('article.post'):
        title = article.select_one('h2.title')
        link = article.select_one('a.permalink')
        date = article.select_one('time[datetime]')
        description = article.select_one('div.excerpt')
        
        if all([title, link, date]):
            articles.append({
                'title': title.get_text(strip=True),
                'link': link.get('href'),
                'date': date.get('datetime'),
                'description': description.get_text(strip=True) if description else '',
            })
    
    return articles
```

### Safe File Operations
```python
from pathlib import Path
from typing import Optional
import json
import logging

def save_feed(feed_content: str, output_path: Path) -> bool:
    """
    Save RSS feed to file with error handling
    
    Args:
        feed_content: RSS XML content
        output_path: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(feed_content, encoding='utf-8')
        logging.info(f"Feed saved to {output_path}")
        return True
    except (IOError, OSError) as e:
        logging.error(f"Failed to save feed: {e}")
        return False
```

---

## Testing Requirements

**Priority Areas:**
1. URL validation and sanitization (security critical)
2. HTML parsing edge cases (malformed HTML, missing elements)
3. Feed generation with various content types

**Test Types Enabled:**
- ☑ Unit tests (target: 80%)
- ☑ Integration tests (scraping workflow)
- ☑ Security tests (URL validation, injection prevention)

**Critical Test Scenarios:**
1. Handle malformed HTML gracefully (missing tags, broken structure)
2. Validate URLs to prevent SSRF attacks
3. Parse dates in multiple formats correctly
4. Handle network timeouts and retries
5. Cache invalidation works correctly
6. Large content doesn't cause memory issues
7. Special characters in content (Unicode, HTML entities)

---

## Development Commands

```bash
# Run script with UV (automatically manages dependencies)
uv run src/main.py

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Type checking
mypy src/

# Linting
ruff check src/
```

---

## Environment Setup

**Required:**
- Python 3.11+
- UV package manager

**Installation:**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Dependencies managed inline via UV - no manual installation needed
# Just run: uv run src/main.py
```

**Configuration:**
```json
// config.json
{
  "target_urls": [
    "https://example.com/blog"
  ],
  "output_dir": "data/feeds",
  "cache_dir": "data/cache",
  "cache_ttl_hours": 6,
  "user_agent": "RSS-Generator/1.0",
  "request_delay_seconds": 2
}
```

---

## Security Checklist

- ☑ Validate and sanitize all URLs (prevent SSRF)
- ☑ Escape HTML content in feed generation
- ☑ Set reasonable request timeouts
- ☑ Rate limiting between requests
- ☑ No execution of scraped JavaScript
- ☑ Whitelist allowed URL schemes (http, https only)
- ☑ Validate file paths (prevent directory traversal)
- ☑ No sensitive data in logs

---

## Common Gotchas

**Issue:** BeautifulSoup warning about parser
- Solution: Explicitly specify parser: `BeautifulSoup(html, 'html.parser')` or install lxml

**Issue:** Requests hanging on slow servers
- Solution: Always set timeout parameter: `requests.get(url, timeout=10)`

**Issue:** Unicode encoding errors when saving files
- Solution: Explicitly use UTF-8: `Path.write_text(content, encoding='utf-8')`

**Issue:** Script fails when run as cron job (different environment)
- Solution: Use absolute paths via `Path(__file__).parent`, don't rely on current directory

**Issue:** Memory usage grows with large pages
- Solution: Process content in streams, use `response.iter_content()` for large responses

---

## Claude Instructions

### Skills to Use
- ☑ python-expert (for Python patterns and best practices)
- ☑ web-security (for URL validation and sanitization)

### Testing Approach
- Write tests for: All parsing functions, URL validation, error handling
- Test automatically: Every new utility function, all data transformations
- Skip testing: Simple logging statements, configuration loading

### Code Generation Preferences
- Comment level: ☑ Only complex logic
- Explanation style: ☑ Brief
- Pattern to follow: Type hints, docstrings, context managers, PEP 8

---

## Quick Reference

### Key Files
- `src/main.py` - Entry point with UV inline metadata
- `src/modules/scraper.py` - HTTP requests and retry logic
- `src/modules/parser.py` - HTML parsing with BeautifulSoup
- `src/modules/feed_generator.py` - RSS XML generation
- `src/utils/validators.py` - URL and data validation

### External Resources
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Docs](https://requests.readthedocs.io/)
- [feedgen Docs](https://feedgen.kiesow.be/)
- [UV Package Manager](https://github.com/astral-sh/uv)

### Configuration
- Config file: `config.json`
- UV metadata: Inline in `main.py` with `# /// script` blocks
- Logs: `logs/rss-generator.log`

---

## Notes & Decisions

**2026-01-19**: Using UV with inline script metadata for dependency management. No virtual environment needed - UV handles everything automatically. This makes the script truly portable and easy to run.

**2026-01-19**: Implemented caching mechanism to avoid re-scraping unchanged content. Cache invalidates after 6 hours (configurable). Cached HTML stored in `data/cache/` with URL hash as filename.

**2026-01-19**: Added rate limiting (2 seconds between requests) to be respectful to target servers. Configurable in `config.json`.

**2026-01-19**: Using `pathlib.Path` throughout instead of string paths. More Pythonic and handles cross-platform path differences.

**2026-01-19**: Decided to generate one RSS file per target URL rather than combining. Easier to manage and allows different update frequencies per source.
