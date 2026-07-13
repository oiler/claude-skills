# wordpress-plugins — Changelog

## v0.2.0 — 2026-07-13

### Fixed — scaffolder input handling

Found by a multi-expert review engagement (orko) and confirmed by independent verification. All four are reproduced by regression tests; the suite grows from 11 to 21.

- **A degenerate plugin name wrote outside the target directory.** `slugify()` returns `""` for names with no alphanumerics (`"!!!"`, `"---"`, `"   "`). Every output path was then built as `f"{slug}/{filename}"` → `"/composer.json"` — an absolute path. `Path(dir) / "/composer.json"` discards `dir` entirely and resolves to the filesystem root. Scope: this only fired when `--dir` did not already exist; under documented usage (`--dir` pointing at an existing plugins directory) the pre-existing overwrite guard caught it first. Fixed by rejecting any slug that is not `^[a-z0-9][a-z0-9-]*$` before any write, and by joining paths component-wise rather than by f-string.
- **`--namespace` and `--text-domain` skipped their sanitizers when passed explicitly.** `namespacify()` / `slugify()` only ran when the flag was *omitted*. An explicit `--namespace` was spliced verbatim into `namespace {ns};` in the generated PHP — a code context, not a comment. Fixed by validating explicit values to the same charset the derived ones produce.
- **Unescaped interpolation into `phpcs.xml.dist` XML attributes.** `name`, `namespace`, and `text_domain` all landed inside attribute values with no escaping; a `"` broke out of the attribute and a `<` would have broken the element. Fixed by constraining namespace/text-domain at the boundary and XML-escaping the free-form `name`.
- **A newline in `--name` injected a line into the generated `.gitignore`.** Fixed by rejecting control characters in `--name`.

The common thread: values were validated on the *derivation* path but trusted on the *explicit* path. Validation now happens at the boundary, in `validate_inputs()`, for both.

## v0.1.0

Initial release. VIP plugin-development skill with deterministic scaffolder, audit checklist, security/performance/standards references.
