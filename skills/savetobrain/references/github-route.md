# GitHub Repository Route — savetobrain

Use this route when the user explicitly saves a GitHub repository URL or an `owner/repo` slug. It
creates an immutable, compact `repository-guide-v2` raw source in flat `raw/`; it never ingests or
writes `wiki/`.

## Preconditions

- The user has explicitly invoked `/savetobrain` or otherwise confirmed the save.
- Accept only `https://github.com/<owner>/<repo>` (optional `.git` or trailing slash) or
  `<owner>/<repo>`. Reject deeper paths, query strings, fragments, and non-GitHub sources.
- `gh auth status` must succeed. Private and public repositories use the authenticated `gh clone`
  flow; never fall back to unauthenticated HTTP.
- Do not capture a canonical workspace artifact that belongs in that workspace's docs tree; retain
  the canonical-workspace rule in the parent skill.

## Guide input contract

First write a compact, original-language guide in a temporary file. Its only level-two headings
must be these four, in this order, each with nonblank evidence-bound prose or a list:

```markdown
## Purpose
## System
## Use
## Constraints
```

`Purpose` says what the repository is and when to use it. `System` gives its concise conceptual
map. `Use` explains how to start, configure, or operate it from upstream guidance. `Constraints`
covers operational, security, contribution, or customization boundaries. Do not paste repository
documentation, metadata, a tree, manifest contents, or code. The collector rejects fenced and
indented code plus archive-shaped JSON object/array payloads such as file trees and manifests.
Those structural checks are deterministic; evidence quality, semantic synthesis, and genuinely
original language remain the capturing agent's contract.

Pass each upstream document as a bounded source reference, with a one-line description:

```bash
python3 ~/jstack/skills/savetobrain/scripts/github-capture.py collect \
  --repository "<github-url-or-owner/repo>" \
  --guide "<agent-authored-guide.md>" \
  --guide-by "<actual-harness/model>" \
  --source-ref "README.md :: Primary setup and operating guide." \
  --source-ref "docs/index.md :: Documentation entry point."
```

Pass at least one and at most 12 `--source-ref` values. Each reference must be a safe
repository-relative tracked regular blob (`100644` or `100755`), optionally followed by ` :: ` and
its description. The collector checks every reference against the authenticated shallow clone;
missing tree entries, gitlinks/submodules, direct symlinks, paths traversing a tracked symlink,
secrets, binaries, and generated/dependency paths fail closed. It then appends
`## Where to go deeper` to the guide. Bare paths receive a generic upstream reference description,
but supply a specific description whenever possible. Descriptions and `--guide-by` must be bounded,
printable single lines. `--date` must be a real `YYYY-MM-DD` calendar date.

Prefer upstream README, AGENTS/CLAUDE, documentation indexes, skills/instruction files, manifests,
and only the few architectural files needed to explain a material gap. Refer to them by path; never
copy their contents. If those sources leave a needed conceptual gap, use bounded read-only Luna
exploration and turn its output into original-language guide prose with the relevant paths.

## Output, immutability, and failure behavior

The raw guide contains only minimal provenance (`source`, `repository`, full `commit`, and
`capture_format: repository-guide-v2`), the four authored sections, and the short deeper-reading
map. It has no repository metadata section, file-tree dump, manifest content, source content, or
code block.

Destination format:

`raw/YYYY-MM-DD-github-owner-repo-1234567-guide-v2.md`

Dedupe is exact `repository` + full `commit` + `capture_format`. A legacy capture for the same
commit is not a v2 dedupe match. A later date with the same v2 provenance reuses the immutable file;
a changed commit creates a new guide. A seven-character filename collision fails loudly. All input
validation completes before writing; publication is atomic no-clobber and errors leave no newly
created destination directory, temporary file, or partial raw source.

Before publishing, call `capture prepare` with route `github`, the canonical
repository URL as source, and the chosen flat target. Pass the returned JSON to the
collector with `--prepared`. The collector publishes atomically with that exact
raw-v2 frontmatter. Then call `capture finalize --route github --artifact
"raw/<file>.md" --json` exactly once. A duplicate reports the existing immutable
file and does not finalize again.

On success, use the normal report:

```
Saved raw source: raw/<file>.md — GitHub repository <owner/repo> pinned at <7-char-sha>. Brainwork deferred.
Pending ingest backlog: <N> source(s). Run /brainwork to process.
```
