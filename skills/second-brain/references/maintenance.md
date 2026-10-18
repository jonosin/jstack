# Organisation, corrections and maintenance

Select semantic compile, deterministic maintenance or controlled migration
explicitly. Dot's own runtime runs daily work. A maintenance request does not
authorise compiling the backlog or rewriting the user's beliefs.

| Request | Procedure |
|---|---|
| Check health | `python3 tools/sb.py schema check --scope all --json`, `lint --json`, `check --json`, `compile status --json`, `overlay freshness --json`, `verify --json`. Use full prefix on every command. |
| Stale/incomplete overlay | Run exactly `python3 tools/sb.py overlay update --json`, then freshness and the original query. Stop and report the next code if repair fails. |
| Deterministic generated drift | Use brainwork maintenance runbook: `views build --json`; review safe single-match `check --fix --json` only when the findings warrant it. |
| Canonical correction/new understanding | Append authorised correction evidence, then compile the small semantic delta with raw provenance and current/superseded status. |
| Paths/metadata/category restructuring | Use brainwork migration runbook: freeze preflight + migration manifest, plan disjoint batch, dry-run, checkpoint, apply, verify-batch; rollback only the checkpointed batch on failure. |
| Satellite organisation | Operate in its owning repository through its native router/index; keep satellite content outside brain Graphify/compile. |

Preserve raw bytes and stable IDs. An exact factual correction creates a new raw
artifact with a verified `supersedes` raw ID; maintain canonical supersession
fields and body markers through the controlled proposal. If the old ID cannot
be verified, preserve the user's replacement statement without inventing it.
The current remote-capture JSON contract has no `supersedes` field. For that
structured relation use the native prepare/publish/finalize route in a capable
runtime, or report it as pending. Do not sneak extra fields into remote JSON or
mutate an already finalised raw body. Audited metadata repair is migration work.

Before organisation changes, inspect git state and own only named paths. Keep
before-hashes/checkpoints and reviewed links. Use up to 25 raw or metadata items
or 20 wiki pages per migration batch, as required by the current runbook.
`preflight freeze` and historical verification currently contain machine-local
dependencies; inspect the live code before running on a new dot checkout. Record
a portability blocker rather than replacing protected historical receipts.

Finish with `python3 tools/sb.py verify --json`; retain its JSON even on failure.
Distinguish pre-existing global failures from a newly failed write. Do not weaken
the verifier, regenerate historical proofs without scope, discard unrelated
work or claim the whole brain is healthy because one operation passed.

For schedules, use the host's supported scheduler only when requested. Run the
same dot-runtime procedures on dot's computer, with a durable private checkout,
receipt store and a single-writer lock. Honour the authorised source/scope and
report failure. Keep scheduling separate from skill installation; no periodic
collection or notification is implied. Do not substitute Actions, Codex Cloud or
a laptop job for a requested dot schedule.

Done when: every scoped repair has evidence and final verification, or its
remaining blockers and safe resume command are explicit.
