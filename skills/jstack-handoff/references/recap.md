# Handoff — recap mode (Normal / agent-decides)

No argument was given. The user's context window is filling up and they want to **continue the exact
same work in a fresh session without losing context.** This is a **re-orientation / continuation**
handoff, not a "what I did" report. The next session must pick up the in-flight work seamlessly.

**The handoff routes; the files inform.** Keep the doc short — it can't hold all the context. Its job
is to re-orient and then point at the session's real artifacts (files created/modified) as the
context payload to rehydrate from.

Slug from the session topic. Apply the shared rules from `SKILL.md` (save path, no-duplication —
reference artifacts by path instead of restating them, redaction, **Suggested skills** section).

Write the document with these sections:

    # Continuation handoff — <session topic>

    ## Continue from here
    One paragraph: you are picking up <X> mid-flight; the immediate next step is <Y>. Orient first,
    don't recap.

    ## Brief recap
    A few bullets max — just enough to orient. NOT a blow-by-blow of the session.

    ## Files to read (in order)
    The heart of the handoff. Enumerate the REAL files created/touched this session (full absolute or
    repo-relative paths) — PRDs, specs, plans, code files, handoff packages, notes. Each gets a
    one-line "read this for / it contains…" annotation. Order them so the new session rehydrates
    efficiently (source-of-truth / orientation docs first). These files are the context payload; do
    not restate their contents here.

    ## Current state
    - Done: …
    - In-flight: … (what's half-finished, and where)
    - Immediate next action(s): …
    - Open decisions / questions: …

    ## Don't lose
    Key decisions, constraints, and gotchas the next session must respect — anything that would be
    expensive to rediscover.

    ## Suggested skills
    Skills the next agent should load (per shared rules).

Enumerate the actual session files — never leave placeholders. If a file doesn't exist, don't list it.

Output the resolved absolute path and a copy-pasteable resume line:

```
Handoff saved at: ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md

Copy-paste to resume:
  Please read ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md and continue from there.
```
