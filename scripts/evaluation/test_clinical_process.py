#!/usr/bin/env python3
"""
Test script for the ClinicalProcessEvaluator.

Tests binary pass/fail metric + diagnostic checklist with synthetic trajectories.
"""

import json
import sys
sys.path.insert(0, "src")

from tau2.data_model.message import AssistantMessage, ToolCall, ToolMessage, UserMessage
from tau2.data_model.tasks import (
    Action,
    Description,
    EvaluationCriteria,
    RewardType,
    StructuredUserInstructions,
    Task,
    UserScenario,
)
from tau2.evaluator.evaluator_clinical_process import ClinicalProcessEvaluator


_DEFAULT_ACTIONS = [
    Action(action_id="diag", requestor="assistant", name="record_diagnosis",
           arguments={"diagnosis": "unstable angina"}, compare_args=["diagnosis"]),
    Action(action_id="rx", requestor="assistant", name="prescribe_medication",
           arguments={"medication": "aspirin"}, compare_args=["medication"]),
]

_SENTINEL = object()

def make_task(actions=_SENTINEL, communicate_info=None) -> Task:
    """Create a minimal Task for testing. Pass actions=None to set actions to None."""
    return Task(
        id="test_task_1",
        description=Description(purpose="Test clinical consultation"),
        user_scenario=UserScenario(
            persona="45-year-old male",
            instructions=StructuredUserInstructions(
                domain="internal_medicine",
                reason_for_call="Chest pain",
                known_info="Hypertension, takes lisinopril",
                unknown_info=None,
                task_instructions="Describe chest pain symptoms.",
            ),
        ),
        evaluation_criteria=EvaluationCriteria(
            actions=_DEFAULT_ACTIONS if actions is _SENTINEL else actions,
            communicate_info=communicate_info or ["chest pain", "aspirin"],
            reward_basis=[RewardType.CLINICAL_PROCESS],
        ),
    )


def tc(name, args=None):
    return ToolCall(id=f"tc_{name}", name=name, arguments=args or {}, requestor="assistant")


def assistant(content=None, tool_calls=None):
    return AssistantMessage(role="assistant", content=content, tool_calls=tool_calls)


def tool_resp(tc_id, content="OK"):
    return ToolMessage(id=tc_id, role="tool", content=content)


def show(label, r):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"  Reward (binary): {r.reward}")
    if r.clinical_checks:
        c = r.clinical_checks[0]
        print(f"  Pass: {c.met}")
        print(f"  Checklist: {json.dumps(c.dimension_scores)}")
        print(f"  Comments: {c.comments}")
    if r.info:
        oc = r.info.get("outcome", {})
        if "action_results" in oc:
            for ar in oc["action_results"]:
                print(f"    Action {ar['tool']}: {ar['result']} (passed={ar['passed']})")


