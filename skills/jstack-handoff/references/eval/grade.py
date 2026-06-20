#!/usr/bin/env python3
"""Deterministic machine-grader for the jstack-handoff skilltune.

Usage: grade.py <sandbox> <outputs_subdir> [--judge judge.json]

Reads evals.json + <sandbox>/<outputs_subdir>/<id>.{plan.md,savepath.txt,goalprompt.txt,recap.txt}
Runs every machine assertion per probe. Optionally folds in a cold-judge self-sufficiency
file (judge.json: {"<id>": <score in [0,1]>}). Prints grading JSON to stdout.

composite (per split) = 0.70 * assertion_pass_rate + 0.30 * mean_judge   (judge defaults to 0 if absent)
"""
import sys, os, json, re

def read(p):
    try:
        with open(p, encoding="utf-8") as f: return f.read()
    except OSError: return None

def main():
    sb = sys.argv[1]
    outsub = sys.argv[2]
    judge = {}
    if "--judge" in sys.argv:
        jp = sys.argv[sys.argv.index("--judge")+1]
        jdat = read(jp)
        if jdat:
            try: judge = json.loads(jdat)
            except json.JSONDecodeError: judge = {}
    ev = json.loads(read(os.path.join(sb, "evals.json")))
    forbidden = [p.lower() for p in ev["forbidden_phrases_case_insensitive"]]
    sp_pat = re.compile(ev["savepath_pattern"])
    outdir = os.path.join(sb, outsub)
    results = []
    for probe in ev["probes"]:
        pid = probe["id"]
        plan = read(os.path.join(outdir, f"{pid}.plan.md")) or ""
        savepath = (read(os.path.join(outdir, f"{pid}.savepath.txt")) or "").strip()
        goalprompt = read(os.path.join(outdir, f"{pid}.goalprompt.txt"))
        recap = read(os.path.join(outdir, f"{pid}.recap.txt"))
        a = probe["assertions"]
        checks = []  # (name, passed)
        plan_l = plan.lower()

        if "savepath_no_goal_suffix" in a:
            checks.append(("savepath_no_goal_suffix", bool(savepath) and not savepath.endswith("-goal.md")))
        if "savepath_goal_suffix" in a:
            checks.append(("savepath_goal_suffix", savepath.endswith("-goal.md")))
        if "savepath_pattern" in a:
            checks.append(("savepath_pattern", bool(sp_pat.search(savepath))))
        for sec in a.get("must_contain_sections", []):
            checks.append((f"section:{sec}", sec.lower() in plan_l))
        for s in a.get("must_contain_resume", []):
            checks.append((f"resume:{s}", s.lower() in plan_l))
        for s in a.get("must_contain_living_banner", []):
            checks.append((f"banner:{s}", s.lower() in plan_l))
        for s in a.get("must_reference_session_files", []):
            checks.append((f"ref:{s}", s.lower() in plan_l))
        for s in a.get("must_carry_directive", []):
            checks.append((f"directive:{s}", s.lower() in plan_l))
        for s in a.get("must_have_verifiable_done", []):
            checks.append((f"done:{s}", s.lower() in plan_l))
        if "not_goal_mode" in a:
            # directive/recap must NOT look like a goal handoff
            bad = ("living document" in plan_l) or ("/goal " in plan) or ("stop only when" in plan_l)
            checks.append(("not_goal_mode", not bad))
        if "goalprompt_max_chars" in a:
            gp = goalprompt or ""
            checks.append(("goalprompt_present", bool(goalprompt and goalprompt.strip())))
            checks.append((f"goalprompt<={a['goalprompt_max_chars']}", len(gp) <= a["goalprompt_max_chars"] and len(gp.strip()) > 0))
        for s in a.get("goalprompt_must_contain", []):
            gp = (goalprompt or "")
            checks.append((f"gp:{s}", s.lower() in gp.lower()))
        if "recap_max_words" in a:
            rc = recap or ""
            wc = len(rc.split())
            checks.append((f"recap<={a['recap_max_words']}w", 0 < wc <= a["recap_max_words"]))
        if "agent_decides_rationale" in a:
            rc = (recap or "").lower() + " " + plan_l
            checks.append(("agent_decides_rationale", ("chose" in rc) or ("inferred" in rc)))
        if a.get("no_forbidden_phrases"):
            hit = [p for p in forbidden if p in plan_l]
            checks.append(("no_forbidden_phrases", len(hit) == 0))

        passed = sum(1 for _, ok in checks if ok)
        total = len(checks)
        results.append({
            "id": pid, "split": "train" if pid in ev["split"]["train"] else "heldout",
            "passed": passed, "total": total,
            "failed_checks": [n for n, ok in checks if not ok],
            "judge": judge.get(pid)
        })

    def agg(split):
        rs = [r for r in results if r["split"] == split]
        tp = sum(r["passed"] for r in rs); tt = sum(r["total"] for r in rs)
        apr = tp/tt if tt else 0.0
        js = [r["judge"] for r in rs if r["judge"] is not None]
        mj = sum(js)/len(js) if js else 0.0
        comp = 0.70*apr + 0.30*mj
        return {"assertion_pass_rate": round(apr,4), "passed": tp, "total": tt,
                "mean_judge": round(mj,4), "judge_count": len(js), "composite": round(comp,4)}

    out = {"per_probe": results, "train": agg("train"), "heldout": agg("heldout"),
           "all": agg("train") if False else None}
    # overall across all probes
    tp = sum(r["passed"] for r in results); tt = sum(r["total"] for r in results)
    out["overall_assertion_pass_rate"] = round(tp/tt,4) if tt else 0.0
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
