---
name: querybrain
description: >
  Retrieve second-brain facts, decisions, context, and evidence through the
  Graphify-first retrieval overlay. Use when a request needs current canonical
  knowledge, a linked explanation or path, exact raw evidence, a quote, a
  disputed or stale claim, or a high-stakes answer. The skill uses bounded
  second-brain sb query, path, explain, and node get commands; it does not run
  Graphify installation or build workflows during normal retrieval.
---

# querybrain

Use this skill for retrieval only. Raw evidence and the canonical wiki own
truth. The retrieval overlay owns discovery and retrieval planning. A
`node_summary` is a locator only. It is not an answer, evidence, citation, or
verification. Keep `canonical_summary`, `node_summary`, and `source_digest`
separate in every decision.

Invoke it from any workspace when second-brain context can improve the current
task. It queries the second brain only. A web article must already be captured
there to be returned, and workspace-native satellite documents remain on their
workspace route rather than in the overlay.

## Boundary

Run only the bounded repository interface:

```text
python3 tools/sb.py query <text> --depth answer|evidence --budget <tokens> --json
python3 tools/sb.py path <source> <target> --budget <tokens> --json
python3 tools/sb.py explain <node> --budget <tokens> --json
python3 tools/sb.py node get <node-or-path> --budget <tokens> --json
```

The agent can start anywhere. Resolve the second-brain repository from
`SECOND_BRAIN_PATH` in `~/.jstack/config.env`, with `~/second-brain` as the
default, and run the commands from that repository. Use a positive, bounded
output budget. Use the command's JSON result, pagination, omitted count, cursor,
status, and next-command fields. Never open the full graph, manifest, or an
unbounded corpus to answer a query.

Normal retrieval does not load or run the generic Graphify installation,
upgrade, build, or diagnosis skill. The generic Graphify skill is for engine
administration and integration maintenance only.

## Retrieval workflow

1. **Make a bounded query plan.** Read the repository `AGENTS.md` and classify
   the request as a fact, decision, context, path, explanation, draft,
   implementation, analysis, exact quote, disputed claim, stale claim, or
   high-stakes task. Follow `superseded_by` and current-versus-superseded
   status.

   Make one query family for each distinct information need. Use likely
   canonical nouns: the person, venture, decision, concept, title, or stable
   phrase. Split compound questions instead of sending a keyword list. Use no
   more than three query families unless the user asks for deeper retrieval.

   If a query returns `no_support_found`, retry it once with an alternate
   canonical phrase and once with a narrower exact phrase. Use `node get`
   instead when an exact title, path, or stable ID is known. Keep each result
   separate so one weak query does not dilute another.

   Done when: the request has one bounded repository root, one to three focused
   query families, each capped at three query texts, and no request to mutate
   capture, compile, migration, or canonical data.

2. **Select the depth.** Select exactly `answer` when fresh canonical coverage
   is strong and the user needs current synthesis. Select `evidence` for
   drafting, deciding, building, analysis, exact facts or quotes, disputed or
   stale claims, high-stakes work, weak canonical coverage, or when the query
   result requires raw verification. Do not select depth from `personal`,
   `concepts`, or `system` alone. Accept a user depth override, but still state
   the risk and required opens. Use a bounded default budget of 1200 tokens when
   the user gives no budget.

   Done when: the command will use exactly `answer` or `evidence`, the budget
   is positive and bounded, and the reason for the depth is recorded in the
   working answer.

3. **Run the common query wrapper.** Run `sb query` with the selected depth and
   budget. For a relation or traversal request, run `sb path` with the same
   bounded budget. For a node explanation, run `sb explain`. For an exact node
   or source path, run `sb node get`. Use only the selected command's bounded
   JSON result; never substitute a direct Graphify command or a broad file
   search. Require separate `canonical_summary`, `node_summary`, and
   `source_digest` fields, plus role, authority lane, status, provenance,
   source locations, confidence, match signals, freshness, and the required
   next open. A candidate always carries its complete `node_summary`;
   `source_digest` is available only after opening a selected evidence detail
   within the evidence budget.

   Done when: the response is a valid bounded `sb.command/v1` result, the
   selected depth is present, and every returned candidate has a durable
   artifact identity, authority lane, status, source file, source location,
   match signals, freshness, and an exact required-open command.

