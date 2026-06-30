---
name: jstack-myvoice
description: >-
  Draft outbound in the user's own voice AND keep that voice canon current. DRAFT mode (default): use
  before writing, rewriting, polishing, or replying to emails, DMs, LinkedIn messages, follow-ups,
  intros, customer-discovery notes, product updates, scheduling notes, warm asks, paid-pilot framing,
  cold messages, OR any spoken script the user will say out loud (Looms, VSLs, video VO, call openers)
  where they want it to sound like a real person, not an assistant. Triggers: draft in my voice, write
  this email, draft this DM, write this cold message, script this Loom/VSL, write what I'll say.
  LEARN/CAPTURE mode: when the intent is learn my voice, capture my voice, remember how I talk, update
  my voice, or harmonize my voice: fold an approved draft or correction into the voice canon. Always
  enforce the user's punctuation preference: never use em dashes.
---

# jstack-myvoice: voice router

> Encodes one founder's voice as a reusable canon. The persona is `${JSTACK_PERSONA_NAME}` (set in
> `~/.jstack/config.env`, default "the user"). This file only *routes*; the voice rules live in the
> reference files. Never inline the full rules here.

This skill has two function classes. Read the invocation intent and pick one.

## A. DRAFT mode (default)

Anything where ${JSTACK_PERSONA_NAME} wants something written in his voice. Route by intent to **one**
reference file, load it, draft per its rules, then run the QA below.

| Signal in the request | Load |
|---|---|
| An email, reply, DM, LinkedIn message, follow-up, intro, product update, scheduling note, warm ask, paid-pilot/pricing framing: a message to someone he already knows or is in dialogue with | `references/message-email-voice.md` |
| Something he will **say out loud**: a Loom/VSL/video VO script, a call opener, a talking script, a spoken explainer | `references/talking-script-voice.md` |
| A **cold** first-touch to a stranger: cold DM, cold email, InMail, connection-request note, cold opener/subject line | `references/cold-message-voice.md` |

If two signals overlap (e.g. a cold email he'll also read aloud), pick the file matching the *dominant*
channel; cold always beats warm-email when the recipient is a stranger. When genuinely unsure, ask one
short clarifying question rather than guessing.

After drafting:
1. **Run it through `/humanizer`.** The recurring tell to catch is **dropped contractions** that make a
   line stiff ("we are" / "you are" / "I have" where ${JSTACK_PERSONA_NAME} would say "we're" /
   "you're" / "I've"). Restore the spoken rhythm.
2. **Read it aloud.** If it doesn't sound like a real person talking, plain it down.
3. **No em dashes, ever.** Split into two sentences or use a comma/colon/parentheses.

All prior `jstack-msgdraft` behaviour is preserved verbatim in `references/message-email-voice.md`, so
the email/reply voice does not regress. `jstack-msgdraft` is now a thin alias into this router.

## B. LEARN / CAPTURE mode

Trigger on **intent**, not exact words: "learn my voice", "capture my voice", "remember how I talk",
"update my voice", "harmonize my voice", "save how I open cold DMs", and the like. The invocation param
carries ${JSTACK_PERSONA_NAME}'s directive on *what* to capture.

Load `references/learn-voice.md` and follow it. In short: read the feedback/approved drafts plus his
inline directive, decide which of the three voice files the lesson belongs to, edit that file to fold
the lesson in (add, sharpen, or reconcile: keep it deduped), then confirm the diff back to him. This is
how the voice canon compounds over time.

## Reference files
- `references/message-email-voice.md`: warm founder emails and replies (owns the written-message voice).
- `references/talking-script-voice.md`: spoken / VO / video-script voice (owns what he *says*).
- `references/cold-message-voice.md`: cold DM / email / InMail voice (the cold STRATEGY lives in `jstack-coldmsg`).
- `references/learn-voice.md`: the update-the-playbook procedure for LEARN mode.
