# Package this plugin as a portable .plugin bundle — a zip with the plugin
# manifest (.claude-plugin/plugin.json) at the archive ROOT (a wrapper dir
# like my-plugin/.claude-plugin/plugin.json fails validation). Anthropic
# documents that a custom plugin file can be uploaded but specifies no
# archive layout, so the root-manifest requirement is observed behavior, not
# a documented format. Two ways to install the result: upload this .plugin
# in Claude Cowork, or — in Claude Code desktop/CLI — skip the file and
# `/plugin marketplace add <repo>` straight from the working tree. (Cowork
# can also sync a marketplace from a GitHub repo or git URL — no file
# needed; see references/distribution.md §6.) The versioned artifact also
# serves as a rollback / portable hand-off snapshot. Built REPRODUCIBLY and LEAK-FREE from git-tracked
# content via `git archive`, so a local `.venv`, `.DS_Store`, `__pycache__`, or
# process scratch CANNOT slip in.
#
# Do NOT hand-zip the working tree — `zip -r` honors nothing in .gitignore.
# Shipped by claude-cowork-builder (assets/templates/Makefile); default
# packaging for a plugin that is its own git repo. Use .gitattributes
# export-ignore lines to drop docs/, evals/, or tests from the bundle.
#
# Usage
# -----
#   make                 # build + verify the bundle
#   make plugin          # build dist/<name>-<version>-<sha>.plugin
#   make verify          # build, then assert well-formed + leaked nothing
#   make clean           # remove dist/
#   make plugin REF=v0.1.0   # build from a specific commit/tag instead of HEAD
#
# The artifact name carries the version and short commit SHA — the rollback
# key that says exactly which commit a bundle was cut from.

REF  ?= HEAD
DIST := dist

MANIFEST := .claude-plugin/plugin.json
NAME     := $(shell python3 -c "import json;print(json.load(open('$(MANIFEST)')).get('name','plugin'))" 2>/dev/null || echo plugin)
VERSION  := $(shell python3 -c "import json;print(json.load(open('$(MANIFEST)')).get('version','0.0.0'))" 2>/dev/null || echo 0.0.0)
SHA      := $(shell git rev-parse --short $(REF) 2>/dev/null)
ARTIFACT := $(DIST)/$(NAME)-$(VERSION)-$(SHA).plugin

# Paths that must never appear in a published bundle. `git archive` already
# drops untracked/ignored files; this denylist turns "shouldn't happen" into
# a hard build failure if one is ever force-added.
FORBIDDEN := .DS_Store __pycache__/ .venv/ .idea/ node_modules/ .ruff_cache/ .pytest_cache/

.PHONY: all plugin verify clean print-version print-artifact

all: verify

## Build dist/<name>-<version>-<sha>.plugin from git-tracked content at $(REF).
plugin:
	@test -n "$(SHA)" || { echo "ERROR: could not resolve a commit SHA for REF=$(REF)"; exit 1; }
	@mkdir -p $(DIST)
	@rm -f "$(ARTIFACT)"
	@git archive --format=zip $(REF) -o "$(ARTIFACT)"
	@echo "Built $(ARTIFACT)  (v$(VERSION), $(REF)=$(SHA), $$(du -h "$(ARTIFACT)" | cut -f1))"

## Build, then assert the bundle is well-formed and leaked nothing.
## The skill-layer check accepts any of the three shapes the plugin spec
## treats as valid — skills/<name>/SKILL.md, commands/<name>.md, or a
## single root SKILL.md. Append one grep line per file YOUR plugin must
## ship (bundled scripts, HTML templates, …) — these two are the
## universal minimum.
verify: plugin
	@unzip -l "$(ARTIFACT)" | awk '{print $$4}' | grep -Eq '(^|/)\.claude-plugin/plugin\.json$$' \
		|| { echo "ERROR: $(ARTIFACT) has no .claude-plugin/plugin.json at root"; exit 1; }
	@unzip -l "$(ARTIFACT)" | awk '{print $$4}' | grep -Eq '(^|/)(skills/[^/]+/SKILL\.md|commands/[^/]+\.md|SKILL\.md)$$' \
		|| { echo "ERROR: $(ARTIFACT) ships no skill layer (skills/<name>/SKILL.md, commands/<name>.md, or a root SKILL.md)"; exit 1; }
	@for bad in $(FORBIDDEN); do \
		if unzip -l "$(ARTIFACT)" | awk '{print $$4}' | grep -Fq "$$bad"; then \
			echo "ERROR: forbidden path matching '$$bad' leaked into $(ARTIFACT)"; exit 1; \
		fi; \
	done
	@echo "verify OK: $(ARTIFACT) is well-formed and leaked nothing"

clean:
	@rm -rf $(DIST)

print-version:
	@echo $(VERSION)

print-artifact:
	@echo $(ARTIFACT)
