# Versioning Policy

The project uses semantic versions in the form `MAJOR.MINOR.PATCH`.

## Folder model

- Each `versions/MAJOR.MINOR/` folder is a product workstream and dossier.
- Patch releases live inside that folder, for example `versions/1.4/releases/1.4.1.yaml`.
- A minor-version README may evolve while the workstream is active.
- A patch release record becomes historical when its status becomes `released`.
- Git tag `vMAJOR.MINOR.PATCH` identifies the exact released code commit.

## Major versions

A major version signals an intentionally communicated compatibility boundary. Before declaring a new major version, document the affected API, data, workflow, support, and migration guarantees in a product decision record. A major version does not by itself require a rewrite.

## Patch releases

A patch release normally corrects behavior without expanding the accepted minor-version scope. If it introduces new externally observable behavior, document that behavior in a specification or explicit amendment.

## Prereleases

If used, prerelease labels follow SemVer, such as `1.4.0-beta.1`. State whether prereleases receive formal acceptance and support.
