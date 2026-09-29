---
name: fastwiki-version-release
description: Bump and verify FastWiki releases using Semantic Versioning and the repository's ISO-dated VERSION file. Use when asked to version, release, deploy, or report a FastWiki build.
---

# FastWiki Version Release

Treat the repository-root `VERSION` file as the release source of truth:

```text
MAJOR.MINOR.PATCH
YYYY-MM-DD
```

The first line is the user-facing Semantic Version. The second line is the
release date and must be refreshed whenever the version changes.

## Choose the bump

- `major`: incompatible API, schema, authentication, or primary-workflow change.
- `minor`: substantive backward-compatible product, AI, integration, or workflow capability.
- `patch`: backward-compatible fix or security hardening.
- No bump: release tooling, tests, formatting, or documentation added to the
  release that was just versioned.

Prefer `minor` for normal release-significant features; do not infer a breaking
major release from the size of a change.

## Workflow

1. Inspect `git status`, recent commits, and `VERSION` before choosing a bump.
2. Run `python skills/fastwiki-version-release/scripts/bump_version.py <level>`.
   The script increments SemVer and stamps today's ISO date atomically.
3. Review `VERSION` and ensure `/health` plus the authenticated sidebar still
   expose the same version and release date.
4. Run the relevant tests and `git diff --check`.
5. Commit and push only when requested. Do not create a tag or external release
   unless explicitly requested.
6. Report the old/new versions, date, commit, tests, and live health result when
   deployment is part of the task.

If `VERSION` is missing or malformed, stop instead of guessing a baseline.
