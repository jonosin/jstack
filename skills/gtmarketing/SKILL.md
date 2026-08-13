---
name: gtmarketing
description: "Front-door router for ALL go-to-market and marketing work. Use whenever the user talks about GTM, go-to-market, launch, positioning, ICP, pricing, sales motion, growth system, competitor/market research, or any marketing execution: copywriting, landing pages, CRO, SEO/AI-SEO, paid ads, ad creative, email sequences, cold email, social content, content strategy, lead magnets, onboarding, churn, referrals, analytics, PR, offers, popups, paywalls, signup flows, marketing plans, or a marketing playbook. Also home of the cold-outbound copy doctrine: drafting, reviewing, optimizing, or A/B-testing cold emails, LinkedIn InMails/DMs, connection notes, openers, subject lines, follow-up sequences, or fixing low reply rates (absorbed coldmsg via references/cold-outreach.md). Routes strategy intents to the GTM-Strategist phase pack and execution intents to the canonical marketing playbooks under ~/.jstack/marketing-skills. Does not generate output itself."
---

# gtmarketing — GTM + marketing front door

Single router for everything go-to-market and marketing. Two skill families behind one door,
plus your machine-local data:

```
~/builds/gtm-strategist-skills/        ← third-party MIT clone: STRATEGY pack (read-only)
  .claude/skills/<phase>/SKILL.md      ← 12 GTM phase skills, loaded BY PATH (a git pull can overwrite)
  my-gtm-context.md                    ← the pack's generic context template (reference only)

~/.jstack/marketing-skills/          ← canonical EXECUTION playbooks, loaded BY PATH
  <playbook>/SKILL.md                ← marketing playbooks routed through this front door

references/ (this skill)               ← COLD-OUTBOUND copy doctrine, loaded BY PATH
  cold-outreach.md                     ← operating layer (absorbed coldmsg 2026-07-06)
  cold-outreach-framework.md           ← deep playbook: psychology, levers, worked examples
  cold-outreach-sources.md             ← provenance
  gtm-40-checks-audit.md               ← current-motion audit + 40-check rubric

~/.jstack/gtm/                         ← YOUR machine-local data (gitignored, survives re-clone)
  contexts/<venture>.md                ← per-venture GTM context the skills read
  outputs/<venture>-*.md               ← gap reports + deliverables (when not in a venture repo)
```

Why split: `~/builds/gtm-strategist-skills` is someone else's repo — a re-clone or `git pull`
wipes anything you put there. Personal venture context never goes in `~/builds/...` and never in
the shareable `~/jstack/` skill repo (secrets-gate forbids it). It lives in `~/.jstack/gtm/`.

This skill does **not** produce output. It (1) picks STRATEGY vs EXECUTION, (2) resolves the
venture context, (3) loads the chosen skill by path, and (4) follows it with the resolved context.

## How to route

1. **Resolve context first.** Decide which venture this is about.
   - If the user named a venture (e.g. Facet), use `~/.jstack/gtm/contexts/<venture>.md` if it
     exists; else fall back to the pack template `~/builds/gtm-strategist-skills/my-gtm-context.md`.
   - If the context file is empty/missing, offer to fill it: interview the user OR pull from the
     second brain (`~/second-brain/wiki/personal/sources/*<venture>*`) before running anything.
     Write the filled context to `~/.jstack/gtm/contexts/<venture>.md`.
2. **Pick the layer.**
   - **Strategy** (deciding what/who/why: positioning, ICP, pricing strategy, launch plan,
     motion, roadmap, auditing the whole GTM) → a **phase** from the 12-phase table.
   - **Execution** (making a specific asset or running a channel: copy, page, ads, emails,
     SEO, social, flows) → a **playbook** from the marketing table.
   - Spans both (e.g. "launch this product") → run the phase first; reach for playbooks when
     it needs concrete assets.
3. **Load and follow.**
   - Phase → `Read ~/builds/gtm-strategist-skills/.claude/skills/<phase>/SKILL.md`, execute verbatim.
   - Playbook → `Read ~/.jstack/marketing-skills/<playbook>/SKILL.md`, execute verbatim.
4. **Deliverables** go to the venture's own repo when working inside one (`~/ventures/<slug>`),
   else `~/.jstack/gtm/outputs/`. Never into `~/builds/...`, `~/jstack/`, or `~/second-brain/`.

## Strategy — intent → GTM phase (`~/builds/gtm-strategist-skills/.claude/skills/`)

