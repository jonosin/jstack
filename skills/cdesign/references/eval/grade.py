#!/usr/bin/env python3
"""Deterministic machine-assertion grader for the cdesign tune loop.

Usage: grade.py <evals.json> <decisions.json> [judge.json]
  decisions.json: [{"id","use_case","uc_file","edit_path","ops":[...],"authoring_plan":"..."}]
  judge.json (optional): {"<id>": <score 0..1>, ...}

Emits grading.json to stdout: per-scenario assertion pass + split rates + composite if judge given.
Composite weights: assertion 0.5, judge 0.5 (efficiency not optimized for a routing/authoring skill).
"""
import sys, json, os

def norm(s): return str(s).strip().lower()

def basename(p): return os.path.basename(str(p).strip()).lower()

def check(decision, a):
    t = a["type"]; v = a["value"]
    if t == "use_case":
        return norm(decision.get("use_case","")) == norm(v)
    if t == "edit_path":
        return norm(decision.get("edit_path","")) == norm(v)
    if t == "uc_file":
        return basename(decision.get("uc_file","")) == basename(v)
    ops = [norm(o) for o in decision.get("ops",[])]
    uploads = [norm(u) for u in decision.get("uploads",[])]
    if t == "ops_present":
        return all(any(norm(want) in o for o in ops) for want in v)
    if t == "ops_order":
        # greedy subsequence: required ops appear in this RELATIVE order in the ops
        # list, tolerant of repeats (e.g. list_files as both a read and a verify step).
        it = iter(ops)
        return all(any(norm(want) in o for o in it) for want in v)
    if t == "op_absent":
        return not any(any(norm(bad) in o for o in ops) for bad in v)
    if t == "no_upload":
        return not any(any(norm(bad) in u for u in uploads) for bad in v)
    raise ValueError("unknown assertion type "+t)

def main():
    evals = json.load(open(sys.argv[1]))
    decisions = {d["id"]: d for d in json.load(open(sys.argv[2]))}
    judge = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    out = {"scenarios": [], "weights": evals["composite_weights"]}
    splits = {"train": [], "heldout": []}
    j_splits = {"train": [], "heldout": []}
    for sc in evals["scenarios"]:
        sid = sc["id"]; sp = sc["split"]
        d = decisions.get(sid)
        results = []
        if d is None:
            passed = 0; total = len(sc["assertions"])
            results = [{"assertion": a, "pass": False, "note": "no decision"} for a in sc["assertions"]]
        else:
            for a in sc["assertions"]:
                ok = check(d, a)
                results.append({"assertion": a, "pass": ok})
            passed = sum(1 for r in results if r["pass"]); total = len(results)
        rate = passed/total if total else 0.0
        splits[sp].append(rate)
        jsc = judge.get(sid)
        if jsc is not None: j_splits[sp].append(float(jsc))
        out["scenarios"].append({
            "id": sid, "split": sp, "use_case_expected": next((a["value"] for a in sc["assertions"] if a["type"]=="use_case"), None),
            "use_case_got": (d or {}).get("use_case"), "passed": passed, "total": total,
            "assertion_rate": round(rate,3), "judge": jsc, "checks": results,
        })
    def mean(xs): return sum(xs)/len(xs) if xs else 0.0
    for sp in ("train","heldout"):
        a_rate = mean(splits[sp]); j_rate = mean(j_splits[sp]) if j_splits[sp] else None
        comp = None
        if j_rate is not None:
            w = evals["composite_weights"]
            comp = w["assertion"]*a_rate + w["judge"]*j_rate
        out[sp] = {"assertion_pass_rate": round(a_rate,4),
                   "judge_score": (round(j_rate,4) if j_rate is not None else None),
                   "composite": (round(comp,4) if comp is not None else None),
                   "n": len(splits[sp])}
    # overall passed/total for the dry-run gate sanity
    out["all_passed"] = sum(s["passed"] for s in out["scenarios"])
    out["all_total"] = sum(s["total"] for s in out["scenarios"])
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
