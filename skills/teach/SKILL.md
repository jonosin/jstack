---
name: teach
description: "Teach the user a new skill or concept over multiple sessions, building a persistent teaching workspace under ~/.jstack/teach. Use when the user says /teach, \"teach me X\", \"help me learn X\", \"walk me through X\", \"prep me for X\", \"get me up to speed on X\", \"I want to understand X\", or \"tutor me on X\". Stateful: it grounds every lesson in a mission, gathers trusted resources, produces beautiful interactive HTML lessons, and tracks what the user has learned."
---

# teach

The user has asked you to teach them something. This is a **stateful** request — they intend to
learn the topic over multiple sessions, and the workspace persists between them.

> Adapted from Matt Pocock's `teach` skill (MIT, © 2026 Matt Pocock),
> `github.com/mattpocock/skills` → `skills/productivity/teach`. Methodology preserved; the workspace
> is rehomed to `~/.jstack/teach` per the jstack harness-artifact convention.

## Teaching workspace — always `~/.jstack/teach/<topic-slug>/`

Do **not** use the current directory. All teaching state lives under `~/.jstack/teach/`, one
subdirectory per topic (`<topic-slug>` = dash-case topic, e.g. `~/.jstack/teach/rust-cli/`). This
keeps teaching artifacts out of whatever repo you happen to be in, and lets multiple topics coexist.

On first use for a topic, create the workspace:

```bash
mkdir -p ~/.jstack/teach/<topic-slug>
```

If the user names a topic you have taught before, resume its existing `~/.jstack/teach/<topic-slug>/`
rather than starting fresh. If unsure which topic they mean, list `~/.jstack/teach/` first.

The state of their learning is captured in the workspace across these files:

- `MISSION.md`: captures the _reason_ the user is learning this topic. Grounds all teaching. Format:
  [references/MISSION-FORMAT.md](./references/MISSION-FORMAT.md).
- `RESOURCES.md`: curated, trusted sources for knowledge and communities for wisdom. Format:
  [references/RESOURCES-FORMAT.md](./references/RESOURCES-FORMAT.md).
- `./lessons/*.html`: the lessons. A **lesson** is a single self-contained HTML file that teaches one
  tightly-scoped thing tied to the mission. This is the primary unit of teaching. Titled
  `0001-<dash-case-name>.html`, incrementing.
- `./reference/*.html`: reference materials — compressed learnings (cheat sheets, algorithms, syntax,
  glossaries). Beautiful documents that print well and are designed for quick lookup. A `GLOSSARY.md`
  (format: [references/GLOSSARY-FORMAT.md](./references/GLOSSARY-FORMAT.md)) is the canonical language
  for the workspace.
- `./learning-records/*.md`: what the user has learned — the teaching equivalent of ADRs. Titled
  `0001-<dash-case-name>.md`, incrementing. Used to calculate the zone of proximal development.
  Format: [references/LEARNING-RECORD-FORMAT.md](./references/LEARNING-RECORD-FORMAT.md).
