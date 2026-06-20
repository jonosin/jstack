# Handoff — directive mode (Normal / directed)

Produces a handoff **document** for an attended next session (you'll be back at the keyboard).

You described what the next session should do. **You set the objective; the agent decides what to
feed forward** — curate the handoff around your directive: pull in only the session facts that serve
it, drop dead ends and tangents, and carry your directive instructions through to the next agent.

Slug from the directive. Apply the shared rules from `SKILL.md` (save path, no-duplication,
redaction, **Suggested skills** section).

## What "good" looks like

The next session is attended, but it should still be able to **start executing in one read** — not
re-derive what you already know. So make the handoff concrete and checkable, not a vague note. Write
these sections:

    # <directive, as an action-oriented title>

    ## Objective
    The directive restated in one or two sentences — concrete and unambiguous about what to produce.

    ## Context & current state
    What's already true: the key files by full repo-relative path, what's done vs. not, and any term
    of art defined in plain English. Reference existing artifacts by path; don't restate them.

    ## Plan / approach
    The ordered steps the next session should take to satisfy the directive. Enough that they don't
    re-plan from scratch.

    ## Acceptance / done-condition
    **What "done" looks like, made concrete and checkable** — the exact command(s) to run and the
    expected result, or the observable behavior to confirm. If the directive is inherently fuzzy, make
    it measurable here. Never leave acceptance subjective ("looks good").

    ## Open decisions (only if any)
    Any unresolved choice the next session faces — but **pre-decide it with a recommended default**
    plus a one-line rationale, so the executor can proceed without stalling (they can still override).
    Don't hand forward a bare "decide X".

    ## Suggested skills
    Skills the next agent should load (per shared rules).

    ## Resume
    End the saved document with the copy-pasteable resume line so a fresh session can pick it up:

        Copy-paste to resume:
          Please read ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md and continue from there.

This is a **Normal, attended** handoff — NOT an autonomous run. Do not emit a `/goal` prompt, an
autonomous execution protocol, or living-document/Progress-Decision-Log sections; that's goal mode.

After writing the document, also print the resolved absolute save path and that same resume line to
the user. The `## Resume` block above must remain **inside the saved document** (not only printed),
so the next session that opens the file sees how to continue:

```
Handoff saved at: ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md

Copy-paste to resume:
  Please read ~/.jstack/handoffs/session-YYYY-MM-DD-<slug>.md and continue from there.
```
