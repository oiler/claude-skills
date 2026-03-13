---
name: git-tagging
description: Manages semantic versioning, git tags, GitHub Releases, and CHANGELOG.md for any project. Use when user asks about version tracking, git tags, creating releases, semver, changelog, "how do I version my project", "create a release", "tag a version", or wants to establish v1.0/v2.0-style versioning in a GitHub repo. Always apply this skill for tasks involving git releases, version bumps, or changelog maintenance.
---

# Git Tagging & Release Management

Covers the practical versioning stack for GitHub projects: semantic versioning, annotated git tags, GitHub Releases, and CHANGELOG.md maintenance.

---

## The Recommended Stack

For most projects, use all four together:

1. **Semantic versioning** — numbering scheme
2. **Annotated git tags** — marks the commit in history
3. **GitHub Release** — human-readable notes + optional assets
4. **CHANGELOG.md** — single-file history in the repo

---

## Semantic Versioning (semver)

Format: `MAJOR.MINOR.PATCH`

| Bump | When |
|------|------|
| `MAJOR` (v2.0.0) | Breaking changes — existing users must update their code |
| `MINOR` (v1.1.0) | New features, backwards compatible |
| `PATCH` (v1.0.1) | Bug fixes only, no new features |

**Pre-release suffixes:** `v2.0.0-alpha.1`, `v2.0.0-rc1` (release candidate)

**Starting out:** Use `v0.x.x` until the public API is stable. `v0` signals "anything can change."

Full spec: https://semver.org/

---

## Git Tags

### Create an annotated tag (always prefer annotated over lightweight)

```bash
git tag -a v1.0.0 -m "Initial stable release"
```

Annotated tags store: tagger name, email, date, and message. Lightweight tags are just pointers with none of that context.

### Push tags to GitHub

```bash
# Push a specific tag
git push origin v1.0.0

# Push all local tags at once
git push --tags
```

### Tag a past commit

```bash
git log --oneline          # find the commit hash
git tag -a v1.0.0 abc1234 -m "Tagging past commit"
git push origin v1.0.0
```

### List, inspect, and delete

```bash
git tag                        # list all tags
git show v1.0.0                # inspect tag details + commit
git tag -d v1.0.0              # delete local tag
git push origin --delete v1.0.0  # delete remote tag
```

### Check out a tagged version

```bash
git checkout v1.0.0
```

---

## GitHub Releases

GitHub Releases build on top of tags — they add a title, Markdown release notes, and optional downloadable assets (binaries, zips, etc.).

### Via GitHub CLI (recommended)

```bash
# Create a release from an existing tag
gh release create v1.0.0 --title "v1.0.0" --notes "First stable release"

# Create tag + release in one step
gh release create v1.0.0 --title "v1.0.0" --notes-file CHANGELOG_FRAGMENT.md

# Mark as pre-release
gh release create v2.0.0-rc1 --prerelease --title "v2.0.0 Release Candidate"

# Attach binary assets
gh release create v1.0.0 dist/myapp-linux dist/myapp-macos
```

### Via GitHub UI

GitHub → Releases → "Draft a new release" → pick the tag (or create one) → write notes → Publish.

---

## CHANGELOG.md

Keep a `CHANGELOG.md` at the repo root. Use the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.1.0] - 2026-03-13
### Added
- New feature X
- Support for Y

### Changed
- Improved performance of Z

### Fixed
- Bug where A caused B

## [1.0.0] - 2026-01-15
### Added
- Initial release
```

**Sections to use:** `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`

**Workflow:** Maintain an `[Unreleased]` section at the top. When cutting a release, rename it to the version + date and open a new `[Unreleased]` block.

---

## Typical Release Workflow

```bash
# 1. Finalize and commit all changes
git add .
git commit -m "chore: prepare v1.1.0 release"

# 2. Update CHANGELOG.md — rename [Unreleased] to [1.1.0] - YYYY-MM-DD
#    (do this manually or with a tool like git-cliff or standard-version)

# 3. Create the annotated tag
git tag -a v1.1.0 -m "v1.1.0 — add feature X, fix bug Y"

# 4. Push commits and tag
git push origin main
git push origin v1.1.0

# 5. Create GitHub Release
gh release create v1.1.0 --title "v1.1.0" --notes-file CHANGELOG_FRAGMENT.md
```

---

## Automation (Optional)

For projects that want fully automated releases:

- **[git-cliff](https://git-cliff.org/)** — generates changelogs from conventional commits
- **[semantic-release](https://semantic-release.gitbook.io/)** — automates version bump + tag + release + changelog from commit messages
- **[standard-version](https://github.com/conventional-changelog/standard-version)** — simpler alternative to semantic-release
- **GitHub Actions** — trigger releases automatically on merge to main

These tools require [Conventional Commits](https://www.conventionalcommits.org/) format (`feat:`, `fix:`, `chore:`, etc.) to work properly.

---

## Quick Reference

| Goal | Command |
|------|---------|
| Create annotated tag | `git tag -a v1.0.0 -m "message"` |
| Push tag | `git push origin v1.0.0` |
| Push all tags | `git push --tags` |
| Create GitHub release | `gh release create v1.0.0 --title "..." --notes "..."` |
| List tags | `git tag` |
| Delete remote tag | `git push origin --delete v1.0.0` |
| Check out a tag | `git checkout v1.0.0` |
