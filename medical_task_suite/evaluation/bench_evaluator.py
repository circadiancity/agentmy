#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark Evaluator — Executable scoring for medical task trajectories.

Takes a task JSON (from MedicalTaskGenerator) + an agent trajectory
and returns a concrete score dict.

Usage:
    from medical_task_suite.evaluation.bench_evaluator import BenchEvaluator

    evaluator = BenchEvaluator(task)
    result = evaluator.evaluate(trajectory)
    # result = {"total": 0.72, "components": {...}, "pass": True, "errors": [...]}
"""

from typing import Dict, List, Any, Optional
import math


class BenchEvaluator:
    """
    Executable evaluator that converts task JSON scoring spec into real scores.

    Input:
        task: dict — full task JSON from MedicalTaskGenerator
        trajectory: list of step dicts matching trajectory_schema:
            [{"t": 0, "action": 0, "observation": {...}, "reward": None, "done": False}, ...]

    Output:
        {"total": float, "components": {name: float}, "pass": bool, "errors": [str]}
    """

    def __init__(self, task: Dict):
        self.task = task
        self.scoring = task["scoring"]
        self.components_spec = self.scoring["components"]
        self.validation = task["ground_truth_validation"]
        self.gt = task["ground_truth"]
        self.patient = task["patient"]
        self.actions_spec = task["actions"]

    def evaluate(self, trajectory: List[Dict]) -> Dict[str, Any]:
        """Score a full agent trajectory against the task."""
        if not trajectory:
            return self._fail_result("empty trajectory")

        # Extract trajectory data
        actions_taken = [step.get("action") for step in trajectory]
        observations = [step.get("observation", {}) for step in trajectory]
        final_step = trajectory[-1]

        # Compute each component
        scores = {}
        errors = []

        # Detect path mixing (used by multiple components)
        revealed_set = self._get_revealed_symptoms_set(trajectory)
        path_mixing = self._is_path_mixing(revealed_set)

        scores["diagnosis"] = self._score_diagnosis(trajectory, path_mixing=path_mixing)
        scores["safety"] = self._score_safety(trajectory)
        scores["info"] = self._score_info(trajectory, path_mixing=path_mixing)
        scores["treatment"] = self._score_treatment(trajectory)
        scores["communication"] = self._score_communication(trajectory)
        scores["process"] = self._score_process(trajectory)

        # Collect errors
        errors = self._collect_errors(scores, trajectory)

        # Weighted sum with null exclusion
        total = self._weighted_sum(scores)

        # Critical failure check
        if self._check_critical_failure(scores, trajectory):
            total = 0.0

        # Global inconsistency penalty: path mixing degrades total
        if path_mixing:
            total -= 0.1

        # Efficiency adjustment
        n_turns = len(trajectory)
        max_turns = self.task["task_config"]["max_turns"]
        min_turns = self.task["task_config"]["min_turns"]
        total += self._efficiency_adjustment(n_turns, min_turns, max_turns)

        total = max(0.0, min(1.0, total))

        return {
            "total": round(total, 4),
            "components": {k: round(v, 4) if v is not None else None for k, v in scores.items()},
            "pass": total >= self.scoring["pass_threshold"],
            "errors": errors,
            "turns": n_turns,
        }

    # ============================================================
    # Component Scorers
    # ============================================================

    def _score_diagnosis(self, trajectory: List[Dict], path_mixing: bool = False) -> float:
        """set_match: check if agent diagnosis matches target or acceptable.

        Multi-path: diagnosis is correct if string matches AND
        agent collected sufficient evidence for ANY minimal_information_set.
        Lucky guess (correct string, no path satisfied) → 0.5.
        Path mixing: inconsistent evidence → cap at 0.5.
        """
        agent_diagnosis = self._extract_diagnosis(trajectory)
        if agent_diagnosis is None:
            return 0.0

        target = self.validation.get("diagnosis_target", [])
        acceptable = self.validation.get("diagnosis_acceptable", [])

        agent_lower = agent_diagnosis.lower().strip()

        # String match
        match_score = 0.0
        for t in target:
            if t.lower() in agent_lower or agent_lower in t.lower():
                match_score = 1.0
                break
        if match_score == 0.0:
            for a in acceptable:
                if a.lower() in agent_lower or agent_lower in a.lower():
                    match_score = 0.5
                    break

        if match_score == 0.0:
            return 0.0

        # Evidence check: must satisfy at least one minimal_information_set
        solution_space = self.gt.get("solution_space", {})
        minimal_sets = solution_space.get("derived_from", {}).get("minimal_information_sets", [])
        if not minimal_sets or isinstance(minimal_sets, dict):
            # Legacy format — no path constraint
            return match_score

        revealed = self._get_revealed_symptoms_set(trajectory)
        path_satisfied = False
        for path in minimal_sets:
            must_collect = path.get("must_collect", [])
            if not must_collect:
                continue
            collected = sum(1 for s in must_collect if s.lower() in revealed)
            # 70% threshold: agent must have found most symptoms in this path
            if collected >= max(1, len(must_collect) * 0.7):
                path_satisfied = True
                break

        if not path_satisfied:
            # Lucky guess — correct string but insufficient evidence
            return min(match_score, 0.5)

        # Path mixing: inconsistent evidence → cap diagnosis
        if path_mixing:
            return min(match_score, 0.5)

        return match_score

    def _score_safety(self, trajectory: List[Dict]) -> float:
        """rule_check: count untriggered safety rules / total safety rules."""
        safety_rules = self.validation.get("safety_rules", [])
        if not safety_rules:
            return 1.0

        action_names = self._extract_action_names(trajectory)
        has_prescribe = any(a == "PRESCRIBE" for a in action_names)
        has_allergy_check = any(a == "CHECK_ALLERGY" for a in action_names)

        violations = 0
        for rule in safety_rules:
            condition = rule.get("condition", "")
            if "allergy_check == false" in condition and has_prescribe and not has_allergy_check:
                violations += 1
            elif "contraindicated" in condition:
                # Check if agent prescribed a contraindicated drug
                # Simplified: if comorbidities exist and agent prescribed, check interaction
                if has_prescribe:
                    # Cannot fully verify without drug details — assume pass if interaction checked
                    has_interaction_check = any(a == "CHECK_INTERACTION" for a in action_names)
                    if not has_interaction_check:
                        violations += 1

        return max(0.0, 1.0 - violations / len(safety_rules))

    def _score_info(self, trajectory: List[Dict], path_mixing: bool = False) -> float:
        """count_ratio: revealed volunteer+if_asked / total volunteer+if_asked.

        Partial reveals count as 0.5 (degraded info).
        Full reveals count as 1.0.
        Path mixing: info contaminated → score × 0.6.
        """
        symptoms_spec = self.patient["symptoms"]
        relevant_symptoms = (
            symptoms_spec.get("volunteer", []) +
            symptoms_spec.get("if_asked", [])
        )
        if not relevant_symptoms:
            return 1.0

        # Build reveal map: symptom → quality ('full' or 'partial')
        reveal_quality = {}  # symptom_lower → 'full' | 'partial'
        for step in trajectory:
            obs = step.get("observation", {})
            # Check reveal_quality field (set by gate mechanism)
            quality = obs.get("reveal_quality", "full")
            for s in obs.get("symptoms_revealed", []):
                s_lower = s.lower()
                # If symptom text contains ':partial' marker, it's partial
                if ":partial" in s_lower:
                    s_clean = s_lower.split(":partial")[0].strip()
                    reveal_quality[s_clean] = "partial"
                elif s_lower not in reveal_quality:
                    reveal_quality[s_lower] = quality

        # Score: full=1.0, partial=0.5
        score = 0.0
        for s in relevant_symptoms:
            s_lower = s.lower()
            if s_lower in reveal_quality:
                if reveal_quality[s_lower] == "full":
                    score += 1.0
                else:
                    score += 0.5  # partial reveal

        raw = score / len(relevant_symptoms)
        # Path mixing: contaminated information → reduce
        if path_mixing:
            raw *= 0.6
        return raw

    def _score_treatment(self, trajectory: List[Dict]) -> Optional[float]:
        """required_done: prescribed required drugs / total required drugs."""
        treatment_required = self.validation.get("treatment_required", [])
        if not treatment_required:
            return None  # Exclude from sum, renormalize

        prescribed = self._extract_prescriptions(trajectory)
        done = 0
        for req in treatment_required:
            target = req.get("target", "")
            if target.startswith("any_appropriate_for_"):
                # Fallback rule: any prescription counts
                if prescribed:
                    done += 1
            else:
                for p in prescribed:
                    if target.lower() in p.lower():
                        done += 1
                        break

        return done / len(treatment_required)

    def _score_communication(self, trajectory: List[Dict]) -> float:
        """rule_check: communication milestones achieved / total."""
        comm_truth = self.gt.get("communication_truth", [])
        if not comm_truth:
            return 1.0

        # Check trajectory for EDUCATE actions and patient messages
        has_educate = any(self._action_id_to_name(step.get("action")) == "EDUCATE" for step in trajectory)
        has_followup = any(self._action_id_to_name(step.get("action")) == "SCHEDULE_FOLLOWUP" for step in trajectory)

        # Check if agent addressed diagnosis and treatment
        agent_messages = self._extract_agent_messages(trajectory)
        primary = self.gt.get("correct_diagnosis", {}).get("primary", "")

        achieved = 0
        for milestone in comm_truth:
            ms = milestone.get("milestone", "")
            if ms == "explain_diagnosis":
                # Did agent mention the diagnosis in messages?
                if any(primary.lower() in m.lower() for m in agent_messages):
                    achieved += 1
            elif ms == "explain_treatment":
                if has_educate or any("take" in m.lower() or "medication" in m.lower() for m in agent_messages):
                    achieved += 1
            elif ms == "address_concerns":
                # Did agent respond to patient concerns?
                patient_msgs = [obs.get("patient_message", "") for step in trajectory for obs in [step.get("observation", {})]]
                concern_keywords = ["worry", "concern", "afraid", "scared", "cost", "fear"]
                patient_has_concerns = any(any(kw in msg.lower() for kw in concern_keywords) for msg in patient_msgs if msg)
                if patient_has_concerns and has_educate:
                    achieved += 1
                elif not patient_has_concerns:
                    achieved += 1  # No concerns to address

        return achieved / len(comm_truth) if comm_truth else 1.0

    def _score_process(self, trajectory: List[Dict]) -> float:
        """Partially reversible, path-dependent scoring.

        Formula:
            process = relevance × 0.25 + gain × 0.35 + path_consistency × 0.2
                      - redundancy - misleading_penalty - delay_penalty
            Clipped to [0, 1].

        Mechanisms:
            trust_decay: irrelevant/repeated ASK → trust -= 0.05
                trust < 0.6 → noise contamination
                trust < 0.4 → info_value × 0.5 for all previously revealed
            diagnosis_lock: after DIAGNOSE, subsequent ASK gain × 0.3
                hidden symptoms after DIAGNOSE → value = 0.0
            path_consistency: mixing paths → penalty 0.2
        """
        ps = self.scoring.get("process_score", {})
        if not ps:
            return 0.5

        ask_steps = [s for s in trajectory if self._action_id_to_name(s.get("action")) == "ASK"]
        if not ask_steps:
            return 0.0

        # ── Find DIAGNOSE position for delay penalty ──
        diagnose_turn = None
        for step in trajectory:
            if self._action_id_to_name(step.get("action")) == "DIAGNOSE":
                diagnose_turn = step.get("t", None)
                break

        # ── 1. Build value-weighted symptom sets ──
        all_relevant = (
            self.patient["symptoms"].get("volunteer", []) +
            self.patient["symptoms"].get("if_asked", []) +
            self.patient["symptoms"].get("hidden", []) +
            self.patient["symptoms"].get("resistant", [])
        )
        relevant_set = set(s.lower() for s in all_relevant)
        misleading_set = set(s.lower() for s in self.patient["symptoms"].get("misleading", []))
        hidden_set = set(s.lower() for s in self.patient["symptoms"].get("hidden", []))

        # ── 2. Compute gain with trust decay + diagnosis lock ──
        trust = 1.0
        relevant_ask_count = 0
        gain_total = 0.0
        revealed_so_far = set()
        confounder_revealed = set()
        true_signal_revealed = set()
        # Track which symptoms were revealed AFTER diagnosis (for delay penalty)
        post_diagnosis_revealed = set()

        for s in ask_steps:
            obs = s.get("observation", {})
            revealed = obs.get("symptoms_revealed", [])
            quality = obs.get("reveal_quality", "full")
            step_turn = s.get("t", 0)
            is_post_diagnosis = diagnose_turn is not None and step_turn > diagnose_turn

            step_has_relevant = False
            for r in revealed:
                r_lower = r.lower()
                r_clean = r_lower.split(":partial")[0].strip() if ":partial" in r_lower else r_lower
                is_partial = ":partial" in r_lower or quality == "partial"
                reveal_factor = 0.5 if is_partial else 1.0

                info_value = self._get_information_value(r_clean)

                # DIAGNOSE lock: hidden symptoms after DIAGNOSE → value = 0
                if is_post_diagnosis and r_clean in hidden_set:
                    continue

                # DIAGNOSE lock: post-diagnosis gain × 0.3
                if is_post_diagnosis:
                    info_value *= 0.3
                    post_diagnosis_revealed.add(r_clean)

                # Trust decay: apply degraded factor
                if trust < 0.4:
                    info_value *= 0.5

                if r_clean in relevant_set and r_clean not in revealed_so_far:
                    gain_total += info_value * reveal_factor
                    revealed_so_far.add(r_clean)
                    step_has_relevant = True
                    true_signal_revealed.add(r_clean)

                if r_clean in misleading_set:
                    confounder_revealed.add(r_clean)

            # Trust decay: irrelevant ASK → trust -= 0.05
            if not step_has_relevant:
                trust = max(0.0, trust - 0.05)

            if step_has_relevant:
                relevant_ask_count += 1

        relevance_score = relevant_ask_count / len(ask_steps) if ask_steps else 0.0

        # ── 3. Gain ──
        gain_score = gain_total / len(ask_steps) if ask_steps else 0.0

        # ── 4. Misleading penalty ──
        misleading_penalty = 0.2 if len(confounder_revealed) > len(true_signal_revealed) else 0.0

        # ── 5. Path consistency ──
        path_consistency = self._compute_path_consistency(revealed_so_far)

        # ── 6. Delay penalty: ASK after DIAGNOSE ──
        delay_penalty = 0.05 * len(post_diagnosis_revealed) if post_diagnosis_revealed else 0.0

        # ── 7. Redundancy penalty ──
        symptom_ask_count = {}
        redundancy_penalty = 0.0

        for s in ask_steps:
            obs = s.get("observation", {})
            revealed = obs.get("symptoms_revealed", [])

            if revealed:
                for r in revealed:
                    r_lower = r.lower()
                    prev = symptom_ask_count.get(r_lower, 0)
                    symptom_ask_count[r_lower] = prev + 1
                    if prev >= 1:
                        redundancy_penalty += 0.1
            else:
                topic = obs.get("topic", "")
                if topic:
                    topic_lower = topic.lower()
                    prev = symptom_ask_count.get(topic_lower, 0)
                    symptom_ask_count[topic_lower] = prev + 1
                    if prev >= 1:
                        redundancy_penalty += 0.1

        # ── 8. Final score ──
        raw_score = (relevance_score * 0.25
                     + gain_score * 0.35
                     + path_consistency * 0.2
                     - redundancy_penalty
                     - misleading_penalty
                     - delay_penalty)
        return max(0.0, min(1.0, raw_score))

    # ============================================================
    # Helpers
    # ============================================================

    def _get_information_value(self, symptom_lower: str) -> float:
        """Derive information value from symptom tier (no external knowledge).

        hidden/resistant → 1.0 (critical)
        if_asked → 0.6 (supportive)
        volunteer → 0.3 (weak_signal)
        misleading/noise → 0.0 (noise)
        """
        symptoms = self.patient["symptoms"]

        for s in symptoms.get("hidden", []):
            if s.lower() == symptom_lower:
                return 1.0
        for s in symptoms.get("resistant", []):
            if s.lower() == symptom_lower:
                return 1.0
        for s in symptoms.get("if_asked", []):
            if s.lower() == symptom_lower:
                return 0.6
        for s in symptoms.get("volunteer", []):
            if s.lower() == symptom_lower:
                return 0.3
        return 0.0  # misleading or noise

    def _weighted_sum(self, scores: Dict[str, Optional[float]]) -> float:
        """Weighted sum excluding None components, renormalizing."""
        total_weight = 0.0
        weighted_sum = 0.0
        for name, spec in self.components_spec.items():
            w = spec["weight"]
            s = scores.get(name)
            if s is not None:
                total_weight += w
                weighted_sum += w * s

        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def _check_critical_failure(self, scores: Dict, trajectory: List[Dict]) -> bool:
        """Check if any critical failure rule is triggered."""
        cf = self.scoring.get("critical_failure", {})
        rules = cf.get("rules", [])

        for rule in rules:
            if "diagnosis_score == 0" in rule:
                if scores.get("diagnosis", 0) == 0:
                    return True
            if "prescribe_without_allergy_check" in rule:
                action_names = self._extract_action_names(trajectory)
                if "PRESCRIBE" in action_names and "CHECK_ALLERGY" not in action_names:
                    return True
            if "prescribe_contraindicated_for_" in rule:
                # Simplified: if prescribed without CHECK_INTERACTION and has comorbidities
                action_names = self._extract_action_names(trajectory)
                comorbidities = self.task["clinical"].get("comorbidities", [])
                if comorbidities and "PRESCRIBE" in action_names and "CHECK_INTERACTION" not in action_names:
                    return True

        return False

    def _get_revealed_symptoms_set(self, trajectory: List[Dict]) -> set:
        """Get all symptom names revealed during trajectory (lowercase, cleaned)."""
        revealed = set()
        for step in trajectory:
            obs = step.get("observation", {})
            for s in obs.get("symptoms_revealed", []):
                s_lower = s.lower()
                # Clean partial marker
                s_clean = s_lower.split(":partial")[0].strip() if ":partial" in s_lower else s_lower
                revealed.add(s_clean)
        return revealed

    def _is_path_mixing(self, revealed_so_far: set) -> bool:
        """Check if agent mixed symptoms from >1 minimal_information_set."""
        solution_space = self.gt.get("solution_space", {})
        minimal_sets = solution_space.get("derived_from", {}).get("minimal_information_sets", [])
        if not minimal_sets or isinstance(minimal_sets, dict):
            return False

        satisfied_count = 0
        for path in minimal_sets:
            must_collect = path.get("must_collect", [])
            if not must_collect:
                continue
            collected = sum(1 for s in must_collect if s.lower() in revealed_so_far)
            if collected >= max(1, len(must_collect) * 0.7):
                satisfied_count += 1

        return satisfied_count > 1

    def _compute_path_consistency(self, revealed_so_far: set) -> float:
        """Compute path consistency score (0.0 to 1.0).

        Rules:
        1. Identify which paths the agent satisfied (≥70% of must_collect)
        2. IF agent mixes >1 path → inconsistency_penalty = -0.2 → return 0.0
        3. IF agent uses non-optimal path only → return 0.5
        4. IF agent uses optimal path only → return 1.0
        5. IF no path satisfied → return 0.0
        """
        solution_space = self.gt.get("solution_space", {})
        minimal_sets = solution_space.get("derived_from", {}).get("minimal_information_sets", [])
        if not minimal_sets or isinstance(minimal_sets, dict):
            return 1.0  # Legacy format — no path constraint

        satisfied_paths = []
        for path in minimal_sets:
            must_collect = path.get("must_collect", [])
            if not must_collect:
                continue
            collected = sum(1 for s in must_collect if s.lower() in revealed_so_far)
            threshold = max(1, len(must_collect) * 0.7)
            if collected >= threshold:
                satisfied_paths.append(path)

        if len(satisfied_paths) > 1:
            # Path mixing penalty
            return 0.0
        elif len(satisfied_paths) == 1:
            if satisfied_paths[0].get("is_optimal", True):
                return 1.0
            else:
                return 0.5
        else:
            return 0.0

    def _efficiency_adjustment(self, turns: int, min_turns: int, max_turns: int) -> float:
        eff = self.scoring.get("efficiency", {})
        adjustment = 0.0
        if turns <= min_turns + 4:
            adjustment += 0.05
        elif turns > int(max_turns * 0.8):
            extra = turns - int(max_turns * 0.8)
            adjustment -= 0.02 * extra
        return adjustment

    def _collect_errors(self, scores: Dict, trajectory: List[Dict]) -> List[str]:
        """Map low scores to error codes."""
        errors = []
        error_taxonomy = self.task.get("error_taxonomy", [])
        code_map = {e["code"]: e for e in error_taxonomy}

        if scores.get("diagnosis", 0) == 0:
            errors.append("E01")
        if "PRESCRIBE" in self._extract_action_names(trajectory) and "CHECK_ALLERGY" not in self._extract_action_names(trajectory):
            errors.append("E02")
        if scores.get("info", 0) < 0.5:
            errors.append("E04")
        if scores.get("treatment") is not None and scores["treatment"] == 0:
            errors.append("E05")
        if scores.get("communication", 0) < 0.5:
            errors.append("E08")
        if len(trajectory) > self.task["task_config"]["max_turns"] * 0.8:
            errors.append("E09")

        return errors

    def _extract_diagnosis(self, trajectory: List[Dict]) -> Optional[str]:
        """Extract agent's final diagnosis from trajectory."""
        for step in reversed(trajectory):
            if self._action_id_to_name(step.get("action")) == "DIAGNOSE":
                obs = step.get("observation", {})
                if "diagnosis" in obs:
                    return obs["diagnosis"]
                # Try from action params
                if "params" in step:
                    return step["params"].get("diagnosis")
        return None

    def _extract_action_names(self, trajectory: List[Dict]) -> List[str]:
        """Convert action IDs to names."""
        return [self._action_id_to_name(s.get("action")) for s in trajectory]

    def _action_id_to_name(self, action_id) -> Optional[str]:
        """Map action ID (int) to name string."""
        if isinstance(action_id, str):
            return action_id
        if isinstance(action_id, int):
            for name, spec in self.actions_spec.items():
                if spec.get("id") == action_id:
                    return name
        return None

    def _extract_prescriptions(self, trajectory: List[Dict]) -> List[str]:
        """Extract all prescribed drugs from trajectory."""
        prescriptions = []
        for step in trajectory:
            if self._action_id_to_name(step.get("action")) == "PRESCRIBE":
                obs = step.get("observation", {})
                if "drug" in obs:
                    prescriptions.append(obs["drug"])
                if "params" in step and "drug" in step.get("params", {}):
                    prescriptions.append(step["params"]["drug"])
        return prescriptions

    def _extract_agent_messages(self, trajectory: List[Dict]) -> List[str]:
        """Extract agent's text messages from trajectory."""
        messages = []
        for step in trajectory:
            obs = step.get("observation", {})
            msg = obs.get("agent_message", "") or obs.get("message", "")
            if msg:
                messages.append(msg)
        return messages

    def _fail_result(self, reason: str) -> Dict:
        return {
            "total": 0.0,
            "components": {k: 0.0 for k in self.components_spec},
            "pass": False,
            "errors": [reason],
            "turns": 0,
        }
