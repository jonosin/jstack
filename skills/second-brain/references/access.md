# Access and capabilities

## Establish the target

Use the private repository named in the request or established session context.
Verify access with a harmless read of `AGENTS.md`; record ref/commit and fetch the
current contract before writes. For a local runtime, resolve each value by
environment variable, then `~/.jstack/config.env`, then its documented default:
`SECOND_BRAIN_PATH` defaults to `~/second-brain`, `JSTACK_PATH` to `~/jstack`.
Compare the clone's Git remote with the requested repository; stop a mismatch.
Read only required config keys; keep credential material out of output.

Read `CONTEXT.md` for roles. Read a specialised repository skill only on its
explicit trigger (for example, a requested syllabus or academic update).
Inspect applicable `.agents/skills` if present; absence is valid. Load the
selected suite owner and its one route-specific runbook. GitHub fetch can open
`skills/querybrain/SKILL.md`, `skills/savetobrain/SKILL.md` or
`skills/brainwork/SKILL.md` in the same suite repository as this file, without
resolving a machine's home directory.

Apply repository `AGENTS.md` authority/lifecycle rules over stale README advice.
In particular, a generated-index fallback cannot repair `OVERLAY_NOT_READY`.
If the current contract and executable surface disagree, record the discrepancy
and stop only the dependent action. Do not silently invent an alternate lane.

## Choose by actual callable capability

| Capability observed | Supported route |
|---|---|
| Dot's own Python runtime + complete private checkout | Primary route for daily capture, compile, query, maintenance and scheduled work. Use the dot-runtime reference. Node/bun are not required. |
| GitHub reads only | Read contracts and exact known sources, follow known supersession links, cite opened evidence. Prepare requests/proposals for a capable executor. Broad overlay query, capture and maintenance are blocked without execution/transport. |
| GitHub file writes + Actions results readable | Existing compatibility pipeline only when explicitly selected. Daily work belongs on dot's computer. GitHub executes repository code through Actions, not through a fetch/search tool. |
| Local/remote shell with repo dependencies | Run the public `python3 tools/sb.py ...` surface and owning local playbooks; inspect `--help` before unfamiliar options. |
| Approved runtime delegation already available | Hand off exact repo/ref, authorised scope and request/proposal; require durable receipts. Task creation or messaging still follows the host's authorisation rules. |

Tool names vary. Inspect actual tool schemas. A connector search result, a tool
description or an installed GitHub plugin is not proof of write/Actions access.
Do not test a write capability by submitting personal evidence. An explicit
permission failure stops that operation; read-only independent work may continue.

## Existing Actions transport

Inspect this pipeline for migration/testing and compatibility. Preserve it until
the dot runtime passes the agreed tests and the user approves the switch. Do not
submit a request to its watched paths while also processing it on dot's computer.

Read these target-repository files at the selected ref before using transport:

| Operation | Contract source | Push path | Result evidence |
|---|---|---|---|
| Query | `tools/remote_query.py`, `.github/workflows/remote-query.yml` | `state/remote-query-requests/UNIQUE-ID.json` | `state/remote-query-results/UNIQUE-ID.json` + run logs |
| Capture | `tools/remote_capture.py`, `.github/workflows/remote-capture.yml` | `state/remote-capture-requests/UNIQUE-ID.json` | Run JSON/logs, new raw file, compile manifest and registration state |
| Compile | `tools/remote_compile.py`, `tools/remote_compile_verify.py`, `.github/workflows/remote-compile.yml` | `state/remote-compile-requests/UNIQUE-ID.json` | Canonical/extraction/manifest diff, verification log; failure diagnostics under `state/remote-compile-diagnostics/` |

These workflows currently trigger on **push**, not `workflow_dispatch`. File
writes must land on an authorised branch whose workflow exists. Opening a PR
alone is not execution. Use an isolated branch for reviewable mutations unless
the user's established workflow authorises another target; report branch scope.
Never merge, enable auto-merge or change access as an implied ingestion step.

Use a unique, stable request ID per logical operation. Reuse it for inspection
after an uncertain submission. Check the request path, result, raw target,
manifest and Actions run before retrying. The processors may handle every
pending request on that branch; inspect the queue first and stop if execution
would process unrelated work. Never delete someone else's pending request.

For GitHub writes, use the supported create/update/commit APIs and optimistic
SHA checks. Never replace a file without its expected current SHA. If Actions
logs/results cannot be read, report execution as unconfirmed. Query failures may
write `ok: false` while the workflow exits zero: inspect the JSON itself.

Current remote query rebuilds its overlay only in the runner and commits query
transport results. Freshness proves that query snapshot, not a persisted overlay
for later writes. Current remote capture does not run `sb verify`; remote compile
runs `remote_compile_verify.py`, not `sb verify`. Obtain a separate capable-runtime
`sb verify` result before claiming repository completion.
