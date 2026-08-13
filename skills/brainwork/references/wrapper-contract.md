# Second-brain wrapper contract

`python3 tools/sb.py` is the only normal executable interface for brainwork. The
skill routes and interprets these commands. It does not call private Graphify
functions, inline Python, or legacy source-card workflows.

## Response and exit contract

1. Run commands with `--json` unless the command is the long-running MCP server.
   A response has `schema`, `command`, `ok`, `exit_code`, `result`, `error`,
   `pagination`, and `artifacts` fields. Output is bounded to 32 KiB unless a
   named artifact is returned.
   Done when: the response is machine-readable and bounded.

2. Interpret exit codes as follows: `0` completed, `2` invalid input or schema,
   `3` stale or not ready, `4` blocked or conflict, and `5` dependency or internal
   failure. A status command can return `0` while reporting remaining work.
   Done when: the route records the exit code and stable error code, if any.

3. Treat paths in command output as repository-relative POSIX paths. Treat stable
   IDs as durable identity. Use artifact hashes and receipts to resume; do not
   infer state from a path mention or a cache entry.
   Done when: every selected state transition has a stable ID, hash, or receipt.

## Command families

| Need | Public commands |
| --- | --- |
| Freeze and migration | `preflight freeze`, `migrate freeze`, `migrate plan`, `migrate status`, `migrate dry-run`, `migrate checkpoint`, `migrate apply`, `migrate verify-batch`, `migrate rollback` |
| Capture registration check | `capture prepare`, `capture register`, `capture finalize`, `capture resume`, `capture parity` |
| Schema and compile state | `schema check`, `compile status`, `compile snapshot`, `compile next`, `compile show`, `compile conflicts`, `compile resume`, `compile rebuild-manifest` |
| Extraction and canonical delta | `compile validate-extraction`, `compile record-extraction`, `compile integration-plan`, `compile apply-integration` |
| Overlay and views | `overlay build`, `overlay update`, `overlay rebuild`, `overlay freshness`, `overlay status`, `overlay summaries`, `views build` |
| Verification | `lint`, `check`, `verify`, `verify reconstruct` |

Compile, migration, and maintenance runbooks define the allowed order. Do not
invent a command or substitute a shell script when the wrapper has a matching
family.

## State rules

- The compile manifest is sorted JSON Lines and owns compile state. Valid states
  include `deferred`, `captured`, `extracting`, `extracted`, `integrating`,
  `integrated`, `verified`, `failed`, and `blocked`.
- The migration manifest is separate and owns migration state. A checkpoint is the
  only source for rollback.
- `node_summary` is deterministic locator text in a sidecar. It is not a source
  digest, canonical summary, answer, or evidence.
- `verify` is the completion authority. A clean `check` alone is not completion.