- `./assets/*`: reusable **components** shared across lessons (see [Assets](#assets)).
- `NOTES.md`: a scratchpad for user preferences and your working notes.

Create the sub-directories (`lessons/`, `reference/`, `learning-records/`, `assets/`) lazily — only
when the first file of that kind is written.

## Philosophy

To learn at a deep level, the user needs three things:

- **Knowledge**, captured from high-quality, high-trust resources
- **Skills**, acquired through highly-relevant interactive lessons you devise from that knowledge
- **Wisdom**, which comes from interacting with other learners and practitioners

Before `RESOURCES.md` is well-populated, your focus is to find high-quality resources that help the
user acquire knowledge. **Never trust your parametric knowledge** — ground teaching in trusted
sources. (For finding those sources, follow the research-router skill.)

Some topics need more skills than knowledge. Theoretical physics leans knowledge; yoga leans skills.

### Fluency vs storage strength

Split two types of learning:

- **Fluency strength**: in-the-moment retrieval of knowledge
- **Storage strength**: long-term retention

Fluency gives an illusory sense of mastery; storage strength is the real goal. Design lessons that
build long-term retention through *desirable difficulty*:

- **Retrieval practice** (recall from memory)
- **Spacing** (distribute practice over time)
- **Interleaving** (mix related topics in practice — skills practice only)

## The mission

Every lesson ties to the mission — the reason the user wants to learn this topic. If the mission is
unclear or `MISSION.md` is unpopulated, your **first job is to interview the user** on why they want
to learn this, then write `MISSION.md`. A bad mission is worse than none — push back on vagueness
(concrete "ship a Rust CLI to my team" beats abstract "learn Rust").

Failing to understand the mission means teaching is ungrounded: lessons feel abstract and you cannot
judge what to teach next. Missions may shift as the user grows — that is normal; confirm with the
user, update `MISSION.md`, and write a learning record capturing the change.

## Zone of proximal development

Each lesson should challenge the user *just enough*. If they name an exact thing to learn, teach it.
Otherwise, find their zone by: reading their `learning-records/`, deciding the right next thing from
the mission, and teaching the most relevant thing that fits.

## Lessons

A lesson is the main thing you produce — the unit in which knowledge and skills reach the user. Each
lesson is one self-contained HTML file in `./lessons/`, titled `0001-<dash-case-name>.html`
(incrementing).

- **Beautiful.** Clean, readable typography and layout — the user returns to review these. Think Tufte.
- **Short and completable quickly.** Working memory is small; stay within it. Each lesson gives one
  tangible win, tied to the mission, inside the zone of proximal development.
- **Cited.** Litter lessons with links to the external resources backing every claim — this is what
  makes a lesson trustworthy.
- **Linked.** Use HTML anchors to link to other lessons and reference documents.
- **Sourced.** Recommend one primary source (the highest-quality, highest-trust resource found) to
  read or watch.
- **Interactive.** Include a reminder that the user can ask you (their teacher) followup questions on
  anything unclear.
- If possible, open the lesson for the user with a CLI command after writing it (e.g. `open <file>`).

### Knowledge in lessons

Teach only the knowledge required for the skill the lesson targets. Teach knowledge first, then have
the user practice the skill via a tight feedback loop. **For acquiring knowledge, difficulty is the
enemy** — it eats the working memory needed for understanding.

### Skills in lessons

Skills are about durability and flexibility — making knowledge stick. **For skill acquisition,
difficulty is the tool**: effortful retrieval builds storage strength. Teach skills through:

- Interactive lessons using quizzes and light in-browser tasks
- Lessons that guide the user through real-world steps (e.g. yoga poses)

Each rests on a **feedback loop** giving feedback as immediately and automatically as possible. For
quizzes, make every answer the same number of words (and characters if possible) so formatting leaks
no clue about the correct answer.

## Assets

Lessons are built from reusable **components** in `./assets/`: stylesheets, quiz widgets, simulators,
diagram helpers — anything a second lesson could reuse. **Reuse is the default.** Before authoring a
lesson, read `./assets/` and build from what exists. When a lesson needs something new and reusable,
write it as a component in `./assets/` and link to it — never inline code a future lesson would
duplicate. A shared stylesheet is the first component every workspace earns, so all lessons look like
one course rather than a pile of one-offs.

## Reference documents

While creating lessons, also create reference documents in `./reference/`. Lessons are rarely
revisited; reference documents are — they are the compressed essence, designed for quick lookup.
Good candidates: syntax/snippets (programming), algorithms/flowcharts (processes), poses/sequences
(yoga), exercises/routines (fitness), and glossaries for any topic with its own nomenclature. Once a
`GLOSSARY.md` exists, adhere to it in every lesson.

## Acquiring wisdom

Wisdom comes from real-world interaction — testing skills outside the learning environment. When the
user asks a question that requires wisdom, attempt to answer, but ultimately delegate to a
**community**: a forum, subreddit, real-world class (budget permitting), or local group where they
can test skills for real. Find high-reputation communities to suggest; if the user opts out of
communities, respect it and note it in `RESOURCES.md`.

## Learning records

Write a learning record in `./learning-records/` when: the user demonstrated genuine understanding of
something non-trivial (sets a new floor); disclosed prior knowledge ("I already know X"); had a
misconception corrected; or the mission shifted. Do **not** record mere coverage — coverage is not
learning; wait for evidence. Full rules and template:
[references/LEARNING-RECORD-FORMAT.md](./references/LEARNING-RECORD-FORMAT.md).

## `NOTES.md`

When the user expresses a preference for how they want to be taught, or something to keep in mind,
record it in `NOTES.md` so you can refer back when designing lessons.

## Next skills

| Next | When |
|------|------|
| `research-router` | Before gathering resources for `RESOURCES.md` or grounding any lesson — route the source search through the research stack instead of parametric knowledge. |
| `/html` | A lesson or reference document needs to be rendered as a clean, on-brand standalone HTML file. |
| `/savetobrain` | A durable insight emerged that belongs in the second brain (a decision or fact about the user), not just in the teaching workspace. |

Otherwise standalone — resume the same `~/.jstack/teach/<topic-slug>/` workspace next session to
continue teaching.
