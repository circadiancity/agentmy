#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate a rule-based agent on 3 tasks to verify confounder dominance works.

Strategy: ASK(open) → ASK(targeted) → ORDER_LAB → GET_RESULTS → DIAGNOSE

Success criteria:
  - At least 1 task score < 0.7
  - At least 1 task diagnosis WRONG
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from medical_task_suite.generation.v2.task_generation.task_generator import MedicalTaskGenerator
from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator


# ============================================================
# Pseudo-Simulator: interprets task JSON update_rules
# ============================================================

class PseudoSimulator:
    """Simulates environment responses for a rule-based agent trajectory."""

    def __init__(self, task: dict):
        self.task = task
        self.symptoms = task["patient"]["symptoms"]
        self.ground_truth = task["ground_truth"]
        self.clinical = task["clinical"]
        self.actions = task["actions"]

        # Internal state
        self.revealed = set()
        self.gate_state = {}   # symptom → 'init' | 'unlocked' | 'locked'
        self.miss_count = {}   # symptom → int
        self.turn = 0
        self.consecutive_global_miss = 0

        # Extract confounder and true symptom sets
        self.confounder_symptoms = set(s.lower() for s in self.symptoms.get("misleading", []))
        self.volunteer = [s.lower() for s in self.symptoms.get("volunteer", [])]
        self.if_asked = [s.lower() for s in self.symptoms.get("if_asked", [])]
        self.hidden = [s.lower() for s in self.symptoms.get("hidden", [])]
        self.resistant = [s.lower() for s in self.symptoms.get("resistant", [])]

        # Relevant = volunteer + if_asked (true symptoms agent should discover)
        self.relevant = set(self.volunteer + self.if_asked)

        # Initialize gate states for all gated symptoms
        for s in self.if_asked + self.hidden + self.resistant:
            self.gate_state[s] = "init"
            self.miss_count[s] = 0

    def step(self, action_name: str, question_content: str = "") -> dict:
        """Execute one action, return observation."""
        self.turn += 1
        obs = {}

        if action_name == "ASK":
            obs = self._simulate_ask(question_content)
        elif action_name == "ORDER_LAB":
            obs = self._simulate_order_lab()
        elif action_name == "GET_RESULTS":
            obs = self._simulate_get_results()
        elif action_name == "DIAGNOSE":
            obs = self._simulate_diagnose()
        elif action_name == "CHECK_ALLERGY":
            obs = {"allergies": self.clinical.get("allergies", [])}
        elif action_name == "CHECK_INTERACTION":
            obs = {"interactions": "none found"}
        elif action_name == "PRESCRIBE":
            obs = {"drug": "metformin"}
        elif action_name == "END":
            obs = {"done": True}

        return obs

    def _simulate_ask(self, question_content: str) -> dict:
        """Simulate ASK action with confounder dominance + revelation gates."""
        q = question_content.lower()
        revealed_this_step = []

        # ── RULE 1: Volunteer symptoms (no gate) ──
        for s in self.volunteer:
            if s not in self.revealed:
                # Volunteer symptoms always revealed on first ASK
                if self.turn <= 1 or any(kw in q for kw in s.split()):
                    revealed_this_step.append(s)
                    self.revealed.add(s)

        # ── RULE 2: CONFOUNDER DOMINANCE (turn <= 2) ──
        if self.turn <= 2:
            # Confounder symptoms: HIGH priority
            for s in list(self.confounder_symptoms):
                if s not in self.revealed:
                    conf_keywords = s.split()
                    if any(kw in q for kw in conf_keywords):
                        revealed_this_step.append(s)
                        self.revealed.add(s)
                        self.consecutive_global_miss = 0

            # True hidden symptoms: SUPPRESSED during early stage
            # (do NOT reveal any if_asked/hidden/resistant on turn <= 2)
            return {"symptoms_revealed": revealed_this_step}

        # ── RULE 3: turn > 2 — TRUE_SIGNAL_UNLOCK ──
        # Check REVELATION_GATES for if_asked symptoms
        for s in list(self.if_asked):
            if s in self.revealed:
                continue
            if self.gate_state.get(s) == "locked":
                continue

            # Check if question matches this symptom
            sym_keywords = [w for w in s.split() if len(w) >= 3]
            matches_symptom = any(kw in q for kw in sym_keywords) if sym_keywords else s in q

            if matches_symptom:
                if self.gate_state.get(s) == "unlocked":
                    # Reveal!
                    revealed_this_step.append(s)
                    self.revealed.add(s)
                    self.consecutive_global_miss = 0
                else:
                    # Not unlocked — miss
                    self.miss_count[s] = self.miss_count.get(s, 0) + 1
                    if self.miss_count[s] >= 2:
                        self.gate_state[s] = "locked"

        # Check hidden symptoms (also gated)
        for s in list(self.hidden):
            if s in self.revealed:
                continue
            if self.gate_state.get(s) == "locked":
                continue

            sym_keywords = [w for w in s.split() if len(w) >= 3]
            matches_symptom = any(kw in q for kw in sym_keywords) if sym_keywords else s in q

            if matches_symptom:
                if self.gate_state.get(s) == "unlocked":
                    revealed_this_step.append(s)
                    self.revealed.add(s)
                    self.consecutive_global_miss = 0
                else:
                    self.miss_count[s] = self.miss_count.get(s, 0) + 1
                    if self.miss_count[s] >= 2:
                        self.gate_state[s] = "locked"

        return {"symptoms_revealed": revealed_this_step}

    def _simulate_order_lab(self) -> dict:
        return {}

    def _simulate_get_results(self) -> dict:
        return {"lab_results": self.clinical.get("labs", {})}

    def _simulate_diagnose(self) -> dict:
        return {"diagnosis": "pending"}

    def get_agent_diagnosis(self) -> str:
        """Rule-based agent picks diagnosis based on earliest prominent symptom cluster.

        Realistic behavior: agent forms early hypothesis from first symptoms seen,
        which are confounder-biased. Only revises if labs clearly contradict.

        Rules (deterministic):
        1. Collect all symptoms seen before DIAGNOSE
        2. If any confounder disease explains ≥2 of the seen symptoms → diagnose confounder
        3. Else pick first acceptable alternative or primary
        """
        primary = self.ground_truth.get("correct_diagnosis", {}).get("primary", "")
        confounders_raw = self.clinical.get("confounders", [])

        # Check if any confounder explains ≥2 symptoms the agent saw
        for conf in confounders_raw:
            if not isinstance(conf, dict):
                continue
            conf_name = conf["name"]
            overlapping = [s for s in conf.get("overlapping_symptoms", [])]
            # Count how many overlapping symptoms match what agent saw
            matched = 0
            for overlap_sym in overlapping:
                for revealed_sym in self.revealed:
                    if overlap_sym.lower() in revealed_sym.lower() or revealed_sym.lower() in overlap_sym.lower():
                        matched += 1
                        break
            # Also check volunteer symptoms (these ARE confounder-front-loaded)
            for vol_sym in self.volunteer:
                # weight loss matches hyperthyroidism, chest pain matches musculoskeletal, etc.
                for overlap_sym in overlapping:
                    if overlap_sym.lower() in vol_sym.lower() or vol_sym.lower() in overlap_sym.lower():
                        matched += 1
                        break

            if matched >= 2:
                return conf_name  # Agent misled by confounder

        # Fallback: pick first differential
        differentials = self.ground_truth.get("correct_diagnosis", {}).get("acceptable_alternatives", [])
        if differentials:
            return differentials[0]

        return primary


