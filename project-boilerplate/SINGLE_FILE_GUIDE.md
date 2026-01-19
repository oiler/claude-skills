# CLAUDE.md Single-File Format

## Overview

For small to mid-size projects, use a **single `CLAUDE.md` file** instead of the full boilerplate suite. This condensed format provides all essential information Claude needs in one place, making it quick to set up and easy to maintain.

---

## When to Use What

### Use Single CLAUDE.md File For:
- ✓ Small projects (1-3 developers, <10,000 lines of code)
- ✓ Personal projects or internal tools
- ✓ Projects with straightforward requirements
- ✓ Quick prototypes or MVPs
- ✓ Single-technology projects (one language/framework)

### Use Full Boilerplate Suite For:
- ✓ Large, complex projects (multiple teams, >10,000 lines)
- ✓ Projects with extensive testing requirements
- ✓ Long-term maintained applications
- ✓ Projects requiring detailed documentation
- ✓ Multi-technology stacks with complex integration

---

## Quick Start

### 1. Copy Template
```bash
cp CLAUDE.md /path/to/your-project/
```

### 2. Fill Out Sections (15 minutes)
- Basic Information (project type, purpose)
- Tech Stack (languages, tools, runtime)
- Code Standards (conventions specific to your project)
- Project Structure (folder organization)
- Key Patterns (code examples to follow)
- Testing Requirements (what needs testing)
- Development Commands (how to run/build/test)
- Security Checklist (applicable security measures)

### 3. Reference in Claude Sessions
```
"Review CLAUDE.md before we start. Focus on [specific aspect]."
```

---

## Template Structure

The `CLAUDE.md` template has these sections:

### Essential Sections (Always Complete)
1. **Basic Information** - Project type, purpose, status
2. **Tech Stack** - Languages, frameworks, tools, versions
3. **Code Standards** - Style, conventions, security
4. **Project Structure** - Folder organization
5. **Security Checklist** - Applicable security measures

### Important Sections (Complete If Applicable)
6. **Key Patterns & Conventions** - Code examples to follow
7. **Testing Requirements** - What and how to test
8. **Development Commands** - Run, build, test commands
9. **Common Gotchas** - Known issues and solutions

### Optional Sections (Add As Needed)
10. **Claude Instructions** - How Claude should work on this project
11. **Quick Reference** - Frequently used info
12. **Notes & Decisions** - Context and history

---

## Included Examples

We've provided three complete examples showing how to fill out `CLAUDE.md` for different project types:

### 1. WordPress Theme (`example-wordpress-theme.md`)
- Custom post types and taxonomies
- Gutenberg block development
- VIP-compliant code patterns
- Sass compilation workflow
- Server-side block rendering

**Use this example for:**
- WordPress custom themes
- WordPress plugins with custom post types
- Projects using ACF or block development

### 2. Vanilla JavaScript App (`example-vanilla-js.md`)
- Client-side file processing
- ES6 modules and functional patterns
- No build bundler (keeping it simple)
- Browser-based data conversion
- Sass for styling

**Use this example for:**
- Browser-based tools and utilities
- Data processing applications
- Projects avoiding framework overhead
- Client-side only apps

### 3. Python Automation Script (`example-python-script.md`)
- UV for dependency management (inline metadata)
- Web scraping with BeautifulSoup
- RSS feed generation
- Error handling and retries
- Standalone script (no virtual env needed)

**Use this example for:**
- Python automation scripts
- Web scraping projects
- Data processing pipelines
- Scheduled/cron jobs

---

## Customization Tips

### Start from an Example
1. Find the example closest to your project type
2. Copy it to your project as `CLAUDE.md`
3. Search and replace project-specific names
4. Modify sections that differ from the example
5. Remove sections that don't apply

