# Claude Collaboration Guide

This file provides specific guidance for Claude (both Claude.ai and Claude Code) when working on this project.

**Project:** [Project Name]  
**Last Updated:** [Date]

---

## Project Context Summary

### In One Sentence
<!-- Extremely concise project description -->


### Key Objectives
1. 
2. 
3. 

### Success Metrics
<!-- How do we know if this project is successful? -->


---

## Claude Skills to Use

Reference these skills when working on this project:

- [ ] **css-specialist** - For CSS/Sass architecture and modern CSS features
- [ ] **python-expert** - For Python best practices and patterns  
- [ ] **web-security** - For security patterns across all stacks
- [ ] **wordpress-blocks** - For Gutenberg block development
- [ ] **wordpress-themes** - For WordPress theme development
- [ ] **Other:** ___________

### Primary Skill Focus
<!-- Which skill should Claude prioritize? -->


---

## Project-Specific Conventions

### Code Style Preferences
<!-- Any project-specific style rules beyond PROJECT_STANDARDS.md -->


### Naming Conventions
<!-- Specific naming patterns for this project -->
- Functions: 
- Variables: 
- Classes: 
- Files: 

### File Organization Rules
<!-- How should code be organized? -->


---

## Testing Approach for This Project

### Test Priority Order
1. [Most important to test first]
2. 
3. 

### Test Generation Rules
<!-- When should Claude automatically write tests? -->
- Always test: 
- Sometimes test: 
- Skip testing: 

### Edge Cases to Always Consider
<!-- Specific edge cases unique to this project -->
1. 
2. 
3. 

---

## Common Patterns in This Project

### Recurring Code Patterns
<!-- Patterns Claude should recognize and follow -->

**Pattern:** [Pattern name]
```javascript
// Example of the pattern
```

**When to use:**


**Pattern:** [Pattern name]
```javascript
// Example of the pattern
```

**When to use:**


---

## Known Gotchas & Pitfalls

### Technical Challenges
<!-- Things that are tricky in this project -->
1. **[Challenge]**
   - Why it's tricky: 
   - How to handle: 

2. **[Challenge]**
   - Why it's tricky: 
   - How to handle: 

### Anti-Patterns to Avoid
<!-- Things NOT to do in this project -->
- ❌ DON'T: 
  - WHY: 
  - DO INSTEAD: 

- ❌ DON'T: 
  - WHY: 
  - DO INSTEAD: 

---

## Dependencies & Constraints

### Required Libraries
<!-- Must use these -->
- 

### Prohibited Libraries
<!-- Don't use these -->
- 
  - Reason: 

### Browser/Platform Constraints
<!-- Specific compatibility requirements -->
- 

### Performance Constraints
<!-- Specific performance requirements -->
- 

---

## Code Review Criteria

When reviewing or generating code, check for:

### Functionality
- [ ] Meets requirements in PROJECT_CONFIG.md
- [ ] Handles edge cases listed in TEST_REQUIREMENTS.md
- [ ] Follows patterns in this guide
- [ ] No anti-patterns present

### Quality
- [ ] Follows PROJECT_STANDARDS.md
- [ ] Proper error handling
- [ ] Clear, descriptive naming
- [ ] Appropriate comments
- [ ] Modular and maintainable

### Security
- [ ] Input validation present
- [ ] Output properly escaped
- [ ] No security anti-patterns
- [ ] Follows security requirements in PROJECT_CONFIG.md

### Testing
- [ ] Appropriate tests included
- [ ] Tests cover edge cases
- [ ] Tests are deterministic
- [ ] Follows TEST_REQUIREMENTS.md

---

## Communication Preferences

### Question Priority
When Claude needs clarification:
1. First priority questions: [Security, architecture, requirements]
2. Can decide autonomously: [Style choices, implementation details]
3. Document and continue: [Minor details, assume standard practice]

### Response Style
- **Code comments**: [Verbose / Minimal / Only complex logic]
- **Explanations**: [Detailed / Brief / Only if asked]
- **Examples**: [Always / When helpful / Only if requested]

### Decision Making
<!-- How much autonomy should Claude have? -->
- Autonomous decisions: 
- Always ask first: 

---

## Development Workflow

### Before Starting Each Feature
1. Review PROJECT_CONFIG.md for requirements
2. Check TEST_REQUIREMENTS.md for test scenarios
3. Review this file for project-specific guidance
4. Confirm approach before implementing

### During Development
1. Follow patterns in this guide
2. Write tests as you go (if applicable)
3. Document complex decisions
4. Keep PROJECT_CONFIG.md updated

### Before Considering Feature Complete
1. All tests passing
2. Documentation updated
3. CHANGELOG.md updated
4. Code review checklist completed

---

## Context You Should Know

### Project History
<!-- Important background information -->


### Recent Changes
<!-- What's changed recently that affects future work -->


### Current Focus
<!-- What's being actively worked on -->


### Upcoming Plans
<!-- What's coming next -->


---

## Frequently Referenced

### Key Files
<!-- Files Claude will reference often -->
- 
- 

### External Resources
<!-- Documentation, APIs, references -->
- 
- 

### Related Projects
<!-- Other codebases to reference -->
- 

---

## Examples & Templates

### Example 1: [Common Task]
```javascript
// Example code showing how to do common task
```

### Example 2: [Another Common Task]
```javascript
// Example code
```

---

## Debugging Hints

### Common Issues
**Issue:** [Description]
- **Symptoms:** 
- **Cause:** 
- **Solution:** 

**Issue:** [Description]
- **Symptoms:** 
- **Cause:** 
- **Solution:** 

### Debug Commands
```bash
# Useful debugging commands
```

---

## Quick Reference

### Project Commands
```bash
# Start development
[command]

# Run tests
[command]

# Build for production
[command]

# Deploy
[command]
```

### Environment Setup
```bash
# One-time setup steps
```

---

## Update History

### Major Updates
- **[Date]**: [What changed and why]
- **[Date]**: [What changed and why]

---

## Notes from Previous Sessions

<!-- Keep notes from conversations with Claude that should inform future work -->

### Session [Date]
**Topic:**
**Key Decisions:**
**Learnings:**

### Session [Date]
**Topic:**
**Key Decisions:**
**Learnings:**

---

**Remember**: This file should evolve with the project. Update it whenever you discover new patterns, gotchas, or important context that would help future work!
