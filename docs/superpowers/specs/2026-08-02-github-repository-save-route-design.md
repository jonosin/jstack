---
title: GitHub Repository Save Route Design
date: 2026-08-02
status: approved
---

# GitHub Repository Save Route Design

## Decision

`jstack-savetobrain` accepts explicit GitHub repository URLs and `owner/repo` slugs through a deterministic GitHub route. The route writes one immutable, compact repository guide only after authenticated shallow collection and validation succeed. The guide is immediately useful orientation, not an evidence archive.

## Contract

- Input: a repository-root `https://github.com/owner/repo` URL (optional `.git` or trailing slash) or `owner/repo`; issue/tree/blob and other deeper paths are rejected.
- Access: authenticated `gh` only, so public and private repositories follow the same path.
- Provenance: exact `source_type: github-repository`, `capture_format: repository-guide-v2`, canonical repository URL/slug, exactly 40 hexadecimal commit characters, and actual guide authoring harness/model. Do not add descriptive GitHub API or release metadata.
- Guide: original-language `Purpose`, `System`, `Use`, and `Constraints` sections, followed by a nonempty `Where to go deeper` map of 1–12 repository-relative paths with one-line descriptions. Prefer README, AGENTS/CLAUDE, documentation indexes, instruction/skill files, and only the architectural paths needed to close a material documentation gap.
- Omission: never embed repository metadata sections, file-tree dumps or JSON, full documents, manifest contents, source-code excerpts, or fenced code blocks. Upstream guides are named and synthesized, not copied.
- Safety: reject secret-like paths, binaries, generated/dependency directories, traversal, and symlink source references. Authenticate with `gh`, shallow-clone the default branch, and validate every referenced path as a checked-out regular file before publication.
- Atomicity: validate all inputs, write a unique same-directory temporary file, fsync it, then publish with an atomic no-clobber operation to `raw/clips/YYYY-MM-DD-github-owner-repo-1234567-guide-v2.md`. Failures leave no `.tmp`, raw artifact, or newly-created empty destination directory.
- Deduplication: exact parsed frontmatter scalars for `repository`, full `commit`, and `capture_format` identify an existing immutable guide. A legacy capture at the same commit does not dedupe v2. An occupied seven-character v2 filename with different provenance is a loud collision error.

## Interface

`github-capture.py collect` is the normal agent interface. It receives the repository, an agent-authored compact guide through `--guide`, required provenance through `--guide-by`, and 1–12 `--source-ref "path :: description"` values. The guide must contain exactly four nonempty level-two sections in order: `Purpose`, `System`, `Use`, `Constraints`; the collector appends the deeper-reading map. `finalize` remains available for offline workflows and tests without requiring local copies of upstream contents. Vault resolution is environment variable → `~/.jstack/config.env` → `~/second-brain`.

## Non-goals

- No wiki ingestion or modification.
- No broad repository archive or source-code dump.
- No unauthenticated public fallback.
- No capture of canonical workspace-owned specs or decisions; the existing parent-skill rule remains authoritative.

## Verification

Offline tests exercise strict HTTPS/root normalization, authenticated `gh` clone flow, compact output structure and omissions, exact nonempty guide sections, bounded source references, secret/generated/symlink/binary exclusion, format-aware reuse, changed-commit versioning, legacy coexistence, seven-character collisions, atomic no-clobber publication, and failure-without-write cleanup. A live repository smoke test separately verifies the authenticated network path and unchanged-commit reuse.
