# Query and source-backed answers

1. Read the target/ref contract and choose `answer` for current synthesis with
   strong canonical coverage; use `evidence` for quotes, disputed/stale claims,
   decisions, drafting, implementation or weak coverage. Start with a bounded
   1200-token budget and up to three distinct query families.
2. Use the complete overlay for discovery. In a runtime use the querybrain
   owner. Its supported commands are:

   ```text
   python3 tools/sb.py query TEXT --depth answer|evidence --budget 1200 --json
   python3 tools/sb.py node get NODE-OR-PATH --budget 1200 --json
   python3 tools/sb.py path SOURCE TARGET --budget 1200 --json
   python3 tools/sb.py explain NODE --budget 1200 --json
   ```

   Cloud transport currently supports query only, not path/explain/node command
   dispatch. Create the request below only through an available authorised write
   tool. Substitute the user's actual question, keep keys exact, then inspect
   the matching result JSON and workflow run.

   ```json
   {"schema":"sb.remote-query-request/v1","query":"synthetic example decision","depth":"evidence","budget":1200,"limit":5}
   ```

   `budget` is an integer 1..4000; `limit` is 1..20. Require `ok: true`, a bundle
   hash/generation, and fresh graph, authority and summaries. Read coverage,
   diagnostics, selected depth and omitted/continuation information if returned;
   do not fabricate local result fields that the remote schema lacks.
3. Open selected **current canonical pages** at their source locations before
   answering. Follow `superseded_by` and `> SUPERSEDED` to the exact replacement.
   At evidence depth also open exact raw sections. Keep canonical and evidence
   lanes separate. `node_summary`, `source_digest`, graph edges and generated
   index pages are locators, never claim support.
4. For a known exact page, a read-only connector may open it directly and its
   explicit raw/supersession links. State that this is a bounded source read,
   with overlay discovery unavailable if so. Do not turn GitHub full-text
   search into an alternate broad brain retrieval lane. Use transport/runtime
   for unknown-topic discovery. A returned `OVERLAY_NOT_READY` always stops
   retrieval until the documented overlay update succeeds.
5. After a valid complete-overlay zero match, retry once with an alternate
   canonical phrase and once with a narrower exact phrase per family. Report
   `no_support_found` after those attempts; this is not proof of absence.
   Preserve an error code and retryability for actual failures.
6. Cite opened wiki/raw GitHub **blob links at the inspected commit** with
   relevant line or section locations. Separate sourced facts, synthesis and
   uncertainty. Do not cite a query result file as proof of a personal fact.
   Report depth, sources, freshness snapshot and coverage limits compactly.

Done when: each material claim traces to opened current canonical support and
the exact raw section when required, or the unsupported claim is left explicit.
Keep ordinary reads read-only with respect to knowledge; cloud request/result
writes are operational transport and may contain private query text.
