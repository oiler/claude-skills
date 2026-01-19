# Oiler Project Documentation System - Complete Guide

Two approaches for documenting projects for effective Claude collaboration.

---

## Choose Your Approach

### Option 1: Single CLAUDE.md File (Recommended for Most)
**Best for:** Small to mid-size projects (1-3 developers, <10k lines of code)

**What you get:**
- One `CLAUDE.md` file (~200-400 lines)
- 15-30 minute setup
- Easy to maintain and update
- Essential project context for Claude
- Three complete examples to start from

**Files:**
- `CLAUDE.md` (template)
- `example-wordpress-theme.md`
- `example-vanilla-js.md`
- `example-python-script.md`
- `SINGLE_FILE_GUIDE.md` (how to use it)

### Option 2: Full Boilerplate Suite
**Best for:** Large, complex projects (multiple teams, >10k lines of code)

**What you get:**
- 11 comprehensive documentation files
- 1-2 hour setup
- Detailed testing strategy
- Complete project lifecycle coverage
- Universal standards + project-specific configs

**Files:**
- `PROJECT_STANDARDS.md` - Universal standards
- `PROJECT_CONFIG.md` - Project specifications
- `TEST_REQUIREMENTS.md` - Testing framework
- `project.yml` - Machine-readable metadata
- `CLAUDE_GUIDE.md` - Claude collaboration notes
- Plus supporting docs, checklists, examples

---

## Quick Decision Matrix

| If your project... | Use... |
|-------------------|--------|
| Is a personal tool or small app | **Single CLAUDE.md** |
| Has 1-3 developers | **Single CLAUDE.md** |
| Is under 10,000 lines of code | **Single CLAUDE.md** |
| Uses one primary language/framework | **Single CLAUDE.md** |
| Is a quick prototype or MVP | **Single CLAUDE.md** |
| Has simple, straightforward requirements | **Single CLAUDE.md** |
| Involves multiple teams | **Full Boilerplate** |
| Is over 10,000 lines of code | **Full Boilerplate** |
| Requires extensive testing documentation | **Full Boilerplate** |
| Has complex integration requirements | **Full Boilerplate** |
| Needs detailed lifecycle tracking | **Full Boilerplate** |
| Is mission-critical or enterprise-level | **Full Boilerplate** |

**When in doubt:** Start with Single CLAUDE.md. You can always migrate to the full suite later.

---

## Getting Started with Single CLAUDE.md

### 1. Pick Your Example
- **WordPress Theme?** → Use `example-wordpress-theme.md`
- **JavaScript App?** → Use `example-vanilla-js.md`
- **Python Script?** → Use `example-python-script.md`
- **Other?** → Use base `CLAUDE.md` template

### 2. Copy and Customize (15 minutes)
```bash
# Copy example to your project
cp example-wordpress-theme.md /path/to/your-project/CLAUDE.md

# Edit the file
# - Update project name and purpose
# - Modify tech stack
# - Adjust code patterns
# - Update file structure
# - Add your specific requirements
```

### 3. Start Working with Claude
```
"Review CLAUDE.md and let's build [feature]. Follow the patterns shown."
```

**That's it!** You're ready to work with Claude on your project.

---

## Getting Started with Full Boilerplate

### 1. Copy All Files
```bash
# Copy entire boilerplate to your project
cp oiler-boilerplate/* /path/to/your-project/
```

### 2. Follow QUICKSTART.md Checklist (1-2 hours)
- Fill out `project.yml` first (drives everything else)
- Complete `PROJECT_CONFIG.md` sections
- Customize `TEST_REQUIREMENTS.md`
- Review `PROJECT_STANDARDS.md`
- Update `CLAUDE_GUIDE.md` with project specifics

### 3. Reference in Claude Sessions
```
"Review PROJECT_CONFIG.md, TEST_REQUIREMENTS.md, and CLAUDE_GUIDE.md. 
The project is [brief description]. Let's start with [task]."
```

---

## What's Included in Package

### Single File Format (4 files)
```
CLAUDE.md                    # Blank template
example-wordpress-theme.md   # Complete WordPress example
example-vanilla-js.md       # Complete JavaScript example  
example-python-script.md    # Complete Python example
SINGLE_FILE_GUIDE.md        # How to use single-file format
```

