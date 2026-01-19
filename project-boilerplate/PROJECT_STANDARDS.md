# Project Standards

**Version:** 1.0  
**Last Updated:** January 2026

This document defines universal standards that apply to all Oiler projects, regardless of project type. These standards ensure consistency, maintainability, and quality across your entire codebase.

---

## Code Quality Principles

### Clean Architecture
- **Modularity First**: Break code into discrete, single-purpose modules
- **Shallow Inheritance**: Maximum 2-3 levels of nesting/hierarchy
- **Self-Documenting**: Code structure serves as documentation
- **Independence**: Components should operate with minimal external dependencies
- **Minimal Maintenance**: Design for long-term stability with infrequent updates

### Security Standards
- **Input Validation**: Never trust user input, validate and sanitize all data
- **Output Escaping**: Context-appropriate escaping for all output
- **SQL Injection Prevention**: Use prepared statements, never string concatenation
- **XSS Prevention**: Escape all user-generated content in HTML contexts
- **Path Traversal Protection**: Validate file paths, use safe path joining methods
- **Authentication**: Implement proper session management and CSRF protection
- **Sensitive Data**: Never log passwords, API keys, or PII

### Performance Standards
- **Optimize for Speed**: Minimize HTTP requests, optimize assets
- **Lazy Loading**: Load resources only when needed
- **Caching**: Implement appropriate caching strategies
- **Database Efficiency**: Use indexed queries, avoid N+1 queries
- **Asset Optimization**: Minify CSS/JS, optimize images

---

## Code Style Guidelines

### General Conventions
- **Indentation**: 2 spaces (JavaScript/CSS) or 4 spaces (Python)
- **Line Length**: 80-100 characters maximum
- **Naming**: Clear, descriptive names over brevity
- **Comments**: Explain "why" not "what", document complex logic
- **File Organization**: Logical grouping, consistent structure

### JavaScript Standards
- **Modern ES6+**: Use features supported since 2017
- **Functional Patterns**: Prefer pure functions over classes
- **Const by Default**: Use `const` unless reassignment needed
- **Arrow Functions**: For callbacks and short functions
- **Template Literals**: For string interpolation
- **Destructuring**: Extract object/array values cleanly
- **Modules**: Use ES6 import/export syntax
- **Error Handling**: Comprehensive try/catch, meaningful error messages

### CSS/Sass Standards
- **Semantic Classes**: Describe purpose, not appearance
- **BEM Methodology**: Block__Element--Modifier naming
- **Mobile First**: Base styles for mobile, enhance for desktop
- **Custom Properties**: Use CSS variables for theming
- **Logical Properties**: Use logical properties for RTL support
- **Shallow Nesting**: Maximum 2-3 levels in Sass
- **No `!important`**: Solve specificity issues through architecture

### Python Standards
- **PEP 8 Compliance**: Follow Python style guide
- **Type Hints**: Use for function signatures when helpful
- **Docstrings**: Document all public functions/classes
- **Context Managers**: Use `with` statements for resources
- **List Comprehensions**: When they improve readability
- **Error Messages**: Clear, actionable feedback

### WordPress Standards
- **VIP Compliance**: Follow WordPress VIP coding standards
- **Text Domains**: Use constants, never hardcoded strings
- **Nonces**: Implement for all form submissions
- **Sanitization**: Input on save, escape on output
- **Hooks**: Use appropriate actions and filters
- **Template Parts**: Break templates into logical components

---

## Git Workflow

### Commit Standards
- **Atomic Commits**: One logical change per commit
- **Clear Messages**: Descriptive present-tense commit messages
- **Conventional Commits**: Use type prefixes (feat:, fix:, docs:, refactor:, test:)
- **Interactive Rebase**: Clean up history before merging

### Branch Strategy
- **Main Branch**: Always deployable, protected
- **Feature Branches**: Short-lived, focused on single features
- **Naming**: `feature/description`, `fix/issue`, `refactor/component`

### Code Review Process
- **Self-Review**: Review your own diff before requesting review
- **Test Verification**: All tests pass before review
- **Documentation**: Update docs alongside code changes

---

## Testing Philosophy

### Test Coverage Goals
- **Critical Paths**: 100% coverage for security-critical code
- **Business Logic**: 80%+ coverage for core functionality
- **Edge Cases**: Test boundary conditions and error states
- **Regression**: Add tests for all bugs before fixing

### Test Types
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Visual Regression**: Test UI consistency (where applicable)

### Test Quality
- **Deterministic**: Tests produce same results every run
- **Independent**: Tests don't depend on each other
- **Fast**: Unit tests run in milliseconds
- **Clear Failures**: Test names and errors clearly indicate what failed
- **Maintainable**: Tests are easy to update as code evolves

---

## Documentation Requirements

### Code Documentation
- **README**: Project overview, setup, and basic usage
- **API Docs**: Document all public interfaces
- **Inline Comments**: Explain complex algorithms and business logic
- **Architecture Docs**: High-level system design decisions

### Project Documentation
- **CHANGELOG**: Track all notable changes
- **CONTRIBUTING**: Guidelines for contributors (if open source)
- **LICENSE**: Clear licensing terms

---

## Deployment Standards

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No console.log or debugging code
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Backup procedures verified

### Monitoring
- **Error Tracking**: Log and monitor application errors
- **Performance Monitoring**: Track response times and resource usage
- **Security Monitoring**: Watch for suspicious activity

---

## Tool References

### Development Tools
- **dart-sass**: CSS compilation via Homebrew
- **UV**: Python package management with inline metadata
- **Git**: Version control with advanced workflow patterns

### Claude Skills Reference
When working with Claude on projects, reference these specialized skills:
- **css-specialist**: CSS/Sass architecture and modern features
- **python-expert**: Python best practices and patterns
- **web-security**: Security patterns across all stacks
- **wordpress-blocks**: Gutenberg block development
- **wordpress-themes**: WordPress theme development

---

## Continuous Improvement

These standards are living documents. Update them as:
- New patterns emerge from project work
- Tools and technologies evolve
- Better practices are discovered
- Team feedback identifies improvements

**Review Cadence**: Quarterly review of standards, update as needed
