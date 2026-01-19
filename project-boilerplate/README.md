# Claude Code Readme

## Summary
The CLAUDE.md file is your project's guide for Claude Code. Based on your development style and the skills we've created, here's what you should include:

## Essential Sections for CLAUDE.md

### 1. Project Overview

- Purpose: What the project does (1-2 sentences)
- Tech Stack: Frameworks, languages, key dependencies
- Architecture: High-level structure (WordPress theme, Django app, FastAPI service, etc.)

### 2. Code Standards & Conventions

Since you have strong preferences:

- WordPress: VIP compliance required, modular inc/functions structure, text domain constants
- Python: UV for dependencies, functional patterns preferred, type hints encouraged
- CSS/Sass: Semantic classes over utilities, dart-sass compilation, 2-3 level nesting max
- JavaScript: ES6+, functional patterns, broad browser compatibility
- Git: Atomic commits, interactive rebase for clean history

### 3. Security Requirements

Point to your security skill or highlight:

- All user input must be sanitized
- All output must be escaped (context-appropriate)
- Prepared statements/ORM only for database queries
- No secrets in code (use environment variables)
- WordPress: nonces, capability checks, VIP standards

### 4. Project Structure

Map out your directory structure:
```
/inc
  /functions
    - setup.php
    - enqueue.php
    - custom-post-types.php
/sass
  /vendor
  /core
  /pages
/js
```

### 5. Development Workflow

- Build commands: Your zsh aliases, dart-sass compilation
- Testing approach: How to verify changes
- Deployment: Any specific requirements

### 6. Context & Constraints

- Target environment: WordPress version, PHP version, Python version
- Browser support: Your compatibility requirements
- Performance: Any specific considerations
- Accessibility: WCAG standards if applicable

### 7. File-Specific Guidelines

For complex areas:

- Custom post type registration patterns
- Gutenberg block structure
- API endpoint patterns
- Database schema notes

## Tips for Your CLAUDE.md

Be specific about what you care about:

- If you have strong opinions on code organization, document them
- Include common gotchas or past mistakes to avoid
- Reference your skills when relevant ("Follow patterns in WordPress expert skill")

Keep it current:

- Update as patterns emerge
- Add examples of preferred approaches
- Document decisions and rationale

Don't over-document:

- Claude Code is smart - avoid explaining basics
- Focus on project-specific conventions
- Point to external docs rather than duplicating them

## Example CLAUDE.md Template

- (CLAUDE.md)[CLAUDE.md]
- (SINGLE_FILE_GUIDE.md)[SINGLE_FILE_GUIDE.md]
- (COMPLETE_GUIDE.md)[COMPLETE_GUIDE.md]
