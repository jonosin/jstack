# channel-spoken: spoken-delivery mechanics (Loom / VSL / VO / call)

> **CHANNEL file (mechanics / delivery / cadence), mode-agnostic.** How anything ${JSTACK_PERSONA_NAME}
> **says out loud** should sound: Loom explainers, VSLs, video VO, call openers, spoken demos. These rules
> hold whether the mode is `mode-warm-founder.md` or `mode-confident-sales.md`; compose this file with
> whichever mode is picked. The **posture/tone** (warm deference vs assumed-value confidence) comes from
> the mode file, not here; a warm-lead demo Loom is usually `mode-confident-sales.md` + this file.
> Universal rules (no em dashes, plain-over-clever, proof-over-claims, never-thank-for-their-time,
> humanizer QA) live in `SKILL.md`. Persona: `${JSTACK_PERSONA_NAME}` (set in `~/.jstack/config.env`).
>
> Seeded from his live corrections building the Second Brain Agency demo script and from a real Loom
> recording diffed against the drafted VO. This is the durable spoken-mechanics asset; grow it through
> `learn-voice.md`.

This is a *spoken* voice, not a written one. The bar is simple: it has to sound like a real person
talking warmly to one other person, not like a sales rep reading copy.

## Pronouns: "we" for the work, "I" only for real relationships
- **Say "we," not "I", for the work.** The team is ${JSTACK_PERSONA_NAME} + Beck, and "we" reassures the
  listener there's a team behind it. "What we do is...", "we bring all of it into one place."
- **Use "I" only for genuine personal relationships**, e.g. "I've got a hotel chain owner I'm working
  with." Never "I build" / "I do this" for the offer itself.

## Warm, human delivery (a delivery mechanic, not a mode)
Even in confident mode, the *delivery* is warm and human; the confidence lives in the posture (mode), not
in a cold read.
- Warm, human, a little personal. Emotional connection beats polish.
- **Small human asides are welcome** ("because it sounds really interesting to me, haha").
- **Light humor / a fun joke is good** when it fits the beat.
- Plain spoken rhythm with **contractions everywhere** ("we're", "you're", "I've got", "that's").

## How ${JSTACK_PERSONA_NAME} actually talks (real-delivery cadence)
Ground-truth from a real Loom vs the drafted VO. Draft *toward* these; don't polish them out.
1. **Thread beats with conjunctions.** Nearly every beat opens on "So," / "And," / "Because," / "By the
   way,". His rhythm is a continuous thread, not clean segmented sentence-starts like a written draft.
2. **He talks his way to the word out loud.** Self-corrections and light filler are native cadence, not
   tells to scrub: "a quick overview, **or** intro", "one **unified, uh, single** AI memory", "the funny
   part… **the fun part**", "Oops." Leave room for this natural restart rhythm rather than over-polishing.
3. **He simplifies and merges on delivery.** He collapses crisp numbered beats into one warm flowing line
   ("I'd also love to get a better understanding of how you run things, **and** land on the exact
   solution"), often with a personal "**I'd love to.**" Merged warm sentences, not numbered beats.
4. **Spontaneous self-aware asides are genuinely his** and read as human, not filler: "unless you already
   know how it works," the punchy fragment "**Or everywhere.**", "so, yeah, let me know."
5. **He reaches for stronger, plainer words than the draft**, "stays **permanent.** Instead of going
   stale" (draft said "current"), and **drops research-flex callbacks** (cut "over hundreds of projects,"
   cut "the over-dependence you call out on your own site"). Keep the human analogy, cut the homework.
6. **He softens/defers logistics naturally.** An apology isn't front-loaded; it drops in mid-stream as "**By
   the way,** I'd like to apologize for the delay. **Been** a very busy day on my end." Subject dropped,
   two short sentences, then he moves on. (Whether to apologize at all is a mode call, see the mode file.)
7. **Where the draft matched him** (keep this as the model): "we" for the work / "I" for real
   relationships held perfectly; contractions everywhere; no em dashes; warm-not-salesy; one idea per beat
   with a concrete example carrying the point.

## Personalize early
Open with a warm, **specific guess about their world**, not a generic pitch. Lead with what's probably
true for *them*: "My guess is that a lot of what runs {{COMPANY}} ... is scattered across tools and
inboxes, and a good chunk of it never actually gets written down." Personalization up front earns the
rest of the script.

**Banned phrase: "lives in someone's head" / "lives in your head."** Reads as AI-generated. Say
"scattered" and "never written down" instead; if the beat needs the causal link, "messy data turns into
messy thinking" lands more natural than the head metaphor.

## Sell the profound value, never the table-stakes
- **Never sell table-stakes.** Do not pitch "ask it and get an answer," "searchable," or "a chatbot that
  grows." Every chatbot does that; saying it undersells and signals you don't get the bigger picture.
- **Sell the sophisticated, profound value:** continuous **context gathering**, **memory portability /
  ownership**, the **foundation** the whole AI future runs on. That is what hooks a sophisticated owner.
- **Lead with the bigger picture.** The real hook is the profound framing (own a portable context
  foundation, get ready for the agent era), not feature claims.
- **Don't hedge a true claim, back it with proof.** The capabilities are real; when one sounds big, support
  it with a concrete example or a real client, don't soften it into a hedge.

## One idea per beat, let the example carry the benefit
- **One idea per beat. No overlap, no repetition.** ${JSTACK_PERSONA_NAME} is allergic to beats that echo
  each other. If two beats say the same thing, cut one.
- **Let an example carry the benefit.** A concrete story does the persuading, so nothing else has to
  restate it. The hotel-owner example carries "his team just asks ChatGPT connected to his brain instead
  of messaging him directly," so no other beat repeats the delegation point. Pick the vivid example, then
  trust it. Shorter is better: say it in the fewest words that still land the joke.

## Match depth to the stage
- **A demo highlights selling points; it does not sermonize.** Heavier or more technical topics (where and
  how data is stored, "you own it outright") are **call conversations**, surfaced when the prospect asks,
  not lectured in the demo.
- Aspiration + future-proofing can ride inside an example rather than a standalone beat (e.g. the hotel
  owner wanting to "clone himself and prepare for AGI," delivered as a light joke).

## CTA: soft, low-commitment, tied to their problem
- A short call (~20 minutes), framed around helping **their** problem, not your pitch.
- Keep it low-commitment: "no commitment," "I'm sure it'll be interesting for you either way."
- Warm and a little human is fine ("because it sounds really interesting to me, haha").
- **Banned phrase: "to see if it's a fit."** Replace with a warm reason tied to their actual problem ("to
  see how we could actually help with that").
- The video's job is to earn interest, not to close, and it doesn't close on gratitude in either direction
  (never "thank you for watching"; see `SKILL.md` + `mode-confident-sales.md`).

## Sanity filter
- Run the draft through `/humanizer`. The recurring tell to catch is **dropped contractions** that make a
  line stiff.
- **Read it aloud.** If it doesn't sound like a person talking, plain it down until it does.
