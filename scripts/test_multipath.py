#!/usr/bin/env python3
"""Test multi-path diagnosis: 2 success paths + 1 failure path."""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from medical_task_suite.generation.v2.task_generation.task_generator import MedicalTaskGenerator
from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator


def build_trajectory(actions, task, revealed_syms, diagnosis,
                     extra_empty_asks=0, drug="metformin"):
    """Build a trajectory with given revealed symptoms.

    extra_empty_asks: simulates prerequisite/gate steps that don't reveal symptoms
    """
    traj = []
    t = 0
    # Prerequisite steps (no reveals — simulates gate unlocking cost)
    for _ in range(extra_empty_asks):
        traj.append({"t": t, "action": actions["ASK"]["id"],
                      "observation": {"symptoms_revealed": []},
                      "reward": None, "done": False})
        t += 1
    # Symptom-revealing steps
    for s in revealed_syms:
        traj.append({"t": t, "action": actions["ASK"]["id"],
                      "observation": {"symptoms_revealed": [s]},
                      "reward": None, "done": False})
        t += 1
    # Clinical steps
    traj.append({"t": t, "action": actions["ORDER_LAB"]["id"],
                  "observation": {}, "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["GET_RESULTS"]["id"],
                  "observation": {"lab_results": task["clinical"]["labs"]},
                  "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["DIAGNOSE"]["id"],
                  "observation": {"diagnosis": diagnosis},
                  "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["CHECK_ALLERGY"]["id"],
                  "observation": {"allergies": []},
                  "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["CHECK_INTERACTION"]["id"],
                  "observation": {"interactions": "none"},
                  "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["PRESCRIBE"]["id"],
                  "observation": {"drug": drug},
                  "reward": None, "done": False}); t += 1
    traj.append({"t": t, "action": actions["END"]["id"],
                  "observation": {"done": True},
                  "reward": None, "done": True})
    return traj


def main():
    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)
    task = gen.generate_task("diagnostic_uncertainty", "L2",
                             target_disease="type 2 diabetes", seed=42)
    actions = task["actions"]
    ev = BenchEvaluator(task)

    # Show paths
    ss = task["ground_truth"]["solution_space"]
    paths = ss["derived_from"]["minimal_information_sets"]
    print("=" * 60)
    print("MINIMAL INFORMATION SETS")
    print("=" * 60)
    for i, p in enumerate(paths):
        print("  Path %d: must_collect=%s  is_optimal=%s" % (
            i + 1, p["must_collect"], p["is_optimal"]))

    print()
    print("SYMPTOM TIERS:")
    for tier in ["volunteer", "if_asked", "hidden", "resistant", "misleading"]:
        syms = task["patient"]["symptoms"].get(tier, [])
        if syms:
            print("  %s: %s" % (tier, syms))

    pa_syms = paths[0]["must_collect"]
    pb_syms = paths[1]["must_collect"]
    misleading = task["patient"]["symptoms"].get("misleading", [])

    # PATH A: Classic (optimal) — volunteer + if_asked, NO gate cost
    traj_a = build_trajectory(actions, task, pa_syms, "type 2 diabetes",
                              extra_empty_asks=0)

    # PATH B: Atypical (non-optimal) — hidden symptoms, WITH gate cost
    # Hidden symptoms require 2 extra prerequisite ASK steps (gate unlocking)
    traj_b = build_trajectory(actions, task, pb_syms, "type 2 diabetes",
                              extra_empty_asks=2)

    # PATH C: FAILURE — confounder misled
    traj_c = build_trajectory(actions, task, misleading[:2], "hyperthyroidism",
                              drug="beta blocker", extra_empty_asks=0)

    ra = ev.evaluate(traj_a)
    rb = ev.evaluate(traj_b)
    rc = ev.evaluate(traj_c)

    print()
    print("=" * 60)
    print("PATH A: Classic (optimal) — no gate cost")
    print("=" * 60)
    print("  Collected: %s" % pa_syms)
    print("  ASK steps: %d (direct reveal)" % len(pa_syms))
    print("  total=%.4f  dx=%.1f  process=%.4f" % (
        ra["total"], ra["components"]["diagnosis"], ra["components"]["process"]))
    print("  pass=%s  errors=%s" % (ra["pass"], ra["errors"]))

    print()
    print("=" * 60)
    print("PATH B: Atypical (non-optimal) — 2 gate steps + 2 reveals")
    print("=" * 60)
    print("  Collected: %s" % pb_syms)
    print("  ASK steps: %d (2 gate + %d reveal)" % (
        2 + len(pb_syms), len(pb_syms)))
    print("  total=%.4f  dx=%.1f  process=%.4f" % (
        rb["total"], rb["components"]["diagnosis"], rb["components"]["process"]))
    print("  pass=%s  errors=%s" % (rb["pass"], rb["errors"]))

    print()
    print("=" * 60)
    print("PATH C: FAILURE (confounder misled)")
    print("=" * 60)
    print("  Collected: %s" % misleading[:2])
    print("  total=%.4f  dx=%.1f  process=%.4f" % (
        rc["total"], rc["components"]["diagnosis"], rc["components"]["process"]))
    print("  pass=%s  errors=%s" % (rc["pass"], rc["errors"]))

    print()
    print("=" * 60)
    print("KEY COMPARISONS")
    print("=" * 60)
    gap_ab = ra["components"]["process"] - rb["components"]["process"]
    print("  A vs B process gap: %+.4f (A optimal > B non-optimal)" % gap_ab)
    print("  A vs C total gap:   %.4f (success vs failure)" % (
        ra["total"] - rc["total"]))
    print("  Both A and B diagnose correctly: dx_A=%.1f  dx_B=%.1f" % (
        ra["components"]["diagnosis"], rb["components"]["diagnosis"]))
    print("  C diagnosed wrong: dx_C=%.1f" % rc["components"]["diagnosis"])

    # Verification
    a_correct = ra["components"]["diagnosis"] == 1.0
    b_correct = rb["components"]["diagnosis"] == 1.0
    c_wrong = rc["components"]["diagnosis"] == 0.0
    a_process_higher = gap_ab > 0

    print()
    all_pass = a_correct and b_correct and c_wrong and a_process_higher
    print("VERIFICATION: %s" % ("ALL PASS" if all_pass else "FAIL"))
    print("  Path A correct diagnosis:  %s" % ("OK" if a_correct else "FAIL"))
    print("  Path B correct diagnosis:  %s" % ("OK" if b_correct else "FAIL"))
    print("  Path C wrong diagnosis:    %s" % ("OK" if c_wrong else "FAIL"))
    print("  A process > B process:     %s (gap=%.4f)" % (
        "OK" if a_process_higher else "FAIL", gap_ab))

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
