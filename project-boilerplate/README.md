# Oiler Project Boilerplate

A comprehensive, Claude-optimized project foundation for building robust, maintainable web applications.

## Purpose

This boilerplate provides a structured starting point for all Oiler projects, with:
- Universal coding standards and best practices
- Project-specific configuration templates
- Comprehensive testing strategy framework
- Machine-readable metadata for Claude Code integration
- Clear boundaries, objectives, and requirements documentation

## What's Included

### Core Documentation Files

1. **`PROJECT_STANDARDS.md`** - Universal standards for all projects
   - Code quality principles
   - Security standards
   - Performance guidelines
   - Git workflow
   - Testing philosophy
   - Documentation requirements

2. **`PROJECT_CONFIG.md`** - Project-specific configuration
   - Project overview and purpose
   - Technical specifications
   - Features and requirements
   - User stories and use cases
   - Security considerations
   - Testing strategy
   - Deployment configuration
   - Timeline and milestones

3. **`TEST_REQUIREMENTS.md`** - Comprehensive testing framework
   - Test types and coverage goals
   - Unit, integration, E2E test scenarios
   - Visual regression and performance tests
   - Security and accessibility testing
   - Test data management
   - Execution and maintenance plans
   - Claude test generation guidelines

4. **`project.yml`** - Machine-readable project metadata
   - Structured data for tooling and automation
   - Easy parsing by Claude and other tools
   - Single source of truth for project configuration

## How to Use This Boilerplate

### Starting a New Project

1. **Copy boilerplate files to your project root:**
   ```bash
   cp PROJECT_STANDARDS.md /path/to/your-project/
   cp PROJECT_CONFIG.md /path/to/your-project/
   cp TEST_REQUIREMENTS.md /path/to/your-project/
   cp project.yml /path/to/your-project/
   ```

2. **Fill out `project.yml` first:**
   - Set basic project metadata
   - Define project type
   - List technologies and dependencies
   - Enable relevant test types
   - This file drives other configurations

3. **Complete `PROJECT_CONFIG.md`:**
   - Check relevant project type boxes
   - Write purpose statement and success criteria
   - Define features and user stories
   - Document security and performance requirements
   - Add project-specific details

4. **Customize `TEST_REQUIREMENTS.md`:**
   - Define testing goals for this project
   - Identify high-risk areas needing extensive testing
   - Specify critical test scenarios
   - Add project-specific test considerations
   - Document any known testing challenges

5. **Review `PROJECT_STANDARDS.md`:**
   - Read through to ensure understanding
   - Note which standards apply to your project type
   - Reference throughout development
   - Update if you discover better practices

### Working with Claude

When starting work with Claude Code or in Claude.ai:

1. **Reference these files in your prompts:**
   ```
   "Review PROJECT_CONFIG.md and TEST_REQUIREMENTS.md before starting.
   Follow standards in PROJECT_STANDARDS.md."
   ```

2. **Claude will use these files to:**
   - Understand project context and boundaries
   - Generate appropriate code structure
   - Write comprehensive tests automatically
   - Follow your specific requirements
   - Maintain consistency across sessions

3. **Update files as project evolves:**
   - Keep configurations current
   - Document decisions in PROJECT_CONFIG.md
   - Update test requirements as needed
   - Reflect learnings in PROJECT_STANDARDS.md

## File Structure in Your Project

```
your-project/
├── PROJECT_STANDARDS.md     # Universal standards (rarely changes)
├── PROJECT_CONFIG.md        # Project specifics (update as needed)
├── TEST_REQUIREMENTS.md     # Testing strategy (update with new features)
├── project.yml             # Structured metadata (keep in sync)
├── README.md               # Project README (create separately)
├── CHANGELOG.md            # Track changes (maintain regularly)
├── src/                    # Your source code
├── tests/                  # Your tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                   # Additional documentation
└── config/                 # Configuration files
```

## Key Benefits

### For You
- **Clear Boundaries**: Define exactly what the project should and shouldn't do
- **Comprehensive Planning**: Think through requirements before coding
- **Consistent Quality**: Universal standards across all projects
- **Easy Onboarding**: New developers (or future you) understand project quickly
- **Reduced Decisions**: Many choices already made in standards

### For Claude
- **Rich Context**: Complete understanding of project goals and constraints
- **Automatic Testing**: Generate tests based on your requirements
- **Consistency**: Follow your patterns and preferences
- **Better Code**: Understand what good code looks like for your projects
- **Reduced Back-and-Forth**: Less need for clarification questions

## Best Practices

### Do:
- ✓ Fill out templates thoroughly before coding
- ✓ Update files as requirements change
- ✓ Reference files in Claude prompts
- ✓ Keep project.yml in sync with other docs
- ✓ Review standards periodically
- ✓ Document decisions and learnings

### Don't:
- ✗ Leave templates blank or with placeholder text
- ✗ Let documentation drift from reality
- ✗ Skip test requirements documentation
- ✗ Forget to specify project type
- ✗ Ignore security considerations
- ✗ Rush through the planning phase

## Maintenance

### Regular Updates
- **After each feature**: Update PROJECT_CONFIG.md with new features
- **After major changes**: Review and update TEST_REQUIREMENTS.md
- **Quarterly**: Review PROJECT_STANDARDS.md for improvements
- **Before deployment**: Verify all docs are current

### Version Control
- Commit documentation changes with code changes
- Tag releases in CHANGELOG.md
- Keep project.yml version in sync with project version

## Examples

See `/examples` directory (to be created) for completed templates from:
- Vanilla JavaScript applications
- WordPress themes and plugins
- Python automation scripts

## Contributing to Boilerplate

As you work on projects and discover better patterns:

1. Update your PROJECT_STANDARDS.md
2. Document what worked and what didn't
3. Refine templates based on real usage
4. Share learnings across projects

## Questions?

If something in the boilerplate is unclear or could be improved:
- Add clarifying comments in your project's version
- Note improvements for future projects
- Update the boilerplate repository

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Maintained by:** Oiler
