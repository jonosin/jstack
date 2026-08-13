# Directive

Use directive when the user sets the next session's job. It is an attended handoff: the new agent
reads the package, then proceeds with the stated instruction.

Write:

```markdown
# <action-oriented title>

## Instruction
<the user's requested result>

## Read first
1. `<path>` — <what it establishes>

## Working agreement
<say whether to follow an existing spec, create a spec before execution, or proceed directly>

## Suggested skills

```

Preserve the user's instruction. Point to an existing spec when it owns the work; otherwise state
that the receiving session should create one before execution when planning is needed. Do not invent
a detailed plan or duplicate a referenced artifact. List only skills that will help the next agent.
