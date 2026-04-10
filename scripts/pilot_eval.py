#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pilot evaluation: run baseline agents on generated tasks using BenchEvaluator.

Tests:
1. BenchEvaluator works on synthetic trajectories
2. Random agent scores low, rule-based scores higher
3. Discrimination between agents is measurable
"""

import json
import sys
import random
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from medical_task_suite.generation.v2.task_generation.task_generator import MedicalTaskGenerator
from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator


def generate_random_trajectory(task: dict, rng: random.Random) -> list:
    """Random agent: picks random actions each turn."""
    actions = task["actions"]
    action_list = list(actions.keys())
    max_turns = task["task_config"]["max_turns"]
    n_turns = rng.randint(3, min(12, max_turns))

    trajectory = []
    disease = task["ground_truth"]["correct_diagnosis"]["primary"]
    symptoms = task["patient"]["symptoms"]
    volunteer = symptoms.get("volunteer", [])
    if_asked = symptoms.get("if_asked", [])
    labs = list(task["clinical"]["labs"].keys()) if task["clinical"]["labs"] else []

    for t in range(n_turns):
        action_name = rng.choice(action_list)
        obs = {}

        if action_name == "ASK":
            # Random question — might or might not reveal symptoms
            pool = volunteer + if_asked
            if pool and rng.random() < 0.3:
                obs["symptoms_revealed"] = [rng.choice(pool)]
            else:
                obs["symptoms_revealed"] = []

        elif action_name == "ORDER_LAB" and labs:
            obs["lab_ordered"] = rng.choice(labs)

        elif action_name == "GET_RESULTS" and labs:
            obs["lab_results"] = {rng.choice(labs): "some value"}

        elif action_name == "DIAGNOSE":
            # Random diagnosis — likely wrong
            wrong_diagnoses = ["common cold", "flu", "stress", "viral infection", "fatigue"]
            obs["diagnosis"] = rng.choice(wrong_diagnoses)

        elif action_name == "CHECK_ALLERGY":
            obs["allergies"] = task["clinical"].get("allergies", [])

        elif action_name == "PRESCRIBE":
            obs["drug"] = rng.choice(["aspirin", "ibuprofen", "paracetamol", "antibiotics"])

        elif action_name == "EDUCATE":
            obs["agent_message"] = "Take your medication as prescribed."

        elif action_name == "SCHEDULE_FOLLOWUP":
            obs["done"] = True

        trajectory.append({
            "t": t,
            "action": actions[action_name]["id"],
            "observation": obs,
            "reward": None,
            "done": t == n_turns - 1,
        })

    return trajectory


def generate_rulebased_trajectory(task: dict) -> list:
    """Rule-based agent: fixed sequence ASK→ORDER_LAB→GET_RESULTS→DIAGNOSE→CHECK_ALLERGY→PRESCRIBE→EDUCATE→END."""
    actions = task["actions"]
    disease = task["ground_truth"]["correct_diagnosis"]["primary"]
    symptoms = task["patient"]["symptoms"]
    volunteer = symptoms.get("volunteer", [])
    if_asked = symptoms.get("if_asked", [])
    labs = list(task["clinical"]["labs"].keys()) if task["clinical"]["labs"] else []
    treatment_required = task["ground_truth_validation"].get("treatment_required", [])

    trajectory = []
    t = 0

    # Phase 1: ASK questions (3-5 turns)
    ask_pool = list(set(volunteer + if_asked))
    n_asks = min(len(ask_pool) + 1, 5)
    revealed = []
    for i in range(n_asks):
        obs = {"symptoms_revealed": []}
        if i < len(ask_pool):
            obs["symptoms_revealed"] = [ask_pool[i]]
            revealed.append(ask_pool[i])

        trajectory.append({
            "t": t, "action": actions["ASK"]["id"],
            "observation": obs, "reward": None, "done": False,
        })
        t += 1

    # Phase 2: ORDER_LAB
    if labs:
        trajectory.append({
            "t": t, "action": actions["ORDER_LAB"]["id"],
            "observation": {}, "reward": None, "done": False,
        })
        t += 1

        # Phase 3: GET_RESULTS
        lab_results = {}
        for lab_name, lab_val in task["clinical"]["labs"].items():
            lab_results[lab_name] = lab_val
        trajectory.append({
            "t": t, "action": actions["GET_RESULTS"]["id"],
            "observation": {"lab_results": lab_results}, "reward": None, "done": False,
        })
        t += 1

    # Phase 4: DIAGNOSE
    trajectory.append({
        "t": t, "action": actions["DIAGNOSE"]["id"],
        "observation": {"diagnosis": disease}, "reward": None, "done": False,
    })
    t += 1

    # Phase 5: CHECK_ALLERGY
    trajectory.append({
        "t": t, "action": actions["CHECK_ALLERGY"]["id"],
        "observation": {"allergies": task["clinical"].get("allergies", [])}, "reward": None, "done": False,
    })
    t += 1

    # Phase 6: CHECK_INTERACTION (if comorbidities)
    comorbidities = task["clinical"].get("comorbidities", [])
    if comorbidities:
        trajectory.append({
            "t": t, "action": actions["CHECK_INTERACTION"]["id"],
            "observation": {"interactions": "none found"}, "reward": None, "done": False,
        })
        t += 1

    # Phase 7: PRESCRIBE
    drug = "metformin"  # Generic fallback
    if treatment_required:
        target = treatment_required[0].get("target", "")
        if not target.startswith("any_appropriate"):
            drug = target
    obs = {"drug": drug}
    trajectory.append({
        "t": t, "action": actions["PRESCRIBE"]["id"],
        "observation": obs, "reward": None, "done": False,
    })
    t += 1

    # Phase 8: EDUCATE
    trajectory.append({
        "t": t, "action": actions["EDUCATE"]["id"],
        "observation": {"agent_message": f"You have {disease}. This is a condition that requires ongoing management. Let me explain your treatment plan."}, "reward": None, "done": False,
    })
    t += 1

    # Phase 9: END
    trajectory.append({
        "t": t, "action": actions["END"]["id"],
        "observation": {"done": True}, "reward": None, "done": True,
    })

    return trajectory


def run_pilot(n_tasks=18, seed=42):
    """Run pilot evaluation with random and rule-based agents."""
    print("=" * 60)
    print("PILOT EVALUATION")
    print("=" * 60)

    # Initialize KB and generator
    from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    # Generate tasks
    print(f"\nGenerating {n_tasks} tasks...")
    tasks = gen.generate_batch(n=n_tasks, seed=seed)
    print(f"Generated {len(tasks)} tasks successfully")

    # Evaluate with both agents
    rng = random.Random(seed)
    results = {"random": [], "rule_based": []}

    for i, task in enumerate(tasks):
        task_id = task["id"][:50]
        evaluator = BenchEvaluator(task)

        # Random agent
        rand_traj = generate_random_trajectory(task, rng)
        rand_result = evaluator.evaluate(rand_traj)
        results["random"].append({"task_id": task_id, **rand_result})

        # Rule-based agent
        rb_traj = generate_rulebased_trajectory(task)
        rb_result = evaluator.evaluate(rb_traj)
        results["rule_based"].append({"task_id": task_id, **rb_result})

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    for agent_name in ["random", "rule_based"]:
        scores = results[agent_name]
        totals = [s["total"] for s in scores]
        passes = [s["pass"] for s in scores]
        avg = sum(totals) / len(totals) if totals else 0
        pass_rate = sum(passes) / len(passes) if passes else 0

        print(f"\n{agent_name.upper()} AGENT ({len(scores)} tasks):")
        print(f"  Mean score:  {avg:.3f}")
        print(f"  Min score:   {min(totals):.3f}")
        print(f"  Max score:   {max(totals):.3f}")
        print(f"  Pass rate:   {pass_rate:.1%}")

        # Component breakdown
        components = {}
        for s in scores:
            for k, v in s["components"].items():
                if v is not None:
                    components.setdefault(k, []).append(v)
        print(f"  Components:")
        for k, vals in components.items():
            print(f"    {k}: {sum(vals)/len(vals):.3f}")

        # Error breakdown
        all_errors = []
        for s in scores:
            all_errors.extend(s["errors"])
        if all_errors:
            from collections import Counter
            error_counts = Counter(all_errors)
            print(f"  Errors: {dict(error_counts)}")

    # Discrimination check
    rand_avg = sum(s["total"] for s in results["random"]) / len(results["random"])
    rb_avg = sum(s["total"] for s in results["rule_based"]) / len(results["rule_based"])
    gap = rb_avg - rand_avg

    print(f"\n{'=' * 60}")
    print(f"DISCRIMINATION GAP: {gap:.3f} (rule_based - random)")
    if gap > 0.15:
        print("  ✓ PASS — meaningful discrimination between agents")
    elif gap > 0.05:
        print("  ⚠ WEAK — some discrimination but may need calibration")
    else:
        print("  ✗ FAIL — no meaningful discrimination")

    # Write detailed results
    output_path = ROOT / "pilot_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "config": {"n_tasks": n_tasks, "seed": seed},
            "random_avg": rand_avg,
            "rule_based_avg": rb_avg,
            "gap": gap,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results → {output_path}")

    return results


if __name__ == "__main__":
    run_pilot()
