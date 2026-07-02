---
name: jstack-coldmsg
description: >-
  Battle-tested framework for drafting cold outbound that earns replies, cold emails, LinkedIn
  InMails and DMs, connection-request notes, and the openers and subject lines for them. Use whenever
  drafting, reviewing, optimizing, or A/B-testing cold outreach: first-touch messages, opener lines,
  subject lines, follow-up sequences, or whenever reply rates are low and the copy needs fixing.
  Encodes the reply psychology and quantified levers from field-tested sources (ColdIQ playbooks,
  cold-outreach psychology) plus the GTM executing-sales phase. Always compose with jstack-msgdraft to
  render the draft in the user's own voice (no em dashes). Pairs with jstack-gtm (outbound/sales).
---

# jstack-coldmsg, cold outbound that gets replies

A framework for writing first-touch cold messages people actually answer. It is opinionated because
the sources agree: the lever is not "better copy," it is **non-automatable specificity** delivered in
a structure the reader's inbox-reflex can't file as spam. Deep detail lives in
[references/framework.md](references/framework.md); provenance in [references/sources.md](references/sources.md).

## The one rule (mental model)
The keep/delete decision fires in ~0.3-0.5s by pattern-match, **before** your copy is read. A message
only clears the reflex when it carries something that **could not have been mass-produced**, one
specific, checkable detail about *that* prospect. The fastest way to get deleted is a confident claim
that is equally true of every competitor in their vertical. **Personalization pinned to a real
specific is the single biggest reply lever (+54.7% in ColdIQ's data). Everything below serves it.**

## Procedure, drafting a batch of cold messages
1. **Find one checkable specific per prospect** (from their profile / site / a real trigger): a number
   (years, locations, headcount, #events), a named product/service/system, a niche, a recent move. If
   you cannot find one, you are not ready to write that message, get the specific first.
2. **Write the opener around that specific** (the highest-leverage line). Pick a shape from the table
   below. Never open with what *you* do. Never pitch in line 1. End on a question they want to answer.
3. **Pin, don't generalize.** Acid test: *if the sentence would read true for any competitor, rewrite
   it.* A vertical-generic assumption = the #1 delete trigger.
4. **Body by tier** (see framework.md): T1 fully custom, T2 semi (industry/role hook), T3 templated
   with one real personalized line. Keep first touch **under ~150 words** (shorter wins, +22%). If you
   can, lead with or attach a tiny **give** (a finding, a 3-bullet artifact), it removes the "believe
   me" step.
5. **CTA = tiny and low-friction.** A yes/no or "worth a quick look?" beats "book a 30-min call."
6. **QA gate before sending** (all must pass):
   - Single-person test: could this exact message have gone to 1,000 people unchanged? If yes, fail.
   - Specificity: contains one real, checkable detail about *them*.
   - Length: first touch lean; no "what we do" preamble.
   - Voice: run it through **jstack-msgdraft**, natural, human, **no em dashes**.
   - Payoff: the body delivers on whatever the opener implied (an opened curiosity gap that resolves to
     a generic pitch is worse than no gap).

## Opener shapes (pick by what signal exists), with measured lift
| Shape | Use when | Pattern | Lift |
|---|---|---|---|
| Peer-comparison | you have industry intel | "We dug into {finding}, want to see what's working for others in {industry}?" | +27.1% |
| Job-change | they recently moved | "Saw you just joined {company}, how's {initiative} shaping up?" | +21.5% |
| Post reference | they posted on a pain | "Spotted your post on {pain}, how are you tackling it today?" | +19.3% |
| Trigger / hiring | a visible trigger fires | "Noticed you're hiring {role}, happy with your current {topic} setup?" | +18.2% |
| **Assumption-pinned** (fallback) | **ICP doesn't post / no trigger** | "{Name}, [one real specific about them], I'd bet [operational reality]. Is that [captured/queryable], or [stuck in heads/inboxes]?" | field-tested* |

\* The no-trigger fallback for non-technical SMB owner-operators who generate no posts/triggers. Stays
assumption-led but **anchored to a real specific + ending on a binary question**, keeps the confident
frame without reading as a blast. **Precondition (learned the hard way): the prospect must already
*feel* the premise.** A "[stuck in heads / not queryable]?" close reads as an unsolicited diagnosis,
and to someone who doesn't live the pain it lands as an insult (see framework.md §9, the Paul block).
Only fire it when the offer's pain is one *they* experience; otherwise screen them out or switch to an
offer-led frame ("I clean it up / I do the work"), not a diagnosis. (Field-tested on the
second-brain-agency burn, both the win and the failure; see framework.md §9.)

## The filter, what earns a reply vs what gets deleted
| Earns a reply | Deleted on sight |
|---|---|
| One checkable specific about *their* business | Claim true of any competitor in the vertical |
| A finished artifact / specific finding, given free | "Free consultation" / generic value prop |
| Short, person-specific, ends on a question | Volume blast; opens with what you do |
| Real loss framing (a competitive dynamic) | Fake scarcity ("3 spots left", "act now") |
| Warmed-up sender (viewed/engaged first) | "Pick your brain" (all cost on the reader) |
| Plain, slightly informal, human register | Over-polished template; synthetic curiosity |

## Follow-up & channel (summary; full detail in framework.md)
- **3-touch sequence beats one-and-done (+42%).** +0 first touch · +2d a *fresh-angle* note (not a
  "just bumping") · +4d switch channel (email referencing the thread, +13.8%) · +7d pressure-off soft
  close ("bad timing? happy to come back next quarter").
- **LinkedIn:** warm up first (view profile, like one recent post) before connecting (+30.2% accept).
  On a connection request, **skip the note unless you have a real hook, a weak note hurts more than
  none.** Keep first message <150 chars. Message within ~2h of acceptance.
- **Scoreboard / diagnostics:** LinkedIn accept 40%+, reply 18%+, positive 8%+ (email: open 40-60%,
  reply 5-15%, positive 2-5%). Low accept → targeting/warm-up. Low reply → opener/copy. Low positive →
  offer/fit. Subject lines gate the open but **won't rescue a body that doesn't earn the reply.**

## Always finish in the user's voice
After drafting structure with this framework, **run the copy through `jstack-msgdraft`** to render it
in the user's voice and enforce punctuation rules (no em dashes). This skill owns the *strategy*;
jstack-msgdraft owns the *voice*.
