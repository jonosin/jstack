# Incremental refresh on dot

## Choose one route

With approved Git credentials and matching configured remotes, use the existing
second-brain-sync owner. It requires both brain and suite checkouts on main with
clean non-divergent history. A Library-bundle checkout, detached HEAD or locally
authored connector snapshot does not satisfy that contract. Do not extract the
GitHub connector's token to make shell Git work.

Without shell Git credentials, use the available authenticated GitHub connector
for reads and the supplied `scripts/dot_refresh.py` for local materialisation.
This transfers only changed blobs after the initial authorised bootstrap bundle.
It does not run on a laptop, call Actions, make network requests from shell,
publish changes or claim a Git fast-forward.

## Build the connector delta

1. Persist a remote cursor outside the checkout after a successful bootstrap or
   acknowledged publication: `repository`, `remote_commit`, `tree`, `local_commit`.
   The remote tree must be obtained from GitHub and match the complete local
   checkpoint tree. A local commit SHA may differ from its corresponding remote
   commit SHA. Never advance the cursor from file-upload success alone.
2. Resolve the target branch to an immutable commit with a live connector read.
   `github_compare_commits` can compare the cursor commit to that target. Require
   the expected ancestry; stop on divergence. Check pagination/truncation and
   preserve deletions and rename old paths. Search results are not a delta.
3. Read target commit metadata with the connector's approved Git data GET, e.g.
   `/repos/OWNER/REPO/git/commits/COMMIT`. Its `tree.sha` is the target tree.
   The available `github_fetch` tool supports these authenticated repository
   reads; verify capability in the active dot session. It returns JSON as text
   in `content`, so decode that JSON before using fields.
4. Fetch changed blobs with `github_fetch_file` at the immutable target commit
   and `encoding: base64`, or `github_fetch_blob` using a returned blob SHA.
   Obtain exact before/after modes and blob SHAs from Git tree reads. Traverse
   root/subtrees for changed paths to avoid one oversized recursive tree; honour
   `truncated`. Fetch old metadata at the base ref when required. For a rename,
   represent old-path deletion plus new-path addition. Keep returned bytes private.
5. Serialize an external plan with exactly these fields:

   ```json
   {"schema":"sb.dot-refresh/v1","repository":"OWNER/REPO","base_remote_commit":"BASE_SHA","target_remote_commit":"TARGET_SHA","base_tree":"BASE_TREE_SHA","target_tree":"TARGET_TREE_SHA","changes":[{"path":"wiki/concepts/example.md","before":{"mode":"100644","sha":"OLD_BLOB_SHA"},"after":{"mode":"100644","sha":"NEW_BLOB_SHA","content_base64":"EXACT_BASE64_BYTES"}}]}
   ```

   Use null before for an addition and null after for a deletion. Supply real
   40-character Git hashes, not placeholders. The helper accepts regular,
   executable and symlink blobs; it does not dereference symlink targets. Gitlinks
   require another route. Complete target-tree validation detects omitted changes,
   incomplete compare results, wrong modes and corrupted blob bytes.

## Materialise and accept

Run on dot, using a fresh destination and external receipt path:

```bash
python3 "$REFRESH_DRIVER" --repo "$BRAIN" --output "$NEXT_BRAIN" --receipt "$NEXT_CURSOR" --plan "$DELTA_PLAN" --cursor "$CURRENT_CURSOR" --repository "$EXPECTED_REPOSITORY"
```

The helper requires a clean source checkpoint matching the cursor tree. It clones
locally, verifies every before blob/mode, imports exact new bytes, and requires
`git write-tree` to equal GitHub's complete target tree **before checkout**.
It creates a clearly labelled local snapshot commit retaining the existing
history. This commit is not the remote commit object. Its receipt records both
identities and the verified tree; reuse that receipt as the next remote cursor.
The helper removes its local clone-origin reference and configures no credentials.
When later publishing through connector commit APIs, use the receipt's remote
commit as the expected branch parent/lease, never its distinct local checkpoint
SHA. Advance the remote cursor only after the published tree matches exactly.

On failure the original checkout is preserved; a partial destination may remain
for inspection. Do not retry to an existing output/receipt or delete user work.
After an uncertain result inspect that output and receipt first. Never treat a
partially applied delta as the current brain.

On success use the new checkout, read changed contracts/code before executing
them, and rebuild/check the ignored complete overlay with the documented public
commands. Run bounded query/source checks and retain `sb verify --json`. Ignored
overlay generations, private receipt stores, model caches and satellite working
trees are not transported by this delta and need their own approved persistence.
Whole-repo historical verification limitations remain visible.

Keep native Git sync and connector snapshots distinct. If full remote commit
objects/signatures/ancestry become required, obtain approved Git authentication
and a proper fetch in a fresh checkout. JSON commit metadata can lose raw Git
header/signature details; do not fabricate a commit object from it and claim its
SHA matches. The connector snapshot route proves current bytes/tree, not new
remote history. No new laptop export is required for subsequent changed blobs.

The initial parent-dot acceptance used six changed blobs from the real private
repository and reproduced the exact remote target tree in a separate checkout.
Overlay rebuild and a bounded query then found the captured article, without
shell Git credentials or another laptop export. Treat this as recorded test
evidence, not proof that a new environment has those capabilities.
