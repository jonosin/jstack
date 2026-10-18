# Capture new evidence

1. Confirm the user's save request covers the source and private destination.
   Skill installation itself does not authorise new knowledge capture. Resolve
   workspace ownership first: registered nested client, venture, build, then
   unowned brain. A satellite uses its native docs/index route, zero capture
   finalisations and no brain overlay admission.
2. Select explicit role from content, not its source platform or directory:

   | Role | Content |
   |---|---|
   | `personal` | Current user-specific facts, state and accepted decisions |
   | `concepts` | Reusable understanding, frameworks, comparisons and research |
   | `system` | Brain contracts, schemas, tools and operating architecture |

   Preserve useful subject categories in the evidence body and later wiki
   links; do not invent raw frontmatter fields or nested category directories.
   Use one flat `raw/YYYY-MM-DD-topic.md` target. A mixed source can inform
   several canonical pages later; capture need not make one page per source.
3. Deduplicate before fetching/writing. Compare canonical source identity
   (status/video ID, URL, document/version ID, repo ref or conversation identity),
   existing request ID, raw ID and content hash when available. Use bounded exact
   identity lookup, not corpus dumping. Same evidence: return its existing path
   and compile state. New version or correction: append new evidence with
   provenance; a filename collision never justifies overwrite.
4. Acquire source content through an available permitted reader. Preserve title,
   author, canonical URL/document ID, publication/version and capture time,
   extraction method and exact page/section/timestamp locators when available.
   Keep source text distinct from user commentary and agent synthesis. State
   truncation, OCR uncertainty, missing attachments and inaccessible sections.

   | Source | Supported acquisition |
   |---|---|
   | X status/article | Read-only X reader or rendered browser text; local X runbook. Remote `x` + `@fetch-source` uses the current FxTwitter public mirror and validates status ID. Use only for public content; that request sends the status ID to the mirror. An `/i/article/ID` URL needs a verified status permalink or supplied text; the current remote parser accepts status URLs only. |
   | YouTube | Local transcript runbook; remote `youtube` + `@fetch-source` uses the caption reader. Remote target must be `raw/@youtube-title.md`; runner derives title filename. |
   | GitHub repository | Local GitHub capture runbook builds the compact source guide; cloud must supply actual obtained text and commit/ref provenance. No remote repository fetch sentinel exists. |
   | General URL/article | Read the requested URL; supply its obtained body with `external`. Access denied/paywall: request permitted text or report blocked; never reconstruct unseen content. |
   | PDF/DOCX/slides/document | Use an available reader/OCR; capture extracted text with document/version, pages and limitations as `external`. Retain a permitted source pointer/hash; no automatic binary archival or OCR endpoint exists in remote capture. |
   | Conversation | `session` with a stable `conversation:` identity; save only durable authorised content and attribution. |
   | Existing raw/source evidence | Reuse its registered raw ID for compile. For uncaptured external evidence, capture with original provenance; avoid copies of already registered raw. |

5. Route by execution capability. Locally use savetobrain's selected native
   runbook. For general external text, use supported `capture prepare --route
   external --source SOURCE --target raw/DATE-topic.md
   --json`, atomically publish the returned exact raw-v2 metadata plus body
   without replacing an existing file, then `capture finalize --route external
   --artifact raw/DATE-topic.md --json` exactly once. Use the full
   `python3 tools/sb.py` prefix from the brain root. The same boundary applies
   to the native route selected by the owner.

   Check current help: the published CLI prepare currently has no `--title` or
   `--role` options and defaults to personal metadata. For explicit title/role,
   use the existing request processor on dot's computer through the supplied
   driver. Do not invent CLI flags or silently misclassify the evidence.

   On dot's computer pass these exact fields to the driver. Use the watched
   Actions request path only when that compatibility route is explicitly chosen:

   ```json
   {"schema":"sb.remote-capture-request/v1","route":"external","title":"Synthetic notebook example","source":"https://example.org/notebook","role":"concepts","target":"raw/2026-01-01-synthetic-notebook.md","body":"## Provenance\nSynthetic supplied text; illustrative only.\n\n## Source\nA fictional notebook uses numbered pages."}
   ```

   Supported routes: `youtube`, `x`, `github`, `session`, `external`. A literal
   `@fetch-source` is supported only for X/YouTube, not generic URLs/documents.
   The processor performs prepare/write/finalize; the cloud caller must not
   finalise again. Examples are fixtures, never requests to submit.
6. Inspect raw file + stable ID, registration, compile state and run/receipt.
   Report `captured; compile pending` after successful registration. For partial
   failure preserve the file/receipt and inspect before retry. Local registration
   recovery uses `python3 tools/sb.py capture resume RECEIPT --json`;
   check current help. Do not repeat finalize or invent a new capture to hide
   a failed registration. Run `python3 tools/sb.py verify --json` where capable;
   preserve its result separately from the captured state.

Keep credentials, session cookies and access tokens out of captures and examples.
Minimise unrelated third-party information. Preserve authorised sensitive evidence
only inside the private destination; keep skill PRs and logs free of it. Avoid
public mirrors for private/protected sources. A correction appends a new raw
artifact and a verified `supersedes` relation; see maintenance for remote limits.

Done when: the capture is durably registered once, or its precise partial state
and recovery action are reported. Compile only when requested or already authorised.