| If the user wants to… | Phase | Dir |
|---|---|---|
| Start GTM, strategic foundation, OPE canvas, SWOT, value-prop canvas, 90-day plan | 1. Foundations | `gtm-foundations` |
| Research competitors, customer interviews, market/beachhead, competitive landscape | 2. Intelligence | `collecting-intelligence` |
| Validate ICP/assumptions, run experiments, build evidence-based personas/DMU | 3. Validation | `validating-customers` |
| Define MVP, product roadmap, JTBD value prop, metrics & tracking, usability | 4. Product | `building-product` |
| Pricing strategy, WTP research, business model, unit economics (CAC/LTV) | 5. Pricing | `setting-pricing` |
| Position the product, messaging, UVP/USP, April Dunford positioning, visual identity | 6. Positioning | `crafting-positioning` |
| Build launch assets: website, demo, media kit, pitch deck, press release, legal | 7. Launch assets | `preparing-launch-assets` |
| Choose channels/GTM motions, funnel model, social proof, GTM budget, launch plan | 8. Comms engine | `building-communication-engine` |
| Execute launch: war room, support network, launch emails, launch-day playbook | 9. Launch | `executing-launch` |
| Post-launch growth systems, CRM, SOPs, growth sprints/loops, CRO strategy, new markets | 10. GTM system | `building-gtm-system` |
| Ongoing marketing engine: content, social, email, paid, influencer, community (strategy) | 11. Marketing | `running-marketing` |
| Sales engine: sales deck, case studies, outbound, ABM, partnerships, scripts | 12. Sales | `executing-sales` |

Phases build on each other; outputs feed forward. Default order 1→12, but jump to the phase asked for.

## Execution — intent → marketing playbook (`~/.jstack/marketing-skills/<playbook>/SKILL.md`)

| If the user wants to… | Playbook |
|---|---|
| Write/rewrite page copy: homepage, landing, pricing, feature pages, headlines, CTAs | `copywriting` |
| Edit/polish/review existing copy | `copy-editing` |
| Increase conversions on a page or form | `cro` |
| Design/improve the offer itself: bonuses, guarantees, scarcity, payment structure | `offers` |
| Positioning/context doc for marketing ("who is my audience", product context) | `product-marketing` |
| Tactical pricing page, tiers, packaging, freemium/trial mechanics | `pricing` |
| Full marketing/growth/AARRR plan | `marketing-plan` |
| Marketing ideas/inspiration for a SaaS | `marketing-ideas` |
| Psychology, mental models, cognitive biases, persuasion | `marketing-psychology` |
| Plan a launch, Product Hunt, feature announcement (tactical) | `launch` |
| Content strategy, topic selection, blog roadmap | `content-strategy` |
| SEO audit, technical SEO, "why am I not ranking" | `seo-audit` |
| Programmatic SEO, template pages at scale | `programmatic-seo` |
| AI SEO / AEO / GEO — get cited by LLMs | `ai-seo` |
| Schema markup, structured data, JSON-LD | `schema` |
| Sitemap, URL structure, navigation, internal linking | `site-architecture` |
| Directory submissions for backlinks/DR | `directory-submissions` |
| App Store / Play Store listing (ASO) | `aso` |
| Paid campaigns: Google/Meta/LinkedIn ads, ROAS, CPA | `ads` |
| Ad copy/creative variations at scale | `ad-creative` |
| Marketing images: heroes, social graphics, mockups | `image` |
| Marketing video production (route actual generation via `/vidgen`) | `video` |
| Email sequences, drip/nurture/lifecycle flows | `emails` |
| B2B cold email campaigns/sequences (see cold-message rule below) | `cold-email` |
| Build a prospect list, qualify leads | `prospecting` |
| SMS/MMS marketing flows | `sms` |
| Social content, scheduling, listening (LinkedIn/X/IG/TikTok) | `social` |
| Community strategy: Discord/Slack/forum/subreddit | `community-marketing` |
| Co-marketing, partner campaigns | `co-marketing` |
| Referral/affiliate/word-of-mouth programs | `referrals` |
| PR, press, journalist outreach | `public-relations` |
| Lead magnets, gated content | `lead-magnets` |
| Free tool as marketing (engineering-as-marketing) | `free-tools` |
| Popups, modals, exit-intent, banners | `popups` |
| Signup/registration/trial-activation flow optimization | `signup` |
| Post-signup onboarding, activation, time-to-value | `onboarding` |
| In-app paywalls, upgrade screens, upsells | `paywalls` |
| Churn reduction, cancel flows, save offers, dunning | `churn-prevention` |
| A/B tests, experiment design/program | `ab-testing` |
| Analytics setup/audit: GA4, events, UTMs, conversion tracking | `analytics` |
| Customer research, ICP research, interview/survey analysis | `customer-research` |
| Profile/analyze specific competitors from URLs | `competitor-profiling` |
| Competitor comparison / "vs" / alternative pages | `competitors` |
| Sales collateral: pitch decks, one-pagers, objection docs, demo scripts | `sales-enablement` |
| RevOps: lead scoring/routing, MQL, marketing→sales handoff | `revops` |

