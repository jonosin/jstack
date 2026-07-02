# Cold outbound framework, full playbook

Consolidated from field-tested sources (see sources.md). SKILL.md is the lean operating layer; this is
the reasoning and the detail behind each rule. Table of contents:
1. The reply psychology (why the rules work)
2. Quantified levers, ranked
3. Opener shapes in detail
4. Personalization tiers
5. Message body architecture (single-touch vs sequence; give-first)
6. Channel mechanics (LinkedIn, email)
7. Sequence & cadence
8. Metrics scoreboard & diagnostics
9. Worked example (second-brain-agency burn: before → after)

## 1. The reply psychology
- **The 0.3-0.5s gate.** Inbox triage is unconscious pattern-matching built from volume: "does this
  feel like the things I delete?", decided before the copy is read. So the first job of a message is
  to *not* match the spam schema, structurally, before it persuades anything.
- **Specificity heuristic.** Specific, checkable detail is the linguistic fingerprint of real effort;
  liars and bots go vague. One precise detail about *their* business interrupts the reflex. The bar:
  "valuable/specific enough that I'd assume a human actually looked."
- **Curiosity gap.** Surface info that implies you know something specific they don't, and leave it
  partly open so the brain wants to close it. It must be *real*, a gap that opens onto a generic
  pitch damages trust more than never opening one.
- **Structural pattern-interrupt.** Shape signals "sales email" independent of words. A short,
  structurally unexpected message can't be filed; one-liners have been measured at 4-6x reply vs the
  full-sequence email "not because the copy is better, because the structure bypassed the dismissal."
- **Deliberate human imperfection.** Slightly informal, hurried phrasing reads as a real person;
  over-polish is itself a template fingerprint that sophisticated buyers screen out.
- **Loss framing, real not fake.** Frame the cost of inaction around a genuine competitive dynamic
  (peers who do X are pulling ahead). Manufactured scarcity ("3 spots left", "act now") is dismissed
  reflexively.
- **The inbox is earned, not owed.** A reply is earned by carrying something non-automatable, an
  artifact or a specific finding, not by asking the reader to believe a claim.

## 2. Quantified levers, ranked (ColdIQ, 100k+ analyzed LinkedIn conversations)
1. Personalization pinned to a checkable specific, **+54.7%** (the dominant lever; ~doubles replies)
2. 3-step sequence vs single message, **+42%**
3. Warm connection request vs cold, **+30.2% acceptance**
4. Short message (<150 chars) vs long, **+22%**
5. Contextual opener vs generic, **+18%**
6. Multi-channel follow-up vs single-channel, **+13.8%**
Implication: spend your effort budget on (1) first. A generic message at high volume is the signal
that tells the reader to skip it; "a message for everyone is a message for no one."

## 3. Opener shapes in detail
The four trigger-based shapes (lift in SKILL.md table) all share a structure: **short, specific to the
person, end on a question instead of an ask, never open with what you do.** The `{company}/{post}/
{role}` slot is *data a machine can pull*; the question framing is *dialogue you design once and
reuse*. Templated framing + real pulled data = scale without the blast signal.

**Assumption-pinned fallback (the no-trigger case).** Many strong ICPs, non-technical SMB
owner-operators (manufacturers, trades, clinics, professional services, logistics, events), rarely
post content or generate job-change/hiring triggers, so the four shapes have nothing to fire on. For
them: keep the confident, assumption-led frame, but **anchor it to one real specific from their
profile and end on a binary question** the owner can answer in one tap. Form:
`{Name}, [real specific], I'd bet [likely operational reality]. Is that [captured/queryable somewhere], or [still in heads/inboxes]?`
This is the one place a confident assumption is allowed, because it is pinned, not category-wide.
Without the pin, it becomes exactly the interchangeable claim that gets deleted.

**Hard precondition: the prospect must already feel the pain you're naming.** The "[in heads /
inboxes]?" close is a *diagnosis* of how they run their business, delivered by a stranger. To someone
who lives that pain (e.g. a daily AI user who re-explains their business every session) it's a
recognised problem and the question lands. To someone who does **not** (a proud long-tenured operator
with no AI in their world), the same line reads as "you're disorganised / you look uneducated" and
provokes a block, not a reply (§9, the Paul block). So the assumption-pinned shape is **gated by
targeting, not just copy**: only fire it when the offer's core pain is one the prospect demonstrably
experiences. When it isn't, do one of two things: (a) screen them out, or (b) switch from a
*diagnosis* frame to an *offer* frame, lead with "I clean it up / organise it / I do the work for
you" (the consultative cleanup hook) and state the pain as a general observation about peers, not an
accusation about them.

## 4. Personalization tiers (match effort to account value)
- **Tier 1 (top ~20):** fully custom, referencing specific company facts and a real finding.
- **Tier 2 (next ~50):** semi-personalized, industry/role-specific hook + one pulled specific.
- **Tier 3 (rest):** templated, but with **one genuinely personalized line** per message (the pinned
  specific). Never a zero-personalization send.

## 5. Message body architecture
- **First touch is short.** Under ~150 words (ideally far less). No "what we do" preamble. The opener
  earns attention; the body delivers one unit of value or one clear, low-friction ask.