### Full Boilerplate Suite (11 files)
```
PROJECT_STANDARDS.md         # Universal coding standards
PROJECT_CONFIG.md            # Project specification template
TEST_REQUIREMENTS.md         # Testing strategy template
project.yml                  # Machine-readable metadata
CLAUDE_GUIDE.md             # Claude collaboration template
README.md                    # How to use the boilerplate
QUICKSTART.md               # Step-by-step checklist
DIRECTORY_STRUCTURE.md      # Folder organization guide
CHANGELOG.md                # Version tracking template
PACKAGE_SUMMARY.md          # Overview of everything
.gitignore                  # Standard ignore patterns
```

---

## Key Features

### Single CLAUDE.md Approach

✓ **Fast Setup** - 15-30 minutes to complete  
✓ **One File** - Easy to maintain and version control  
✓ **Essential Context** - Everything Claude needs in one place  
✓ **Proven Examples** - Three complete real-world examples  
✓ **Flexible** - Adapt template to any project type  
✓ **Lightweight** - Perfect for small teams and personal projects  

### Full Boilerplate Approach

✓ **Comprehensive** - Complete project lifecycle coverage  
✓ **Structured** - Separate concerns into logical files  
✓ **Universal Standards** - Consistent across all projects  
✓ **Testing Framework** - Detailed strategy for quality  
✓ **Machine-Readable** - YAML file for tooling integration  
✓ **Scalable** - Grows with project complexity  

---

## Common Use Cases

### Single CLAUDE.md Perfect For:

**WordPress Custom Theme**
- Custom post types and Gutenberg blocks
- VIP-compliant code patterns
- Sass compilation workflow
- See: `example-wordpress-theme.md`

**Vanilla JavaScript Tool**
- Browser-based utilities
- Data processing apps
- Client-side only applications
- See: `example-vanilla-js.md`

**Python Automation Script**
- Web scraping tools
- RSS feed generators
- Data processing pipelines
- See: `example-python-script.md`

### Full Boilerplate Perfect For:

**Enterprise Applications**
- Multi-team development
- Long-term maintenance requirements
- Complex testing needs

**Multi-Technology Projects**
- Multiple languages/frameworks
- Complex integrations
- Extensive documentation needs

**Mission-Critical Systems**
- High security requirements
- Detailed audit trails
- Comprehensive testing strategies

---

## Integration with Your Workflow

### With Claude.ai (Web Interface)
Start your conversation:
```
"I'm working on [project name]. Please review CLAUDE.md 
(or PROJECT_CONFIG.md and TEST_REQUIREMENTS.md) to understand 
the project before we begin."
```

### With Claude Code (Terminal)
```bash
cd /path/to/your-project
claude-code

# First prompt:
"Review CLAUDE.md and let's work on [task]."
```

### With API Integration
Include relevant documentation content in your system prompt or as context to guide Claude's responses.

---

## Your Existing Skills Integration

Both documentation approaches reference and complement your existing Claude Skills:

**CSS/Sass Projects:**
- Reference: `css-specialist` skill
- Standards: Semantic naming, shallow nesting, modular structure

**WordPress Projects:**
- Reference: `wordpress-themes` and `wordpress-blocks` skills
- Standards: VIP compliance, modular functions, security practices

**Python Projects:**
- Reference: `python-expert` skill
- Standards: PEP 8, type hints, UV for dependencies

**All Projects:**
- Reference: `web-security` skill
- Standards: Input validation, output escaping, secure queries

---

## Migration Path

### Start Small, Grow as Needed

**Phase 1: Single File** (New project)
- Use `CLAUDE.md` for initial development
- Quick setup, easy to maintain
- Perfect for getting started

**Phase 2: Add Detail** (Project grows)
- Expand sections in `CLAUDE.md`
- Add more patterns and examples
- Document more edge cases

**Phase 3: Consider Full Suite** (Project gets complex)
- When `CLAUDE.md` exceeds 500 lines
- When you need separate testing documentation
- When multiple developers need onboarding
- Migrate content from `CLAUDE.md` to full boilerplate templates

