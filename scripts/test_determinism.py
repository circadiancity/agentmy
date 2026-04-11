#!/usr/bin/env python3
"""
Determinism verification: generate_task(seed=X) twice → byte-identical JSON.

Tests:
1. Same seed → identical task JSON (byte-for-byte)
2. Different seeds → different tasks
3. reproducibility_hash matches between runs
4. No global random state pollution
"""

import sys
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from medical_task_suite.generation.v2.task_generation.task_generator import MedicalTaskGenerator
from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase


def test_byte_identical():
    """Same seed → byte-identical JSON output."""
    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    configs = [
        ("diagnostic_uncertainty", "L1", "type 2 diabetes", 42),
        ("conflicting_evidence", "L2", "hypertension", 123),
        ("treatment_tradeoff", "L3", "coronary artery disease", 999),
        ("drug_safety_risk", "L2", "heart failure", 7),
    ]

    all_pass = True
    for tt, diff, disease, seed in configs:
        t1 = gen.generate_task(tt, diff, target_disease=disease, seed=seed)
        t2 = gen.generate_task(tt, diff, target_disease=disease, seed=seed)

        j1 = json.dumps(t1, sort_keys=True, ensure_ascii=False)
        j2 = json.dumps(t2, sort_keys=True, ensure_ascii=False)

        if j1 != j2:
            print("  FAIL: %s/%s seed=%d — NOT byte-identical" % (disease, diff, seed))
            all_pass = False
        else:
            print("  PASS: %s/%s seed=%d — byte-identical" % (disease, diff, seed))

    return all_pass


def test_different_seeds():
    """Different seeds → different tasks."""
    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    t1 = gen.generate_task("diagnostic_uncertainty", "L2", target_disease="type 2 diabetes", seed=42)
    t2 = gen.generate_task("diagnostic_uncertainty", "L2", target_disease="type 2 diabetes", seed=99)

    # IDs should differ (hash includes seed)
    if t1["id"] == t2["id"]:
        print("  FAIL: different seeds produced same task ID")
        return False

    # Reproducibility hashes should differ
    h1 = t1["task_config"]["reproducibility_hash"]
    h2 = t2["task_config"]["reproducibility_hash"]
    if h1 == h2:
        print("  FAIL: different seeds produced same reproducibility_hash")
        return False

    print("  PASS: different seeds → different IDs and hashes")
    return True


def test_reproducibility_hash():
    """reproducibility_hash is populated and stable."""
    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    t1 = gen.generate_task("diagnostic_uncertainty", "L2", target_disease="copd", seed=42)
    t2 = gen.generate_task("diagnostic_uncertainty", "L2", target_disease="copd", seed=42)

    h1 = t1["task_config"]["reproducibility_hash"]
    h2 = t2["task_config"]["reproducibility_hash"]

    if not h1 or not h2:
        print("  FAIL: reproducibility_hash is empty or None")
        return False

    if h1 != h2:
        print("  FAIL: same seed → different reproducibility_hash (%s vs %s)" % (h1, h2))
        return False

    print("  PASS: reproducibility_hash stable (%s)" % h1)
    return True


def test_no_global_pollution():
    """Generating tasks does not pollute global random state."""
    # Set global random to known state
    random.seed(12345)
    state_before = random.getstate()

    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    # Generate a task (should NOT touch global random)
    gen.generate_task("diagnostic_uncertainty", "L2", target_disease="type 2 diabetes", seed=42)

    state_after = random.getstate()

    if state_before != state_after:
        print("  FAIL: global random state was modified by generate_task")
        return False

    print("  PASS: global random state unchanged after generate_task")
    return True


def main():
    print("=" * 60)
    print("DETERMINISM VERIFICATION")
    print("=" * 60)

    checks = [
        ("Byte-identical JSON (same seed)", test_byte_identical),
        ("Different seeds → different tasks", test_different_seeds),
        ("Reproducibility hash stable", test_reproducibility_hash),
        ("No global random pollution", test_no_global_pollution),
    ]

    results = []
    for label, fn in checks:
        print()
        print("TEST: %s" % label)
        passed = fn()
        results.append((label, passed))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = True
    for label, passed in results:
        status = "PASS" if passed else "FAIL"
        print("  %s  %s" % (status, label))
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("ALL DETERMINISM CHECKS PASSED")
    else:
        print("DETERMINISM CHECKS FAILED")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