# ============================================================
# Rule-based Agent
# ============================================================

def run_rule_based(task: dict) -> tuple:
    """
    Run rule-based strategy: ASK(open) → ASK(targeted) → ORDER_LAB → GET_RESULTS → DIAGNOSE
    Returns (trajectory, step_log)
    """
    sim = PseudoSimulator(task)
    actions = task["actions"]
    trajectory = []
    step_log = []
    t = 0

    def do_step(action_name, question=""):
        nonlocal t
        action_id = actions[action_name]["id"]
        obs = sim.step(action_name, question)

        # Override diagnosis in observation for DIAGNOSE
        if action_name == "DIAGNOSE":
            agent_dx = sim.get_agent_diagnosis()
            obs["diagnosis"] = agent_dx
        if action_name == "PRESCRIBE":
            # Pick first treatment requirement or fallback
            treatment_req = task["ground_truth_validation"].get("treatment_required", [])
            if treatment_req:
                target = treatment_req[0].get("target", "metformin")
                obs["drug"] = target if not target.startswith("any_") else "metformin"

        done = action_name == "END"
        trajectory.append({
            "t": t,
            "action": action_id,
            "observation": obs,
            "reward": None,
            "done": done,
        })

        # Log
        revealed = obs.get("symptoms_revealed", [])
        dx = obs.get("diagnosis", "")
        lab = obs.get("lab_results", {})
        drug = obs.get("drug", "")
        log_parts = [f"  turn {t}: {action_name}"]
        if question:
            log_parts.append(f'    question: "{question}"')
        if revealed:
            log_parts.append(f"    → revealed: {revealed}")
        if lab:
            log_parts.append(f"    → lab_results: {list(lab.keys())}")
        if dx:
            log_parts.append(f"    → diagnosis: {dx}")
        if drug:
            log_parts.append(f"    → drug: {drug}")
        step_log.append("\n".join(log_parts))

        t += 1

    # ── Step 1: ASK(open_question) ──
    do_step("ASK", "what brings you in today?")

    # ── Step 2: ASK(targeted_question, "about your main symptoms") ──
    do_step("ASK", "tell me more about your symptoms")

    # ── Step 3: ORDER_LAB ──
    do_step("ORDER_LAB")

    # ── Step 4: GET_RESULTS ──
    do_step("GET_RESULTS")

    # ── Step 5: DIAGNOSE ──
    do_step("DIAGNOSE")

    # ── Step 6: CHECK_ALLERGY ──
    do_step("CHECK_ALLERGY")

    # ── Step 7: PRESCRIBE ──
    do_step("PRESCRIBE")

    # ── Step 8: END ──
    do_step("END")

    return trajectory, step_log


