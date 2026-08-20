---
name: chatgpt-brain
description: "Operate a second-brain vault remotely from ChatGPT using GitHub as storage. Use when searching, saving, compiling, or maintaining a second brain without a local agent runtime."
---

# chatgpt-brain

This skill adapts second-brain workflows for ChatGPT.

## Core model

GitHub is the vault. The assistant is the reasoning layer. Raw evidence remains immutable. Canonical wiki pages contain distilled knowledge. Generated views are navigation data.

## Reading the brain

When answering from the brain:

1. Read the generated index first when available.
2. Use it only for navigation.
3. Open canonical wiki pages before making claims.
4. Open raw sources for evidence, disputed facts, or detailed context.

## Saving to the brain

When the user asks to save:

1. Create a raw markdown artifact.
2. Preserve the original meaning and context.
3. Commit the new file to the second-brain repository.
4. Do not directly rewrite canonical wiki pages unless explicitly compiling.

## Compiling

When the user asks to compile:

1. Review pending raw material.
2. Extract facts, concepts, and relationships.
3. Decide whether existing wiki pages need updates or new pages.
4. Update canonical markdown.
5. Run verification and refresh generated views when execution tools are available.

## Remote limitations

ChatGPT may edit GitHub files directly. Command execution such as sb.py should run through a remote execution layer such as GitHub Actions.

Do not treat Graphify output as authoritative. It is generated navigation data.
