---
name: jstack-myvoice
description: >-
  Draft outbound in the user's own voice AND keep that voice canon current. DRAFT mode (default): use
  before writing, rewriting, polishing, or replying to emails, DMs, LinkedIn messages, follow-ups,
  intros, product updates, scheduling notes, warm asks, paid-pilot framing, cold messages, OR any spoken
  script the user will say out loud (Looms, VSLs, video VO, call openers) where they want it to sound
  like a real person, not an assistant. The voice composes on two axes: a MODE (warm founder vs confident
  sales) and a CHANNEL (typed vs spoken). Triggers: draft in my voice, write this email/DM/cold message,
  script this Loom/VSL, and "in my confident/sales voice" or "in my warm voice" to force a mode.
  LEARN/CAPTURE mode: when the intent is learn my voice, capture my voice, remember how I talk, update my
  voice, or harmonize my voice, fold an approved draft or correction into the voice canon. Always enforce
  the user's punctuation preference: never use em dashes.
---

# jstack-myvoice: voice router

> Encodes one founder's voice as a reusable canon. The persona is `${JSTACK_PERSONA_NAME}` (set in
> `~/.jstack/config.env`, default "the user"). This file only *routes* + holds the universal rules; the
> voice canon lives in the reference files. Never inline the full rules here.

The voice is composed on **two independent axes**. A draft = **pick one MODE + one CHANNEL**, load both,
compose, then run the Universal QA.

- **MODE (persona / posture)**, *which ${JSTACK_PERSONA_NAME} is he being.* Tone and stance.
- **CHANNEL (mechanics)**, *how it's delivered.* Formatting, rhythm, register. Mode-agnostic.

They're orthogonal, so all four combinations are valid: warm×typed, warm×spoken, confident×typed,
confident×spoken. This skill has two function classes; read the invocation intent and pick one.

## A. DRAFT mode (default)

### Step 1: pick the CHANNEL (how it's delivered)
| Signal in the request | Load |
|---|---|
| Anything **typed**: email, reply, DM, LinkedIn message, follow-up, intro, product update, scheduling note, warm ask, paid-pilot/pricing framing | `references/channel-text.md` |
| Anything he will **say out loud**: Loom/VSL/video VO, call opener, spoken demo or explainer | `references/channel-spoken.md` |

### Step 2: pick the MODE (which persona)
| Signal in the request | Load |
|---|---|
| **Warm founder (default).** Helping someone, deferring to their expertise, delivering work, a considered reply to someone whose judgment he respects. Use this when the mode is unclear. | `references/mode-warm-founder.md` |
| **Confident sales.** Hot inbound, high-intent prospect, peer/operator-to-operator sales, moving a warm lead to a call or close. Also when he explicitly asks for his "confident / sales / attack" voice. | `references/mode-confident-sales.md` |

Default to **warm founder** when the mode signal is ambiguous. If he explicitly names a mode ("in my
confident voice"), honor it. When genuinely torn between modes on a real send, ask one short question.

### Step 3: cold overlay (only if it's a first-touch to a stranger)
A **cold** first-touch (cold DM/email/InMail, connection-request note, cold opener/subject line) also
loads `references/cold-message-voice.md` on top of the chosen mode + channel. The cold *strategy* (levers,
metrics, opener shapes, cadence) lives in `jstack-coldmsg`, not here.

### Step 4: compose + QA
Compose the loaded files: **mode** supplies posture/tone, **channel** supplies formatting/rhythm, the
**cold overlay** (if any) supplies first-touch situational rules. Then run the Universal block below.

`mode-warm-founder.md` + `channel-text.md` together reproduce the old `jstack-msgdraft` warm-email
behavior with no regression; `jstack-msgdraft` is a thin alias into this router.

## Universal rules (every MODE × CHANNEL)
These hold regardless of mode or channel. The reference files don't repeat them; enforce them here.
1. **No em dashes, ever.** Split into two sentences or use a comma/colon/parentheses.
2. **Plain over clever.** No wordplay, cute metaphors, or rhetorical flourishes. Say the point in plain
   words.
3. **Proof over claims.** Verifiable specifics beat adjectives.
4. **Be honest about the deliverable.** Never let a sample seem more finished, certain, or broadly
   applicable than it is.
5. **Never thank them for their time, attention, or interest.** We are the one helping them, so the
   posture is reversed: they end up thanking us. (Full reasoning + the confident-help replacement lines
   live in `mode-confident-sales.md`.)
6. **QA after drafting:** run it through `/humanizer` (the recurring tell is **dropped contractions** that
   stiffen a line, restore "we're" / "you're" / "I've"), **read it aloud**, and confirm no em dashes.

## B. LEARN / CAPTURE mode

Trigger on **intent**, not exact words: "learn my voice", "capture my voice", "remember how I talk",
"update my voice", "harmonize my voice", "save how I open cold DMs", and the like. The invocation param
carries ${JSTACK_PERSONA_NAME}'s directive on *what* to capture.

Load `references/learn-voice.md` and follow it. In short: read the feedback/approved drafts plus his
inline directive, decide **which axis** the lesson belongs to (a mode file, a channel file, the Universal
block, or the cold overlay), edit that target to fold the lesson in (add, sharpen, or reconcile: keep it
deduped), then confirm the diff back to him. This is how the voice canon compounds over time.

## Reference files

**MODE (persona / posture, pick one):**
- `references/mode-warm-founder.md`: warm, considerate, deferential founder voice.
- `references/mode-confident-sales.md`: concise, confident, peer-footing "attack mode."

**CHANNEL (mechanics, pick one, mode-agnostic):**
- `references/channel-text.md`: written-message mechanics (email/DM/reply: register, length, style rules).
- `references/channel-spoken.md`: spoken-delivery mechanics (Loom/VO/call: pronouns, cadence, read-aloud).

**Overlay + procedure:**
- `references/cold-message-voice.md`: cold first-touch overlay (cold STRATEGY lives in `jstack-coldmsg`).
- `references/learn-voice.md`: the update-the-canon procedure for LEARN mode.
