# CLAUDE.md Template

Quick reference template for Claude collaboration on small to mid-size projects.

---

## Basic Information

**Project:** [Project Name]  
**Type:** [ ] WordPress Theme  [ ] WordPress Plugin  [ ] Vanilla JS App  [ ] Python Script  [ ] Other: _____  
**Purpose:** [One sentence description]  
**Status:** [ ] Planning  [ ] Active Development  [ ] Maintenance

---

## Tech Stack

**Primary:**
- 

**Build Tools:**
- 

**Runtime:**
- Node: [version] (if applicable)
- Python: [version] (if applicable)
- PHP: [version] (if applicable)

**Browser Support:**
- Chrome/Edge >= 90, Firefox >= 88, Safari >= 14

---

## Code Standards

### [Language/Framework]
- 
- 
- 

### Security (Required)
- ✓ Sanitize all user input before storage
- ✓ Escape all output (context-appropriate)
- ✓ Use prepared statements for database queries
- ✓ Verify authentication/authorization
- ✓ No secrets in code (use environment variables)

### Style
- Indentation: [2 or 4 spaces]
- Max line length: [80-100 characters]
- Naming: [conventions]
- Comments: Explain "why" not "what"

### Git
- Atomic commits with clear messages
- Convention: `type: description` (feat, fix, docs, refactor, test)
- Interactive rebase for clean history

---

## Project Structure

```
project-root/
├── src/                # Source code
├── tests/             # Test files
└── [other folders]
```

[Customize based on project type - see examples below]

---

## Key Patterns & Conventions

### [Pattern Name]
```[language]
// Example code
```

### [Another Pattern]
```[language]
// Example code
```

---

## Testing Requirements

**Priority Areas:**
1. [High-risk feature requiring extensive testing]
2. [Security-critical functionality]
3. [Core business logic]

**Test Types Enabled:**
- [ ] Unit tests (target: [percentage]%)
- [ ] Integration tests
- [ ] Security tests (always required)
- [ ] Other: _____

**Critical Test Scenarios:**
1. [Scenario that must work correctly]
2. [Edge case to handle]
3. [Error condition to test]

---

## Development Commands

```bash
# Start development
[command]

# Run tests
[command]

# Build for production
[command]
```

---

## Environment Setup

**Required:**
- 

**Configuration:**
```bash
# Environment variables needed
VAR_NAME=description
```

---

## Security Checklist

- [ ] Input validation on all user data
- [ ] Output escaping (HTML, attributes, URLs, JS)
- [ ] SQL injection prevention (prepared statements)
- [ ] CSRF protection (nonces/tokens)
- [ ] XSS prevention
- [ ] Authentication/authorization checks
- [ ] Rate limiting (if applicable)
- [ ] Secure file uploads (if applicable)

---

## Common Gotchas

**Issue:** [Common problem]
- Solution: [How to handle it]

**Issue:** [Another common problem]
- Solution: [How to handle it]

---

## Claude Instructions

### Skills to Use
- [ ] css-specialist
- [ ] python-expert
- [ ] web-security
- [ ] wordpress-blocks
- [ ] wordpress-themes

### Testing Approach
- Write tests for: [areas requiring tests]
- Test automatically: [when to auto-generate tests]
- Skip testing: [areas that don't need tests]

### Code Generation Preferences
- Comment level: [ ] Verbose [ ] Minimal [ ] Only complex logic
- Explanation style: [ ] Detailed [ ] Brief [ ] Only if asked
- Pattern to follow: [any project-specific patterns]

---

## Quick Reference

### Key Files
- 
- 

### External Resources
- 

### Text Domain / Namespace
- [if applicable]

---

## Notes & Decisions

[Document important decisions and context here]