- **Give-first (highest-trust move).** Lead with or attach a finished micro-artifact (a scraped list,
  a rewritten section, a 3-bullet "what we'd find") or one specific finding ("your booking page lists
  6 services, your FAQ covers 2, that gap is exactly the tribal knowledge to capture"). It removes the
  "believe me" step. Scope it tight: an insight costs ~10 min; the inbox can't tell it from an
  afternoon's work.
- **Single-touch exception (paid InMail / one-shot channels).** When each send costs a credit and
  multi-touch isn't free, a single tightened message is correct: pinned-specific question opener + ONE
  sentence of offer + a low-friction ask. (This is the second-brain-agency pattern, §9.)
- **CTA.** Lower the activation energy to reply: a yes/no, "worth a quick look?", "open to it?", not a
  calendar block. Ask for the *reply*, not the meeting.

## 6. Channel mechanics
**LinkedIn**
- Warm-up choreography before connecting: view profile, like one recent post, optionally follow, *then*
  connect, buys +30.2% acceptance almost for free and manufactures recognition.
- Connection-request note: **skip it unless you have a real hook from their activity. A weak note hurts
  more than no note.**
- InMail vs DM: InMail (paid) tolerates more volume than connection requests, but the body still wins
  on short + specific. First message <150 chars where possible; message within ~2h of acceptance while
  you're still the name they just approved.
- Throttle ~20 new requests/day per account; stop immediately on any warning/checkpoint.

**Email**
- Subject is the open gate, not the reply gate. Make it carry the specific detail, not a curiosity
  trick. "No subject line will rescue" a body that doesn't earn the reply.
- Diagnostic: low open + low reply → subject/sender/preview failing; high open + low reply → subject is
  fine, opener/triggers are the problem.

## 7. Sequence & cadence (3-touch, beats one-and-done +42%)
- **+0** first touch (pinned opener + question).
- **+2 days** a *fresh-angle* follow-up, a new observation or give, **not** "just bumping this."
- **+4 days** switch channel (e.g. email referencing the LinkedIn thread, +13.8%).
- **+7 days** pressure-off soft close: "Bad timing? Happy to come back next quarter." Leaves the thread
  open instead of forcing a no.
- Build the play by hand until it works; automation scales a motion, it doesn't fix one. Automate the
  data pull, not the dialogue.

## 8. Metrics scoreboard & diagnostics
- LinkedIn: acceptance **40%+**, reply **18%+**, positive replies **8%+**.
- Email: open **40-60%**, reply **5-15%**, positive **2-5%**.
- Read them as a funnel: low acceptance → targeting/warm-up problem; low reply → opener/copy problem;
  low positive → offer/fit problem. Fix the earliest failing stage first.
- Track *qualified/positive* replies per variant in any A/B, not raw replies.

## 9. Worked example, second-brain-agency burn (2026-06-29)
Offer: "an AI memory of your business" to non-technical SMB owner-operators. ICP generates no
posts/triggers → assumption-pinned fallback (§3), single-touch InMail (§5, paid credits).

- **Before (generic, deletes):** "Running the largest B2B cannabis convention series in the US, I'd bet
  a huge amount of your exhibitor history and event playbooks lives in people's heads and scattered
  docs.", the pain clause is true of *every* events company → interchangeable → spam reflex.
- **After (pinned + question-led):** "Marc, after 50+ NECANN events and 6,000 exhibitors since 2015,
  I'd bet the how-we-run-a-show playbook lives mostly with you and a few long-time staff. Is any of it
  written somewhere your team could query, or all in heads?", anchored to real numbers, ends on a
  binary question, confident frame preserved. Subject carries the specific: "the NECANN playbook in
  your head." Body then adds one sentence of offer + the 90-second-video ask. No em dashes (voice via
  jstack-msgdraft).

**Field result + correction (the Paul block, ~18 sends in).** The pinned-question approach above is
*well-formed copy*, but ~18 sends in it produced a sharp negative: Paul (30-yr mail-handling operator)
replied "possibly the worst idea ever... your AI made you look very uneducated" and blocked. Root cause
was **not the wording, it was the target + the frame**:
1. **Wrong target.** The lead list was screened by industry + seniority (operators with tribal
   knowledge), not by *AI use*. Re-scoring the unsent 61 for any AI signal (AI/ChatGPT/Claude in
   headline/about/skills, or a creator/posting signal) found only **3 with strong signal** and **35
   with none**. The offer ("an AI memory of your business") presupposes a daily AI user who feels the
   re-explaining pain; most of the list weren't that.
2. **Diagnosis, not offer.** "I'd bet your know-how is stuck in heads, is it queryable?" is a verdict
   on a stranger's competence. To a non-AI-user the premise is alien, so it reads as an insult.

**The fix (two levers, both required):**
- **Screen on felt pain, not proxy demographics.** For an offer whose value only exists if the buyer
  already does X, qualify on evidence of X (here: AI use), not on a category that merely *correlates*.
  No signal → drop, don't pitch. Confirming the signal often needs the activity/posts pull, not just
  static profile fields, budget for it before sending paid InMail.
- **Reframe diagnosis → offer.** Lead with the consultative cleanup hook ("I clean it up, organise it,
  structure it into one living memory any AI can use, I do the work") and state the pain as a peer
  observation, not an accusation. Variants that worked in review: (A) felt-pain-led for confirmed AI
  users, "you're already running {business} with AI, so you've hit the part where you re-explain it
  every new chat, that's the piece I take off your plate"; (B) cleanup-led for softer signal, "most
  operators who lean on ChatGPT have their knowledge scattered so the AI never really knows the
  business, I organise it into one memory it just knows." Both drop the "in heads?" close entirely.

**Takeaway for the skill:** a confident assumption-pinned opener is gated by **targeting** first. Great
copy aimed at someone who doesn't feel the pain is worse than no message, it burns the credit, the
account-reputation, and the brand. Screen, then write.
