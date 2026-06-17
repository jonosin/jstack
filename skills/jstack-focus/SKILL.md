---
name: jstack-focus
description: Tighter compression layer on top of jstack-voice (~40% shorter). When invoked after a long response, shortens the previous response. Triggered by "/jstack-focus", "focus", "less wordy", "stop explaining", "keep it short", "tired of reading". Turn off with "/jstack-focus off" or when asked for normal detail.
---

# jstack-focus — Tighter Compression Layer

Builds on jstack-voice or AGENTS.md voice defaults. Adds an additional compression layer.

When active:

## Additional Compression

- Shorten sentence structure ~40% from baseline voice.
- Drop adjectives that don't carry decision-critical meaning.
- Use shorter synonyms where technical precision isn't compromised.
- Break complex sentences into two shorter ones.
- Fragments OK when meaning stays clear.

## Shorten Previous Response

When invoked immediately after the agent gave a long response, the agent rewrites its last message in focus-mode compression and presents the shortened version. Format:

```
[shortened]
... compressed version ...
```

Then continue in focus mode.

## Auto-Clarity Exception

Drop compression temporarily for: security warnings, irreversible action confirmations, multi-step sequences where fragment order risks misread, user asks to clarify or repeats question. Resume compression after clear part done.

## Persistence

ACTIVE EVERY RESPONSE once triggered. No revert after many turns. Off only when user says "/jstack-focus off" or "normal mode".

## Next skills

| Next | When |
|------|------|
| `/jstack-voice` | The user wants the warm advisor *tone*, not just shorter length — pair it with this concision toggle. |

Standalone toggle — stays active until "/jstack-focus off"; no required next step. Companion: `/jstack-voice`.