## Cross-cutting rules

- **Cold messages:** when any phase or playbook reaches drafting real cold emails, InMails, DMs,
  connection notes, or openers/subject lines, `Read` **`references/cold-outreach.md`** in this skill
  (the reply-psychology + front-end-offer doctrine; absorbed the retired coldmsg) — the
  `cold-email` playbook is supplementary craft, cold-outreach.md wins on conflict — then run the
  copy through **`/myvoice`** (no em dashes).
- **Video generation:** any step that reaches "generate a video/clip" routes through
  **`/vidgen`**, never a backend directly.
- **Overlaps:** pricing *strategy* → phase 5, pricing *page/packaging tactics* → `pricing` playbook.
  Launch *plan/motion* → phases 7–9, launch *checklist/PH tactics* → `launch` playbook. Competitor
  *landscape* → phase 2, specific *profiles/vs-pages* → `competitor-profiling`/`competitors`.
- **Research:** any web research inside a phase/playbook goes through the global `research-router`.

## Stress-test / compare mode

"Stress-test / compare / audit our GTM against what works" = grade the current strategy against
the proven methodology and find gaps. Procedure:

1. Ensure the venture context is filled (brain or interview).
2. Run **gtm-foundations** to capture current-state vs the OPE/SWOT/value-prop baseline.
3. For each relevant phase, read its `SKILL.md`, then score the venture's current GTM
   section-by-section: `match best-practice / thin / missing → fix-first`.
4. Cross-check the adversarial layer: `/jstack-challenge` on the weakest gaps and
   `/premortem` on the launch plan.
5. Output a single gap report (match / thin / fix-first, ordered by impact).

## 40-check audit

"Audit this GTM/campaign", "where is our outbound leaking", or a request to score the current motion
against the GTM System Audit’s 40 checks → `Read`
**`references/gtm-40-checks-audit.md`**, then follow it. It resolves the most current grounded GTM
evidence first, scores every applicable check, separates unknowns from failures, and recommends one
evidence-backed fix-first experiment. This is the canonical `gtmarketing:gtm-40-checks-audit`
operation.

## Pack maintenance

The GTM pack updates with `git pull` in `~/builds/gtm-strategist-skills` (safe — nothing personal
lives there). The canonical marketing playbooks are maintained under `~/.jstack/marketing-skills`; if an
update adds or renames a playbook, update the matching table row here.

## Gotchas

- The GTM phase skills are NOT in the harness skill picker — `Skill(gtm-foundations)` will fail.
  Load them by `Read` path only, through this router.
- The marketing playbooks are deliberately NOT in Claude's global skill picker. Route through
  `gtmarketing`, then load the selected playbook from `~/.jstack/marketing-skills/<playbook>/SKILL.md`.
- Never write venture context or deliverables into `~/builds/gtm-strategist-skills` — a `git pull`
  destroys them. `~/.jstack/gtm/` is the only safe home outside a venture repo.
- `jstack-gtm` is retired; if old notes/handoffs reference it, this skill is its replacement.
- `coldmsg` is retired (2026-07-06); its doctrine lives in `references/cold-outreach.md`
  here. If old notes/handoffs invoke `/coldmsg`, Read that reference instead.

## Next skills

| Next | When |
|------|------|
| `/myvoice` | Any outbound copy is drafted and needs the user's voice pass (cold copy is drafted in-skill via `references/cold-outreach.md`). |
| `/jstack-challenge` | A gap or assumption surfaced needs adversarial pressure-testing. |
| `/premortem` | A launch/GTM plan is drafted and you want failure modes before committing. |
| `/savetobrain` | A durable GTM/marketing decision came out and should persist to the brain. |
| `/vidgen` | A phase/playbook reaches "generate a video/clip". |
