# Maintenance runbook

Maintenance checks contracts and generated state. It does not synthesize
knowledge. A requested word such as `lint` or `check` wins over pending compile
work.

## Required sequence

1. **Check schema and links.** Run:

   ```bash
   python3 tools/sb.py schema check --scope all --json
   python3 tools/sb.py lint --json
   python3 tools/sb.py check --json
   ```

   Read bounded findings. Do not hand-edit generated views or repair a semantic
   claim during maintenance.
   Done when: schema, graph/link, and canonical consistency findings are recorded.

2. **Check pending and compile state.** Run:

   ```bash
   python3 tools/sb.py compile status --json
   python3 tools/sb.py compile snapshot --out <snapshot-path> --json
   ```

   Report pending non-deferred raw even when the graph and link checks are clean.
   If the user asked only for maintenance, do not compile without a new explicit
   request.
   Done when: the pending count and any failed or blocked compile records are visible.

3. **Repair only deterministic drift.** If the wrapper reports index or generated
   view drift, run:

   ```bash
   python3 tools/sb.py views build --json
   python3 tools/sb.py check --fix --json
   ```

   Use `check --fix` only for a safe single-match path correction. Inspect the
   bounded result before accepting it. Do not use it for semantic changes.
   Done when: each repair has a named artifact and a before/after hash.

4. **Refresh the overlay when required.** Run:

   ```bash
   python3 tools/sb.py overlay freshness --json
   python3 tools/sb.py overlay rebuild --check --json
   ```

   If stale, rebuild with `overlay rebuild --write --json`, then repeat freshness.
   Never serve a stale summary sidecar as current.
   Done when: freshness is clean, or `OVERLAY_NOT_READY` and exactly `sb overlay update --json` are reported.

5. **Run the completion gate.** Run:

   ```bash
   python3 tools/sb.py verify --json
   ```

   If no repair was needed and pending is zero, report no-op. If pending remains,
   report the count and the compile command; do not hide it.
   Done when: `verify` is clean, or its failed gate, pending count, and resume command are recorded.

## Maintenance limits

- Do not call private Graphify libraries or an installation runbook.
- Do not load or rewrite raw bodies.
- Do not turn a generated summary into canonical knowledge.
- Do not claim a healthy vault when pending, blocked, stale, or failed state remains.
