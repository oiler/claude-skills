# Quick Start Checklist

Use this checklist when starting a new project with the boilerplate.

---

## Initial Setup

### 1. Copy Boilerplate Files
- [ ] Copy `PROJECT_STANDARDS.md` to project root
- [ ] Copy `PROJECT_CONFIG.md` to project root
- [ ] Copy `TEST_REQUIREMENTS.md` to project root
- [ ] Copy `project.yml` to project root
- [ ] Create basic folder structure (`src/`, `tests/`, `docs/`, `config/`)

### 2. Configure project.yml (Do This First!)
- [ ] Set project name and description
- [ ] Select project type
- [ ] Define primary and additional languages
- [ ] List frameworks and build tools
- [ ] Specify runtime versions (Node/Python/PHP)
- [ ] Set browser support targets
- [ ] Enable relevant test types
- [ ] Set coverage targets
- [ ] Define performance targets
- [ ] Specify WCAG level for accessibility

### 3. Complete PROJECT_CONFIG.md

#### Project Overview
- [ ] Check appropriate project type boxes
- [ ] Write 2-3 sentence purpose statement
- [ ] Define target audience
- [ ] List 3-5 success criteria

#### Technical Specifications
- [ ] Document technology stack
- [ ] List all dependencies (required and dev)
- [ ] Define file structure
- [ ] Specify runtime requirements

#### Features & Requirements
- [ ] List core features (must-haves)
- [ ] List optional features (nice-to-haves)
- [ ] Document known limitations
- [ ] Write user stories for primary use cases
- [ ] Identify edge cases

#### Security
- [ ] Define authentication/authorization needs
- [ ] List sensitive data types
- [ ] Check required security measures

#### Performance
- [ ] Set target metrics
- [ ] Prioritize optimization areas

#### Testing Strategy
- [ ] Describe test environment setup
- [ ] List critical test scenarios
- [ ] Define test data requirements
- [ ] Specify browser/platform testing needs

#### Accessibility
- [ ] Select WCAG compliance level
- [ ] Check specific accessibility needs

#### Integration Points
- [ ] Document external services
- [ ] Document internal systems

#### Deployment
- [ ] Configure development environment
- [ ] Configure staging environment
- [ ] Configure production environment
- [ ] List required environment variables
- [ ] Document build/test/deploy commands

#### Timeline
- [ ] Define project milestones
- [ ] Identify dependencies and blockers

#### Claude Collaboration
- [ ] Select relevant Claude skills
- [ ] Add project-specific guidance

### 4. Customize TEST_REQUIREMENTS.md

#### Test Philosophy
- [ ] Define testing goals
- [ ] Perform risk assessment (high/medium/low risk areas)

#### Unit Tests
- [ ] Set coverage requirements
- [ ] Document test conditions for key functions

#### Integration Tests
- [ ] Define integration points to test
- [ ] Specify integration scenarios

#### End-to-End Tests
- [ ] Write user stories in Given/When/Then format
- [ ] Document critical user journeys

#### Visual Regression (if applicable)
- [ ] Define scope of visual testing
- [ ] List viewport sizes and test conditions

#### Performance Tests
- [ ] Define metrics to track
- [ ] Specify load testing scenarios

#### Security Tests
- [ ] Check attack vectors to test
- [ ] Document security test cases

#### Accessibility Tests
- [ ] List WCAG compliance checks
- [ ] Define manual test scenarios

#### Test Data
- [ ] Document test data requirements
- [ ] Define test data sources
- [ ] Specify test data reset strategy

#### Test Environment
- [ ] Document prerequisites
- [ ] Add configuration details
- [ ] Specify fixture/mock locations

---

## During Development

### For Each New Feature
- [ ] Update PROJECT_CONFIG.md with feature details
- [ ] Add test scenarios to TEST_REQUIREMENTS.md
- [ ] Document in CHANGELOG.md
- [ ] Add user story if applicable

### For Each Bug Fix
- [ ] Document in CHANGELOG.md
- [ ] Add regression test to TEST_REQUIREMENTS.md
- [ ] Update known issues if applicable

### Regular Maintenance
- [ ] Keep project.yml in sync with package.json/requirements.txt
- [ ] Update test coverage statistics
- [ ] Review and update documentation

---

## Before First Claude Session

### Prepare Context
- [ ] All configuration files are complete
- [ ] Test requirements are documented
- [ ] Project boundaries are clear
- [ ] Success criteria are defined

### Claude Prompt Template
```
I'm starting a new project. Please review these files to understand 
the project requirements:

1. PROJECT_CONFIG.md - for project specifics
2. TEST_REQUIREMENTS.md - for testing strategy
3. project.yml - for structured metadata
4. PROJECT_STANDARDS.md - for coding standards

Key focus areas:
- [List 2-3 main focus areas]

Please confirm you've reviewed these files and understand the project 
objectives before we begin.
```

---

## Pre-Deployment Checklist

### Documentation
- [ ] All config files are current
- [ ] README.md is complete
- [ ] CHANGELOG.md is updated
- [ ] API documentation is current (if applicable)

### Code Quality
- [ ] All tests passing
- [ ] Coverage targets met
- [ ] No debugging code (console.log, etc.)
- [ ] Code reviewed
- [ ] Security scan passed

### Deployment
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Backup procedures verified
- [ ] Monitoring configured
- [ ] Error tracking enabled

---

## Monthly Review

### Documentation Health Check
- [ ] Are all docs current with code?
- [ ] Are test requirements up to date?
- [ ] Is project.yml in sync?
- [ ] Are milestones accurate?

### Standards Review
- [ ] Are we following PROJECT_STANDARDS.md?
- [ ] Any new patterns to document?
- [ ] Any standards to update?
- [ ] Any learnings to capture?

### Testing Review
- [ ] Coverage meeting targets?
- [ ] Any flaky tests to fix?
- [ ] Any new test types needed?
- [ ] Test execution time acceptable?

---

## Quarterly Deep Review

### Process Improvement
- [ ] Review PROJECT_STANDARDS.md for updates
- [ ] Identify technical debt
- [ ] Plan improvements
- [ ] Update boilerplate templates based on learnings

### Performance Audit
- [ ] Verify performance targets are being met
- [ ] Identify optimization opportunities
- [ ] Update performance targets if needed

### Security Audit
- [ ] Review security measures
- [ ] Check for vulnerabilities
- [ ] Update dependencies
- [ ] Review access controls

---

## Tips for Success

### Do First
1. Fill out project.yml completely (drives everything else)
2. Write clear purpose statement and success criteria
3. Define user stories with concrete examples
4. Identify high-risk areas for testing

### Common Mistakes to Avoid
- Starting to code before completing configuration
- Leaving placeholder text in templates
- Skipping test requirements documentation
- Not updating docs as project evolves
- Forgetting to specify project type

### Best Practices
- Be specific and concrete in requirements
- Include examples in user stories
- Document decisions as you make them
- Keep project.yml in sync with reality
- Reference docs in Claude prompts
- Review and update regularly

---

**Pro Tip**: Print this checklist and keep it handy when starting new projects!