4. **Read the candidate lanes.** Treat result candidates as locators. Preserve
   the authority-aware ordering: exact stable ID, path, title, and label
   matches outrank summary-only matches. Keep canonical and evidence lanes
   separate. At most five candidates may be returned; a summary-only match may
   occupy at most one slot. Never use a summary to remove a stock Graphify
   candidate. Never treat an inferred relationship as a canonical fact.

   For `answer`, use current canonical candidates only. A raw locator can boost
   a linked canonical candidate but cannot compete in the canonical lane. If
   canonical coverage is inadequate, report that the selected depth must be
   `evidence` and obtain raw support before making a work-grade claim.

   For `evidence`, keep `canonical_candidates` and `evidence_candidates` as
   separate lanes. Reserve at least one returned slot for each non-empty lane;
   normally use three canonical and two raw candidates. Include the complete
   stored `node_summary` with `locator_only: true`, its status and generator
   version, freshness, authority, source file, match signals, source location,
   and required-open command. Do not print the 300-word `source_digest` in the
   candidate list. Keep summary text within `min(400 estimated tokens,
   floor(0.25 * query budget))`; never truncate a stored `node_summary`. If a
   whole candidate cannot fit, omit that lowest-ranked candidate and all its
   fields, then report the omitted count and exact continuation command.

   Done when: the selected candidates are current and eligible, archive and
   superseded-only artifacts are excluded, lane separation is intact, and the
   omitted count and continuation cursor are preserved when the budget limits
   the result.

5. **Open current canonical sources first.** Execute each selected candidate's
   exact required-open command, then open the selected current canonical page
   at its reported source location. For `answer`, stop after the canonical
   page supports the answer. Follow a supersession pointer to its current
   replacement before using a page. When the opened page names a directly
   relevant current concept or source in `See Also` or a wikilink, resolve that
   exact target with `node get` or `path`. Follow only links that answer the
   bounded information need. Do not answer from `node_summary`, `source_digest`,
   a graph edge, or a stale page.

   Done when: every answer claim has support in an opened current canonical
   page, and the response names the page path and relevant source location.

6. **Open raw evidence only at evidence depth.** At `evidence`, open the
   selected current canonical pages first. Then open only the exact raw
   sections named by the evidence candidate's source locations for a quote,
   implementation detail, decision, disputed or stale claim, high-stakes work,
   or weak canonical coverage. Keep raw evidence immutable and cite its path
   and line or section range. Raw candidates remain a separate evidence lane;
   they do not replace canonical synthesis. If the canonical page is weak,
   state the weakness and the raw support instead of silently promoting raw to
   canonical knowledge. If a raw ID returns `not_found`, use an exact source-card
   link from the opened canonical page when one exists and report the broken
   pointer. Do not replace it with a broad raw search.

   Done when: each work-grade claim has both the required canonical context and
   the exact raw section when evidence was required, with no whole-corpus read.

7. **Fail closed unless the complete overlay is ready.** Graph, node map,
   authority, build manifest, and node summaries are one required retrieval
   surface. If any component is absent, stale, or malformed, the command returns
   `OVERLAY_NOT_READY`. Run exactly `sb overlay update --json`, then retry the
   original query. Do not read the retired second-brain index and do not start another retrieval
   lane. A valid complete-overlay zero match starts the bounded reformulation
   in step 1. Report `no_support_found` after those reformulations also return
   zero matches.

   Done when: retrieval used one complete overlay, or stopped with
   `OVERLAY_NOT_READY` and the exact repair command; a zero match after bounded
   reformulation is reported as `no_support_found` and is not treated as proof
   that evidence does not exist.

8. **Report the bounded result.** State the selected depth, answer or path,
   authority lane, current status, opened canonical and raw sources, summary
   status, overlay freshness, omitted count, and continuation command. State
   uncertainty when coverage is weak. A query failure is a bounded failure;
   stop and report its stable error code and retryability. Do not capture,
   compile, migrate, edit wiki pages, refresh the overlay, or repair Graphify
   inside this skill.

   Done when: the user can trace every material claim to an opened current
   canonical page and, when required, an exact raw section, while the response
   exposes all bounded-result limits and status fields.

## Hard guards

- Use Graphify first through the repository `sb` wrapper. Normal query never
  invokes the generic Graphify skill.
- Use `answer` and `evidence` only. There is no `orient` depth.
- Current priorities, active work, urgency, and open loops are retrieved from
  the complete overlay. Generated views are not query inputs.
- The retired second-brain index is not a query input.
- Open current canonical sources before raw evidence. Never use archive or
  superseded-only history as current support.
- Keep raw bodies immutable. This skill has no write operation.
- Treat `node_summary` as a locator and `source_digest` as navigation material;
  neither can satisfy an answer or evidence requirement.
- After a zero match, use the bounded reformulation rule in step 1. Never infer
  absence from the final `no_support_found` result.
- Never run Graphify installation, build, extraction, semantic workers, MCP
  mutation, capture, compile, migration, or canonical writes from this skill.

## Next skills

| Next | When |
|---|---|
| `brainwork` | The request needs capture, compilation, migration, or maintenance. |
| `to-spec` | The retrieved context needs an execution contract. |