### Project Structure Section
- Use a text tree to show folder hierarchy
- Comment important files/folders
- Show 2-3 levels deep (don't overdo it)
- Indicate what's git-ignored

### Key Patterns Section
- Include 2-5 code examples
- Show patterns you want Claude to follow
- Include common functions or components
- Comment complex parts

### Testing Requirements
- List 3-5 critical test scenarios
- Identify high-risk areas
- Set coverage targets if you have them
- Specify which test types to use

### Security Checklist
- Check applicable items for your project
- Add project-specific security concerns
- Include validation/sanitization rules
- Note sensitive data handling

---

## Integration with Claude

### In Claude.ai
At the start of your conversation:
```
"I'm working on [project]. Please review CLAUDE.md to understand 
the project requirements and coding standards."
```

### In Claude Code (Terminal)
```bash
# Navigate to project
cd /path/to/your-project

# Start Claude Code
claude-code

# First message
"Review CLAUDE.md and let's work on [feature]."
```

### For Specific Tasks
```
"Following the patterns in CLAUDE.md, create a new [component/function/module] 
that [does X]. Include tests as specified in the testing requirements."
```

---

## Maintenance

### When to Update CLAUDE.md

**After Adding Features:**
- Add new patterns to "Key Patterns" section
- Update test scenarios
- Document any gotchas discovered

**After Technology Changes:**
- Update Tech Stack section
- Modify Code Standards if conventions change
- Update Development Commands

**When You Learn Something:**
- Add to Common Gotchas section
- Update Notes & Decisions
- Refine patterns based on experience

**Before Handoff:**
- Ensure all sections are current
- Verify commands work
- Check that patterns reflect actual code

### Keep It Current
- Review monthly for active projects
- Update before bringing on new developers
- Revise when project direction changes
- Document major decisions

---

## Comparison: Single File vs. Full Suite

| Aspect | CLAUDE.md (Single File) | Full Boilerplate Suite |
|--------|------------------------|------------------------|
| **Setup Time** | 15-30 minutes | 1-2 hours |
| **Maintenance** | Quick updates | Detailed tracking |
| **Best For** | Small-mid projects | Large/complex projects |
| **Files** | 1 file (~200-400 lines) | 11 files (2,700+ lines) |
| **Testing Docs** | Basic requirements | Comprehensive strategy |
| **Standards** | Project-specific | Universal + project-specific |
| **Examples** | Inline patterns | Separate documentation |
| **Version Control** | Easy to track changes | Multiple files to sync |
| **Onboarding** | Single file to read | More complete but longer |

---

## Tips for Success

### Do:
- ✓ Fill out the template before coding
- ✓ Include real code examples in Key Patterns
- ✓ Be specific about security requirements
- ✓ Update as the project evolves
- ✓ Reference it in Claude prompts
- ✓ Use one of the examples as a starting point

### Don't:
- ✗ Leave placeholder text
- ✗ Copy examples without customizing
- ✗ Over-document (keep it concise)
- ✗ Skip the security checklist
- ✗ Forget to update commands/paths
- ✗ Make it longer than needed (aim for <400 lines)

### Pro Tips:
- **Keep it scannable** - Use headers, checkboxes, code blocks
- **Show, don't tell** - Include code examples over descriptions
- **Be specific** - "Use BEM naming" not "use good class names"
- **Document decisions** - Note "why" not just "what"
- **Update inline** - When you discover a gotcha, add it immediately

---

## Evolution Path

### Start Simple
- Begin with `CLAUDE.md` for new projects
- Keep it minimal and focused

### Grow as Needed
- Add sections as project complexity grows
- Document patterns as they emerge
- Expand testing requirements

### Migrate If Needed
- If project grows large, migrate to full boilerplate
- Use `CLAUDE.md` content to populate detailed templates
- Keep both for different project types

---

## File Size Guidelines

### Target Size
- **Small projects:** 150-250 lines
- **Mid-size projects:** 250-400 lines
- **If over 500 lines:** Consider full boilerplate suite

### What to Include
- Essential: Sections 1-5 (Basic info through Security)
- Important: Sections 6-9 (Patterns through Gotchas)
- Optional: Section 10-12 (Claude instructions, reference, notes)

### What to Keep Short
- Basic Information: 10-20 lines
- Tech Stack: 15-30 lines
- Security Checklist: 10-20 items checked
- Notes section: Only key decisions

---

## Getting Started Checklist

- [ ] Copy `CLAUDE.md` or an example to your project
- [ ] Fill out Basic Information section
- [ ] Complete Tech Stack section
- [ ] Define Code Standards relevant to your project
- [ ] Show Project Structure (text tree)
- [ ] Add 2-5 Key Patterns with code examples
- [ ] List 3-5 Critical Test Scenarios
- [ ] Document Development Commands
- [ ] Complete Security Checklist
- [ ] Add Common Gotchas (if known)
- [ ] Customize Claude Instructions
- [ ] Test commands actually work
- [ ] Commit to version control

---

## Questions & Troubleshooting

**Q: How detailed should Key Patterns be?**
A: Include 2-5 complete, working code examples. Show enough that Claude can replicate the pattern, but not every function in your codebase.

**Q: What if my project doesn't fit the examples?**
A: Start with the closest example and heavily modify it. The template is flexible - adapt it to your needs.

**Q: Should I include actual file paths or generic ones?**
A: Use actual file paths from your project. Makes it easier for Claude to reference specific files.

**Q: How often should I update CLAUDE.md?**
A: Update when you add features, discover gotchas, or change patterns. Quick review monthly for active projects.

**Q: Can I use this with the full boilerplate?**
A: Yes! You can have both. Use `CLAUDE.md` for quick reference and link to detailed docs in the full suite.

---

## Summary

The `CLAUDE.md` single-file format is perfect for small to mid-size projects that need:
- Quick setup (15-30 minutes)
- Essential project context for Claude
- Easy maintenance and updates
- Version control simplicity

Use the included examples as starting points, customize to your project, and keep it updated as you work. Reference it at the start of Claude sessions to provide rich context without overwhelming complexity.

**Remember:** Good documentation is documentation you'll actually maintain. Start simple, grow as needed.
