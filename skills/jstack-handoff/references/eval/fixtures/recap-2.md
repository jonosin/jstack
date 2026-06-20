# Session transcript — flaky CI test

User: Our CI is red intermittently. `test_order_settlement` in the payments service fails maybe 1 in 5 runs.

Assistant: Repo is `services/payments` (Python, pytest). The test is in `services/payments/tests/test_settlement.py`. It exercises `settlement.reconcile()` in `services/payments/settlement.py`.

User: Why is it flaky?

Assistant: Traced it. `reconcile()` spawns two threads that both write to a shared `self.ledger` dict without a lock. Under load the CI runner interleaves them and one update is lost, so the asserted balance is off by one transaction. Locally it almost always passes because there's no contention.

Assistant: Reproduced it deterministically by running pytest with `-p no:randomly` and a `time.sleep(0.01)` injected between the read and write — fails every time. Confirms the race.

User: What's the fix?

Assistant: Two options discussed: (a) wrap the ledger mutation in a `threading.Lock`, or (b) make `reconcile()` single-threaded since the parallelism saves <5ms and isn't worth the race. We leaned toward (b) for simplicity but didn't implement yet. STILL TODO: implement (b), remove the thread pool, re-run the test 50x in a loop to confirm zero failures.

User: Have to step away, continue later.