# ============================================================
# Main
# ============================================================

def main():
    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    test_cases = [
        ("diagnostic_uncertainty", "L2", "type 2 diabetes"),
        ("diagnostic_uncertainty", "L2", "coronary artery disease"),
        ("diagnostic_uncertainty", "L2", "copd"),
    ]

    results = []
    all_pass = True

    for task_type, difficulty, disease in test_cases:
        task = gen.generate_task(task_type, difficulty, target_disease=disease, seed=42)
        evaluator = BenchEvaluator(task)

        # Run rule-based agent
        trajectory, step_log = run_rule_based(task)
        result = evaluator.evaluate(trajectory)

        primary_dx = task["ground_truth"]["correct_diagnosis"]["primary"]
        agent_dx = None
        for step in trajectory:
            if step["observation"].get("diagnosis"):
                agent_dx = step["observation"]["diagnosis"]
                break

        correct = agent_dx and (agent_dx.lower() == primary_dx.lower() or
                                agent_dx.lower() in [d.lower() for d in
                                task["ground_truth"]["correct_diagnosis"].get("acceptable_alternatives", [])])

        print("=" * 70)
        print(f"TASK: {disease} ({difficulty})")
        print(f"Primary diagnosis: {primary_dx}")
        print(f"Confounders: {[c['name'] for c in task['clinical'].get('confounders', []) if isinstance(c, dict)]}")
        print(f"Volunteer symptoms: {task['patient']['symptoms']['volunteer']}")
        print(f"Misleading: {task['patient']['symptoms']['misleading']}")
        print(f"Hidden: {task['patient']['symptoms']['hidden']}")
        print("-" * 70)

        for log in step_log:
            print(log)

        print("-" * 70)
        print(f"Agent diagnosis: {agent_dx} ({'CORRECT' if correct else 'WRONG'})")
        print(f"Score: {result['total']:.4f}")
        print(f"  diagnosis:     {result['components']['diagnosis']}")
        print(f"  safety:        {result['components']['safety']}")
        print(f"  info:          {result['components']['info']}")
        print(f"  treatment:     {result['components']['treatment']}")
        print(f"  communication: {result['components']['communication']}")
        print(f"  process:       {result['components']['process']}")
        print(f"  pass:          {result['pass']}")
        print(f"  errors:        {result['errors']}")
        print()

        results.append({
            "disease": disease,
            "score": result["total"],
            "pass": result["pass"],
            "agent_dx": agent_dx,
            "correct": correct,
            "components": result["components"],
        })

    # ── Verification ──
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    n_below_07 = sum(1 for r in results if r["score"] < 0.7)
    n_wrong_dx = sum(1 for r in results if not r["correct"])

    print(f"Tasks with score < 0.7: {n_below_07}/3 {'✓ PASS' if n_below_07 >= 1 else '✗ FAIL'}")
    print(f"Tasks with wrong diagnosis: {n_wrong_dx}/3 {'✓ PASS' if n_wrong_dx >= 1 else '✗ FAIL'}")
    print()

    for r in results:
        dx_status = "WRONG" if not r["correct"] else "correct"
        score_status = "FAIL" if not r["pass"] else "PASS"
        print(f"  {r['disease']:30s} | score={r['score']:.3f} [{score_status}] | dx={r['agent_dx'][:25]:25s} [{dx_status}]")

    if n_below_07 >= 1 and n_wrong_dx >= 1:
        print("\n✓ ALL CRITERIA MET")
    else:
        print("\n✗ CRITERIA NOT MET — modifications needed")

    return n_below_07 >= 1 and n_wrong_dx >= 1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