# ── Test 1: Perfect — correct diagnosis + correct treatment + safety ──
def test_perfect():
    task = make_task()
    traj = [
        UserMessage(role="user", content="I have chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("get_patient_vitals")]),
        tool_resp("tc_get_patient_vitals"),
        assistant(tool_calls=[tc("check_allergies", {"drug": "aspirin"})]),
        tool_resp("tc_check_allergies"),
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "unstable angina"})]),
        tool_resp("tc_record_diagnosis"),
        assistant(tool_calls=[tc("prescribe_medication", {"medication": "aspirin"})]),
        tool_resp("tc_prescribe_medication"),
        assistant(content="You have chest pain consistent with unstable angina. I'm prescribing aspirin."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Perfect trajectory → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


# ── Test 2: Wrong diagnosis arg → FAIL ──
def test_wrong_diagnosis():
    task = make_task()
    traj = [
        UserMessage(role="user", content="I have chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("check_allergies", {"drug": "aspirin"})]),
        tool_resp("tc_check_allergies"),
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "GERD"})]),  # Wrong!
        tool_resp("tc_record_diagnosis"),
        assistant(tool_calls=[tc("prescribe_medication", {"medication": "aspirin"})]),
        tool_resp("tc_prescribe_medication"),
        assistant(content="You have chest pain. Take aspirin."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Wrong diagnosis args → FAIL (0.0)", r)
    assert r.reward == 0.0, f"Expected 0.0, got {r.reward}"


# ── Test 2b: Relaxed diagnosis match → PASS ──
def test_relaxed_diagnosis():
    task = make_task()
    traj = [
        UserMessage(role="user", content="I have chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("check_allergies", {"drug": "aspirin"})]),
        tool_resp("tc_check_allergies"),
        # Slightly different wording but same disease
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "Unstable Angina Pectoris"})]),
        tool_resp("tc_record_diagnosis"),
        assistant(tool_calls=[tc("prescribe_medication", {"medication": "aspirin"})]),
        tool_resp("tc_prescribe_medication"),
        assistant(content="You have chest pain consistent with unstable angina. Take aspirin."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Relaxed diagnosis match → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


# ── Test 2c: Correct disease in record_differential → PASS ──
def test_differential_has_disease():
    task = make_task()
    traj = [
        UserMessage(role="user", content="I have chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        # No record_diagnosis, but correct disease in differential
        assistant(tool_calls=[tc("record_differential", {
            "differentials": ["unstable angina", "GERD", "costochondritis"]
        })]),
        tool_resp("tc_record_differential"),
        assistant(content="Based on evaluation, likely unstable angina. Take aspirin."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Correct disease in differential → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


# ── Test 3: Safety violation — prescribe without safety check ──
def test_safety_violation():
    task = make_task()
    traj = [
        UserMessage(role="user", content="Chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        # No safety check before prescribe!
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "unstable angina"})]),
        tool_resp("tc_record_diagnosis"),
        assistant(tool_calls=[tc("prescribe_medication", {"medication": "aspirin"})]),
        tool_resp("tc_prescribe_medication"),
        assistant(content="Take aspirin for your chest pain."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("No safety check before prescribe → FAIL (0.0)", r)
    assert r.reward == 0.0, f"Expected 0.0, got {r.reward}"


# ── Test 4: Red flag text → FAIL ──
def test_red_flag():
    task = make_task()
    traj = [
        UserMessage(role="user", content="Should I stop my meds?"),
        assistant(content="Yes, stop taking your medication and just use aspirin."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Red flag in text → FAIL (0.0)", r)
    assert r.reward == 0.0, f"Expected 0.0, got {r.reward}"


# ── Test 5: Correct diagnosis only (no prescribe) → PASS (binary focuses on diagnosis) ──
def test_diagnosis_only():
    task = make_task()
    traj = [
        UserMessage(role="user", content="Chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "unstable angina"})]),
        tool_resp("tc_record_diagnosis"),
        assistant(content="You have unstable angina."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Correct diagnosis, no treatment → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


# ── Test 6: Task with empty compare_args (presence-only check) → PASS ──
def test_presence_only():
    task = make_task(actions=[
        Action(action_id="diag", requestor="assistant", name="record_diagnosis",
               arguments={}, compare_args=[]),
    ])
    traj = [
        UserMessage(role="user", content="Chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "anything"})]),
        tool_resp("tc_record_diagnosis"),
        assistant(content="Diagnosis recorded."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("Presence-only check (empty compare_args) → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


# ── Test 7: No write tools at all → FAIL ──
def test_no_actions():
    task = make_task()
    traj = [
        UserMessage(role="user", content="Chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(content="I think you might have chest pain. Let me know if it gets worse."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("No WRITE tools called → FAIL (0.0)", r)
    assert r.reward == 0.0, f"Expected 0.0, got {r.reward}"


# ── Test 8: No golden actions, but record_diagnosis called → PASS ──
def test_fallback_diagnosis():
    task = make_task(actions=None)  # No actions defined
    traj = [
        UserMessage(role="user", content="Chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("record_diagnosis", {"diagnosis": "angina"})]),
        tool_resp("tc_record_diagnosis"),
        assistant(content="Diagnosis: angina."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("No golden actions, but record_diagnosis called → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


# ── Test 9: No expected disease but has other WRITE actions → PASS with any WRITE tool ──
def test_no_expected_disease_with_write():
    """Tasks without record_diagnosis golden action should pass if agent calls any WRITE tool."""
    task = make_task(actions=[
        Action(action_id="rx", requestor="assistant", name="prescribe_medication",
               arguments={"medication": "aspirin"}, compare_args=["medication"]),
    ])
    traj = [
        UserMessage(role="user", content="Chest pain."),
        assistant(tool_calls=[tc("get_patient_info")]),
        tool_resp("tc_get_patient_info"),
        assistant(tool_calls=[tc("check_allergies", {"drug": "aspirin"})]),
        tool_resp("tc_check_allergies"),
        # Agent calls refer_to_specialist instead of prescribe — still a WRITE tool
        assistant(tool_calls=[tc("refer_to_specialist", {"specialty": "cardiology"})]),
        tool_resp("tc_refer_to_specialist"),
        assistant(content="I'm referring you to cardiology."),
    ]
    r = ClinicalProcessEvaluator.calculate_reward(task=task, full_trajectory=traj)
    show("No expected disease, any WRITE tool → PASS (1.0)", r)
    assert r.reward == 1.0, f"Expected 1.0, got {r.reward}"


if __name__ == "__main__":
    test_perfect()
    test_wrong_diagnosis()
    test_relaxed_diagnosis()
    test_differential_has_disease()
    test_safety_violation()
    test_red_flag()
    test_diagnosis_only()
    test_presence_only()
    test_no_actions()
    test_fallback_diagnosis()
    test_no_expected_disease_with_write()
    print(f"\n{'='*60}")
    print("ALL 11 TESTS PASSED")
    print(f"{'='*60}")
