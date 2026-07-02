#!/usr/bin/env bash
# Integration test for jstack-linkedin-send scripts.
# Creates its own fixture, runs all checks, cleans up.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"
TMP=$(mktemp -d)
PASS=0
FAIL=0

fail() {
  echo "FAIL: $*" >&2
  FAIL=$((FAIL+1))
}

pass() {
  echo "  ok: $*"
  PASS=$((PASS+1))
}

cleanup() {
  rm -rf "$TMP"
}
trap cleanup EXIT

echo "=== jstack-linkedin-send integration test ==="
echo "Temp dir: $TMP"
echo ""

# ---- fixture ----
cat > "$TMP/prospects.csv" << 'CSV'
Row,Tier,Variant,Channel,Name,FirstName,Business,Country,OpenProfile,OpenInSalesNav,Subject,Message,VideoQuestion,ConnectionNote,Sent,Reply,DemoSent,Call,Deposit,Notes
1,A,A,InMail (credit),Alice Nguyen,Alice,AlphaCorp,US,https://linkedin.com/in/alicen,https://www.linkedin.com/sales/people/ACoAAA111aaa,how AlphaCorp runs,I noticed AlphaCorp handles onboarding without a central knowledge base. I would bring all of that into one AI brain for AlphaCorp so the know-how is not stuck only in your head. Want me to put a short video together?,What is your biggest bottleneck?,Hi Alice connect note,,,,,
2,A,A,InMail (credit),Bob Martinez,Bob,BetaCo,UK,https://linkedin.com/in/bobm,https://www.linkedin.com/sales/people/ACoAAA222bbb,how BetaCo runs,I noticed BetaCo relies on tribal knowledge that is hard to transfer. I would bring all of that into one AI brain for BetaCo so any team member can access it immediately. Want me to put a short video together?,What does your onboarding look like?,Hi Bob connect note,,,,,
3,B,B,InMail (free/open),Carol Kim,Carol,GammaSoft,CA,https://linkedin.com/in/carolk,https://www.linkedin.com/sales/people/ACoAAA333ccc,one AI memory for GammaSoft any AI can use,I noticed GammaSoft trains each new hire from scratch every time. I would bring all of that into one AI memory of GammaSoft that plugs into whatever AI you already use and that you would own outright. Want me to put a short video together?,What tool does your team rely on most?,Hi Carol connect note,,,,,
CSV

echo "--- 1. validate_csv.py ---"
VALIDATE_OUT=$(python3 "$SCRIPTS/validate_csv.py" --dir "$TMP")
VALIDATE_EXIT=$?
echo "$VALIDATE_OUT"
if [ $VALIDATE_EXIT -eq 0 ]; then
  pass "validate_csv.py exited 0"
else
  fail "validate_csv.py exited $VALIDATE_EXIT"
fi
if echo "$VALIDATE_OUT" | grep -q "PASS"; then
  pass "validate_csv.py printed PASS"
else
  fail "validate_csv.py did not print PASS"
fi

echo ""
echo "--- 2. rebuild_send_queue.py ---"
REBUILD_OUT=$(python3 "$SCRIPTS/rebuild_send_queue.py" "$TMP")
REBUILD_EXIT=$?
echo "$REBUILD_OUT"
if [ $REBUILD_EXIT -eq 0 ]; then
  pass "rebuild_send_queue.py exited 0"
else
  fail "rebuild_send_queue.py exited $REBUILD_EXIT"
fi

# assert send_queue.json has 3 rows, each with non-empty subject+message and empty sent
QUEUE_CHECK=$(python3 - "$TMP/send_queue.json" << 'PYEOF'
import json, sys
q = json.load(open(sys.argv[1]))
assert len(q) == 3, f"expected 3 rows, got {len(q)}"
for e in q:
    assert e.get("subject","").strip(), f"row {e['row']}: subject empty"
    assert e.get("message","").strip(), f"row {e['row']}: message empty"
    assert e.get("sent","") == "", f"row {e['row']}: sent should be empty, got {e['sent']!r}"
print("queue OK: 3 rows, all have subject+message, sent empty")
PYEOF
)
echo "$QUEUE_CHECK"
if echo "$QUEUE_CHECK" | grep -q "queue OK"; then
  pass "send_queue.json has 3 rows with subject+message, sent empty"
else
  fail "send_queue.json check failed: $QUEUE_CHECK"
fi

echo ""
echo "--- 3. node --check send_batch.js ---"
NODE_OUT=$(node --check "$SCRIPTS/send_batch.js" 2>&1)
NODE_EXIT=$?
echo "$NODE_OUT"
if [ $NODE_EXIT -eq 0 ]; then
  pass "send_batch.js parses (syntax OK)"
else
  fail "send_batch.js syntax check failed (exit $NODE_EXIT): $NODE_OUT"
fi

echo ""
echo "--- 4. track_reply.py log ---"
LOG_OUT=$(python3 "$SCRIPTS/track_reply.py" log --lead 1 --outcome call_booked --text "wants a call" --dir "$TMP")
LOG_EXIT=$?
echo "$LOG_OUT"
if [ $LOG_EXIT -eq 0 ]; then
  pass "track_reply.py log exited 0"
else
  fail "track_reply.py log exited $LOG_EXIT"
fi
if echo "$LOG_OUT" | grep -q "logged:"; then
  pass "track_reply.py log printed logged:"
else
  fail "track_reply.py log did not print logged:"
fi

echo ""
echo "--- 5. track_reply.py stats ---"
STATS_OUT=$(python3 "$SCRIPTS/track_reply.py" stats --dir "$TMP")
STATS_EXIT=$?
echo "$STATS_OUT"
if [ $STATS_EXIT -eq 0 ]; then
  pass "track_reply.py stats exited 0"
else
  fail "track_reply.py stats exited $STATS_EXIT"
fi
if echo "$STATS_OUT" | grep -qE "^A[[:space:]]"; then
  pass "stats output contains variant A row"
else
  fail "stats output does not contain variant A row"
fi
if echo "$STATS_OUT" | grep -qE "^B[[:space:]]"; then
  pass "stats output contains variant B row"
else
  fail "stats output does not contain variant B row"
fi
CALLS_CHECK=$(python3 -c "
import csv, sys
rows = list(csv.DictReader(open('$TMP/prospects.csv')))
calls = sum(1 for r in rows if r.get('Call','').strip().lower() == 'yes')
assert calls == 1, f'expected 1 call, got {calls}'
print(f'calls in CSV: {calls}')
")
CALLS_EXIT=$?
echo "$CALLS_CHECK"
if [ $CALLS_EXIT -eq 0 ]; then
  pass "prospects.csv has Calls=1 after log"
else
  fail "prospects.csv Calls count is not 1: $CALLS_CHECK"
fi

echo ""
echo "==================================="
echo "Results: $PASS passed, $FAIL failed"
if [ $FAIL -gt 0 ]; then
  echo "SOME TESTS FAILED"
  exit 1
fi
echo "ALL TESTS PASSED"
