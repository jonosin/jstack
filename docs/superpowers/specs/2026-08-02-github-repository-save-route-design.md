---
title: GitHub Repository Save Route Design
date: 2026-08-02
status: approved
---

# GitHub Repository Save Route Design

## Decision

`jstack-savetobrain` accepts explicit GitHub repository URLs and `owner/repo` slugs through a deterministic GitHub route. The route writes one immutable raw clip only after an authenticated, shallow, bounded collection succeeds.

## Contract

- Input: a repository-root `https://github.com/owner/repo` URL (optional `.git` or trailing slash) or `owner/repo`; issue/tree/blob and other deeper paths are rejected.
- Access: authenticated `gh` only, so public and private repositories follow the same path.
- Provenance: exact `source_type: github-repository`, GitHub metadata, default branch, exactly 40 hexadecimal commit characters, actual harness/model in `synthesis_by`, safe bounded tree, collected file contents, and pinned blob permalinks.
- Scope: the attributed repository map is rendered directly after the title and before metadata/tree/source evidence; source material covers README, root `AGENTS.md`/`CLAUDE.md`, root manifests, and up to six explicit architecture files.
- Safety: reject secret-like paths, binaries, `generated/` and other generated/dependency directories, traversal, and symlinks. Finalization revalidates each explicit include and rejects a matching tree entry with mode `120000`. Cap textual documents at 12,000 characters with a pinned truncation link.
- Atomicity: collect into a temporary directory, validate all material, then atomically create `raw/clips/YYYY-MM-DD-github-owner-repo-1234567.md`, using the first seven commit characters. Failures leave no `.tmp`, raw artifact, or newly-created empty destination directory.
- Deduplication: exact parsed frontmatter scalars for `repository` and full `commit` identify an existing immutable capture; prefix substring matches are forbidden. An occupied seven-character filename with different provenance is a loud collision error.

## Interface

`github-capture.py collect` is the normal agent interface. It receives the repository, a prepared nonblank synthesis Markdown file with at least one section, required `--synthesis-by <actual-harness/model>`, and zero to six `--include` paths. `finalize` is intentionally available for offline/prepared workflows and tests. Vault resolution is environment variable → `~/.jstack/config.env` → `~/second-brain`.

## Non-goals

- No wiki ingestion or modification.
- No broad repository archive or source-code dump.
- No unauthenticated public fallback.
- No capture of canonical workspace-owned specs or decisions; the existing parent-skill rule remains authoritative.

## Verification

Offline tests exercise source normalization, non-GitHub rejection, the exact seven-character filename/frontmatter contract, missing optional docs, secret/generated/symlink/binary exclusion, truncation and pinned permalinks, changed-commit snapshots, immutable deduplication, synthesis validation, and no-output failure cleanup. The GitHub network path is deliberately not exercised in the repository test suite.
