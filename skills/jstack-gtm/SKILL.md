---
name: jstack-gtm
description: "Router for any go-to-market work. Use whenever the user talks about GTM, go-to-market, launch, positioning, ICP, pricing, sales motion, marketing engine, growth system, competitor/market research, or wants to plan, audit, or stress-test a GTM strategy. Routes the intent to the correct GTM-Strategist phase skill in ~/builds/gtm-strategist-skills (Maja Voje's 12-phase methodology, 100 tasks). Does not generate GTM output itself — it picks the right phase skill and loads it."
---

# jstack-gtm — GTM router

Single front door for go-to-market work. Two locations, kept separate on purpose:

```
~/builds/gtm-strategist-skills/        ← third-party MIT clone (CODE, not yours)
  .claude/skills/<phase>/SKILL.md      ← the 12 phase skills (read-only; a git pull can overwrite)
  my-gtm-context.md                    ← the pack's own generic context template (reference only)

~/.jstack/gtm/                         ← YOUR machine-local data (gitignored, survives re-clone)
  contexts/<venture>.md                ← per-venture GTM context the phase skills read
  outputs/<venture>-*.md               ← gap reports + phase deliverables
```

Why split: `~/builds/...` is someone else's repo — a re-clone or `git pull` wipes anything you
put there. Personal venture context never goes in `~/builds/...` and never in the shareable
`~/jstack/` skill repo (secrets-gate forbids it). It lives in `~/.jstack/gtm/`.

This skill does **not** produce GTM output. It (1) picks the right phase, (2) makes sure the
venture context file is set, (3) loads that phase's `SKILL.md` and follows it, passing the
context path and writing deliverables to `~/.jstack/gtm/outputs/`.

## How to route

1. **Resolve context first.** Decide which venture this is about.
   - If the user named a venture (e.g. Facet), use `~/.jstack/gtm/contexts/<venture>.md` if it exists;
     else fall back to the pack template `~/builds/gtm-strategist-skills/my-gtm-context.md`.
   - If the context file is empty/missing, offer to fill it: interview the user OR pull from the
     second brain (`~/second-brain/wiki/personal/sources/*<venture>*`) before running a phase.
     Write the filled context to `~/.jstack/gtm/contexts/<venture>.md`.
2. **Match intent → phase** with the table below. Pick the single best phase. If the user spans
   several (e.g. "audit our whole GTM"), run **gtm-foundations** first, then chain in phase order.
3. **Load and follow.** `Read ~/builds/gtm-strategist-skills/.claude/skills/<phase>/SKILL.md` and
   execute it verbatim, passing the resolved context path. These phase skills are not symlinked
   into the harness picker by design — load them by path through this router so there is one
   source of truth.

## Intent → phase map

| If the user wants to… | Route to phase | Dir |
|---|---|---|
| Start GTM, strategic foundation, OPE canvas, SWOT, value-prop canvas, 90-day plan | 1. Foundations | `gtm-foundations` |
| Research competitors, customer interviews, market/beachhead, competitive landscape | 2. Intelligence | `collecting-intelligence` |
| Validate ICP/assumptions, run experiments, build evidence-based personas/DMU | 3. Validation | `validating-customers` |
| Define MVP, product roadmap, JTBD value prop, metrics & tracking, usability | 4. Product | `building-product` |
| Pricing strategy, WTP research, business model, unit economics (CAC/LTV), offers | 5. Pricing | `setting-pricing` |
| Position the product, messaging, UVP/USP, April Dunford positioning, visual identity | 6. Positioning | `crafting-positioning` |
| Build launch assets: website, demo, media kit, pitch deck, press release, legal | 7. Launch assets | `preparing-launch-assets` |
| Choose channels/GTM motions, funnel model, social proof, GTM budget, launch plan | 8. Comms engine | `building-communication-engine` |
| Execute launch: war room, support network, launch emails, launch-day playbook | 9. Launch | `executing-launch` |
| Post-launch growth systems, CRM, SOPs, growth sprints/loops, CRO, new markets | 10. GTM system | `building-gtm-system` |
| Ongoing marketing engine: content, social, email, paid ads, influencer, community | 11. Marketing | `running-marketing` |
| Sales engine: sales deck, case studies, outbound, ABM, partnerships, scripts | 12. Sales | `executing-sales` |
| **Draft/optimize a cold email, InMail, DM, connection note, opener, or subject line** | (standalone skill) | **`jstack-coldmsg`** |

Phases build on each other; outputs feed forward. Default order is 1→12, but jump to the
phase the user asked for.

**Writing the actual cold messages?** When a phase (8 comms engine, 11 marketing email, 12 outbound)
reaches drafting real cold emails, InMails, DMs, connection notes, or their openers/subject lines, load
**`/jstack-coldmsg`** — a battle-tested reply-psychology framework (pinned specificity, opener shapes,
the filter, cadence) — then run the copy through **`/jstack-msgdraft`** for the user's voice (no em
dashes). jstack-coldmsg is a standalone jstack skill, not a pack phase, so it survives a pack re-clone.

## Stress-test / compare mode

"Stress-test / compare / audit our GTM against what works" = grade the current strategy against
this proven methodology and find gaps. Procedure:

1. Ensure the venture context is filled (brain or interview).
2. Run **gtm-foundations** to capture current-state vs the OPE/SWOT/value-prop baseline.
3. For each phase relevant to the question, read its `SKILL.md`, then score the venture's
   current GTM section-by-section: `match best-practice / thin / missing → fix-first`.
4. Cross-check the adversarial layer: invoke `/jstack-challenge` on the weakest gaps and
   `/jstack-premortem` on the launch plan.
5. Output a single gap report (match / thin / fix-first, ordered by impact).

## Conventions

- Per-venture context lives in `~/.jstack/gtm/contexts/<venture>.md` (machine-local, gitignored).
  Create it by copying the pack template `~/builds/gtm-strategist-skills/my-gtm-context.md` and
  filling from the brain. Keeps ventures from clobbering each other and survives a re-clone of the pack.
- Deliverables land in `~/.jstack/gtm/outputs/`. Never write GTM context or deliverables into the
  third-party clone (`~/builds/...`, a git pull overwrites it), the shareable skill repo (`~/jstack/`,
  secrets-gate forbids personal data), or the brain (`~/second-brain/`). To remember a durable GTM
  decision, use `/jstack-savetobrain`.

## Next skills

| Next | When |
|------|------|
| `/jstack-challenge` | A gap or assumption surfaced by a phase needs adversarial pressure-testing. |
| `/jstack-premortem` | A launch/GTM plan is drafted and you want failure modes before committing. |
| `/jstack-savetobrain` | A durable GTM decision came out of a phase and should persist to the brain. |
| `/jstack-vidgen` | A phase (launch assets / marketing) reaches "generate a video/clip". |
| `/jstack-coldmsg` | Drafting/optimizing cold emails, InMails, DMs, connection notes, or their openers/subject lines. |
| `/jstack-msgdraft` | Rendering any drafted outreach in the user's own voice (enforces no em dashes). |
