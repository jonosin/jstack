# learn-voice: fold a lesson into the voice canon

> The LEARN/CAPTURE procedure for the `jstack-myvoice` router. This is an **update-the-playbook**
> instruction, not a drafting flow. It is how the voice canon compounds: every correction
> ${JSTACK_PERSONA_NAME} makes and every draft he approves can be promoted into the voice files, so the
> next session starts ahead of this one. Persona is `${JSTACK_PERSONA_NAME}`.

Run this when the invocation intent is "learn my voice / capture my voice / remember how I talk /
update my voice / harmonize my voice" (match on intent, not exact words).

## Steps

1. **Read the inputs.**
   - The **feedback ${JSTACK_PERSONA_NAME} gave** and/or the **drafts he approved** this session.
     Source them from the conversation, a file he names, or a block he pastes.
   - Plus his **inline directive carried in the invocation param**: what to capture / save / remember
     / harmonize (e.g. "capture how I open cold DMs", "harmonize the talking-script file with the last
     3 approved Looms"). The param tells you the *scope* of the lesson.

2. **Decide which voice file the lesson belongs to.** Exactly one of:
   - `message-email-voice.md`: warm emails and replies.
   - `talking-script-voice.md`: spoken / VO / video-script voice.
   - `cold-message-voice.md`: cold DM / email / InMail voice.
   If the lesson is about cold *strategy* (a lever, a metric, an opener shape) rather than *voice*, note
   that it belongs in `jstack-coldmsg`, not here, and say so instead of forcing it into a voice file.

3. **Edit that file to fold the lesson in.** Do exactly one of:
   - **Add** a new rule, in the file's existing voice and structure.
   - **Sharpen** an existing rule with the new specifics or a concrete example.
   - **Reconcile** a contradiction: if the new lesson conflicts with a rule already there, resolve it
     to one coherent rule; do not leave both.
   Keep each file **tight and deduped**. Harmonize, don't just append. If the new rule overlaps an
   existing one, merge them rather than stacking a near-duplicate.

4. **Confirm the diff back to ${JSTACK_PERSONA_NAME}.** Show what changed (the before/after of the edited
   rule, or the new rule and where it landed) so he can approve or correct it.

Keep this lean. One lesson, one file, one clean edit, one confirmation.
