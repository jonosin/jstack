---
name: jstack-msgdraft
description: >-
  Draft outbound messages in the user's own voice. Use before writing, rewriting, polishing, or replying to emails, DMs, LinkedIn messages, follow-ups, intros, customer discovery notes, product updates, scheduling notes, warm asks, paid-pilot framing, or business outreach where the user wants it to sound like a real person rather than like an assistant. Enforce the user's punctuation preference: never use em dashes.
---

# jstack-msgdraft: now part of the jstack-myvoice router

This skill is now a thin alias. The voice canon lives in the **`jstack-myvoice`** router
(`~/jstack/skills/jstack-myvoice/`), which routes by intent across three voice files (warm
emails/replies, spoken/talking scripts, cold outreach) and also self-improves via a LEARN mode.

**The original `jstack-msgdraft` email/reply voice is preserved verbatim** in
`~/jstack/skills/jstack-myvoice/references/message-email-voice.md`, so behaviour here is identical to
before. The "never use em dashes" rule still holds.

## What to do
- Load the **`jstack-myvoice`** router (`~/jstack/skills/jstack-myvoice/SKILL.md`) and let it route by
  intent: this is preferred, since it covers emails, talking scripts, and cold outreach.
- Or, if you only need the warm email/reply voice (the classic `jstack-msgdraft` behaviour), load
  `~/jstack/skills/jstack-myvoice/references/message-email-voice.md` directly and draft per its rules.

Then, as before, run the draft through `/humanizer` and never use em dashes.