### Can Use Both
- Keep `CLAUDE.md` for quick reference
- Use full boilerplate for comprehensive docs
- Link between them as needed

---

## Best Practices

### For Both Approaches:

**Do:**
- ✓ Fill out templates before coding
- ✓ Include real code examples
- ✓ Update as project evolves
- ✓ Reference in Claude prompts
- ✓ Version control all documentation
- ✓ Review and update regularly

**Don't:**
- ✗ Leave placeholder text
- ✗ Skip security sections
- ✗ Forget to update after changes
- ✗ Over-document (keep it practical)
- ✗ Ignore testing requirements

---

## Success Metrics

You'll know your documentation is working when:

✓ New Claude sessions start faster (less clarification needed)  
✓ Claude generates code matching your patterns  
✓ Tests are comprehensive and catch bugs  
✓ Onboarding new developers is easier  
✓ Code quality is consistent across features  
✓ Security practices are followed automatically  
✓ You can return to projects after time away  

---

## File Organization in Your Projects

### With Single CLAUDE.md:
```
your-project/
├── CLAUDE.md              # All project context
├── src/                   # Your source code
├── tests/                 # Your tests
├── README.md             # User-facing documentation
└── CHANGELOG.md          # Version history
```

### With Full Boilerplate:
```
your-project/
├── PROJECT_STANDARDS.md   # Universal standards
├── PROJECT_CONFIG.md      # Project specifics
├── TEST_REQUIREMENTS.md   # Testing strategy
├── project.yml           # Metadata
├── CLAUDE_GUIDE.md       # Claude collaboration
├── README.md             # User documentation
├── CHANGELOG.md          # Version history
├── src/                  # Your source code
├── tests/                # Your tests
├── docs/                 # Additional documentation
└── config/               # Configuration files
```

---

## Next Steps

### Immediate Actions:

1. **Choose your approach** based on project size and complexity
2. **Copy appropriate files** to your next project
3. **Fill out templates** (15 min for single file, 1-2 hrs for full suite)
4. **Try a Claude session** with the documentation
5. **Refine based on experience**

### Short Term:

1. Use on 2-3 projects to establish habits
2. Note what works and what doesn't
3. Refine templates based on real usage
4. Build library of completed examples

### Long Term:

1. Evolve documentation as your practices improve
2. Share learnings across projects
3. Update standards quarterly
4. Consider creating project-type-specific variations

---

## Support

### Questions About Single CLAUDE.md?
- Read `SINGLE_FILE_GUIDE.md` for detailed instructions
- Review the three examples for inspiration
- Start with the example closest to your project type

### Questions About Full Boilerplate?
- Read `README.md` for comprehensive overview
- Follow `QUICKSTART.md` checklist
- Review `PACKAGE_SUMMARY.md` for file details

### General Questions?
- Both approaches are flexible - adapt to your needs
- Start simple, add complexity only when needed
- Update based on real project experience
- Document what actually helps, discard what doesn't

---

## Philosophy

Both documentation approaches embody your development principles:

**Clean, Maintainable Code**
- Standards over convenience
- Modular, single-purpose components
- Self-documenting structure

**Security First**
- Built-in security checklists
- Input validation and output escaping
- Safe by default patterns

**Test Everything**
- Clear testing requirements
- Comprehensive coverage goals
- Deterministic, repeatable tests

**Document As You Go**
- Living documentation that evolves
- Capture decisions and context
- Easy to update and maintain

**Minimal Maintenance**
- Design for long-term stability
- Reduce future friction
- Build once, run forever

---

## Summary

You now have two powerful tools for documenting projects:

**Single CLAUDE.md** for most projects:
- Fast, lightweight, easy to maintain
- Perfect for small-mid size projects
- Three complete examples to start from

**Full Boilerplate Suite** for complex projects:
- Comprehensive, structured, scalable
- Detailed testing and standards
- Complete project lifecycle coverage

Both approaches enable effective collaboration with Claude by providing the context needed to generate high-quality, consistent code that follows your patterns and standards.

**Choose based on your project needs, start simple, and evolve as needed.**

---

**Version:** 1.0  
**Created:** January 19, 2026  
**For:** oiler
