# Project Directory Structure Guide

This document shows recommended directory structures for different project types using the Oiler boilerplate.

---

## Base Structure (All Projects)

```
project-root/
├── PROJECT_STANDARDS.md       # Universal coding standards
├── PROJECT_CONFIG.md          # Project-specific configuration
├── TEST_REQUIREMENTS.md       # Testing strategy and requirements
├── project.yml                # Machine-readable metadata
├── README.md                  # Project overview and setup
├── CHANGELOG.md               # Version history
├── QUICKSTART.md              # Quick reference (optional, can delete)
├── .gitignore                 # Git ignore rules
├── docs/                      # Additional documentation
│   ├── api/                   # API documentation
│   ├── guides/                # User guides
│   └── architecture/          # Architecture decisions
└── config/                    # Configuration files
    └── .env.example           # Environment variable template
```

---

## Vanilla JavaScript Web Application

```
project-root/
├── [Base Structure files]
├── src/
│   ├── js/
│   │   ├── main.js            # Entry point
│   │   ├── modules/           # Feature modules
│   │   │   ├── data-processor.js
│   │   │   ├── ui-controller.js
│   │   │   └── validator.js
│   │   └── utils/             # Helper utilities
│   │       ├── dom.js
│   │       ├── string.js
│   │       └── validation.js
│   ├── css/
│   │   ├── vendor/            # Third-party CSS
│   │   ├── core/              # Base styles, variables, mixins
│   │   │   ├── _variables.scss
│   │   │   ├── _mixins.scss
│   │   │   ├── _reset.scss
│   │   │   └── _typography.scss
│   │   ├── pages/             # Page-specific styles
│   │   │   ├── _home.scss
│   │   │   └── _about.scss
│   │   └── main.scss          # Import manifest
│   └── index.html
├── tests/
│   ├── unit/
│   │   ├── data-processor.test.js
│   │   └── validator.test.js
│   ├── integration/
│   │   └── ui-flow.test.js
│   ├── e2e/
│   │   └── user-journey.test.js
│   └── fixtures/
│       └── sample-data.json
├── build/                     # Generated files (git-ignored)
│   ├── css/
│   ├── js/
│   └── index.html
└── package.json               # Node dependencies
```

---

## WordPress Custom Theme

```
project-root/
├── [Base Structure files]
├── inc/
│   ├── functions/             # Modular function files
│   │   ├── enqueue.php
│   │   ├── theme-setup.php
│   │   ├── custom-post-types.php
│   │   ├── menus.php
│   │   └── security.php
│   └── blocks/                # Custom Gutenberg blocks
│       ├── hero/
│       │   ├── block.json
│       │   ├── render.php
│       │   └── editor.js
│       └── testimonial/
├── template-parts/            # Reusable template components
│   ├── header/
│   │   ├── site-header.php
│   │   └── site-nav.php
│   ├── content/
│   │   ├── content-single.php
│   │   └── content-archive.php
│   └── footer/
│       └── site-footer.php
├── assets/
│   ├── src/
│   │   ├── scss/
│   │   │   ├── vendor/
│   │   │   ├── core/
│   │   │   ├── pages/
│   │   │   └── style.scss
│   │   └── js/
│   │       ├── main.js
│   │       └── modules/
│   └── build/                 # Compiled assets (git-ignored)
│       ├── css/
│       └── js/
├── tests/
│   ├── php/
│   │   ├── unit/
│   │   └── integration/
│   └── js/
│       └── blocks/
├── functions.php              # Main functions file (includes only)
├── style.css                  # Theme header (required by WP)
├── index.php                  # Fallback template
├── header.php
├── footer.php
├── single.php
├── archive.php
└── package.json
```

---

## WordPress Plugin/Block

```
project-root/
├── [Base Structure files]
├── plugin-name.php            # Main plugin file
├── includes/
│   ├── class-plugin-name.php
│   ├── class-activator.php
│   ├── class-deactivator.php
│   └── blocks/
│       ├── resource-block/
│       │   ├── block.json
│       │   ├── render.php
│       │   ├── edit.js
│       │   └── save.js
│       └── form-block/
├── admin/
│   ├── class-admin.php
│   └── views/
│       └── settings-page.php
├── public/
│   └── class-public.php
├── assets/
│   ├── src/
│   │   ├── scss/
│   │   └── js/
│   └── build/
├── tests/
│   ├── php/
│   │   ├── unit/
│   │   └── integration/
│   └── js/
└── package.json
```

---

## Python Automation Script

```
project-root/
├── [Base Structure files]
├── src/
│   ├── main.py                # Entry point
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── data_processor.py
│   │   ├── file_handler.py
│   │   └── api_client.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
├── tests/
│   ├── unit/
│   │   ├── test_data_processor.py
│   │   └── test_validators.py
│   ├── integration/
│   │   └── test_api_flow.py
│   └── fixtures/
│       └── sample_data.json
├── data/                      # Input/output data (git-ignored)
│   ├── input/
│   └── output/
├── logs/                      # Log files (git-ignored)
├── requirements.txt           # Python dependencies
└── pyproject.toml            # UV configuration (optional)
```

---

## Python Web Application (Flask/FastAPI)

```
project-root/
├── [Base Structure files]
├── src/
│   ├── app.py                 # Application entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── post.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── data_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   └── decorators.py
│   ├── templates/             # HTML templates (Flask)
│   │   ├── base.html
│   │   └── index.html
│   └── static/                # Static assets
│       ├── css/
│       ├── js/
│       └── images/
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── integration/
│   │   └── test_routes.py
│   └── e2e/
│       └── test_user_flow.py
├── migrations/                # Database migrations
├── logs/
├── requirements.txt
└── .env.example
```

---

## Key Principles

### Organization
- **Flat when possible**: Avoid deep nesting
- **Group by feature**: Not by file type (when it makes sense)
- **Clear naming**: Descriptive folder and file names
- **Consistent structure**: Same patterns across similar projects

### Git Ignore
- **Build outputs**: Never commit generated files
- **Dependencies**: node_modules, venv, vendor
- **Environment**: .env files, local config
- **Logs**: Application logs
- **OS files**: .DS_Store, Thumbs.db

### Documentation Location
- **Project root**: Core project documentation
- **docs/**: Extended documentation
- **Inline**: Code comments for complex logic
- **README in folders**: Explain folder purpose if not obvious

### Testing Organization
- **Mirror src structure**: Tests follow same organization as source
- **Separate by type**: unit/, integration/, e2e/
- **Fixtures**: Shared test data in fixtures/ or __fixtures__/
- **Helpers**: Test utilities in helpers/ or test_utils/

---

## Customization Notes

### Adapt to Your Needs
- Add folders as needed for your project
- Remove sections that don't apply
- Maintain shallow hierarchy
- Keep it simple and navigable

### Common Additions
- `scripts/`: Build and automation scripts
- `examples/`: Usage examples
- `fixtures/`: Test fixtures and sample data
- `migrations/`: Database migrations
- `locales/`: Internationalization files

### Project-Specific
Document any project-specific structure decisions in PROJECT_CONFIG.md under "File Structure" section.

---

**Remember**: The best structure is one that makes your project easy to navigate and maintain!
