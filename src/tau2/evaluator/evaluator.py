from enum import Enum

from tau2.data_model.simulation import RewardInfo, SimulationRun, TerminationReason
from tau2.data_model.tasks import RewardType, Task
from tau2.evaluator.evaluator_action import ActionEvaluator
from tau2.evaluator.evaluator_communicate import CommunicateEvaluator
from tau2.evaluator.evaluator_env import EnvironmentEvaluator
from tau2.evaluator.evaluator_nl_assertions import NLAssertionsEvaluator
from tau2.evaluator.evaluator_clinical import ClinicalEvaluator
from tau2.evaluator.evaluator_clinical_process import ClinicalProcessEvaluator
from tau2.evaluator.metrics.clinical_scoring import apply_clinical_gate
from tau2.registry import registry


class EvaluationType(str, Enum):
    ENV = "env"
    COMMUNICATE = "communicate"
    ACTION = "action"
    ALL = "all"
    NL_ASSERTIONS = "nl_assertions"  # WIP
    ALL_WITH_NL_ASSERTIONS = "all_with_nl_assertions"  # WIP
    CLINICAL = "clinical"  # 医疗/临床评估
    ALL_WITH_CLINICAL = "all_with_clinical"  # 包含医疗评估的综合评估
    ALL_WITH_CLINICAL_GATE = "all_with_clinical_gate"  # 临床评估使用门控阈值
    CLINICAL_PROCESS = "clinical_process"  # Rule-based clinical process evaluation


def evaluate_simulation(
    simulation: SimulationRun,
    task: Task,
    evaluation_type: EvaluationType,
    solo_mode: bool,
    domain: str,
    clinical_model: str = "gpt-4",
) -> RewardInfo:
    """
    Evaluate the simulation based on the evaluation type.
    """
    # For CLINICAL_PROCESS, evaluate even if max_steps was hit — the agent
    # may have completed the clinical workflow before running out of turns.
    if simulation.termination_reason not in {
        TerminationReason.AGENT_STOP,
        TerminationReason.USER_STOP,
    } and evaluation_type not in {
        EvaluationType.CLINICAL_PROCESS,
    }:
        return RewardInfo(
            reward=0.0,
            reward_basis=None,
            info={
                "note": f"Simulation terminated prematurely. Termination reason: {simulation.termination_reason.value}"
            },
        )
    if task.evaluation_criteria is None:
        return RewardInfo(
            reward=1.0,
            reward_basis=None,
            info={"note": "No evaluation criteria"},
        )
    if evaluation_type == EvaluationType.ENV:
        reward_info = EnvironmentEvaluator.calculate_reward(
            environment_constructor=registry.get_env_constructor(domain),
            task=task,
            full_trajectory=simulation.messages,
            solo_mode=solo_mode,
        )
    elif evaluation_type == EvaluationType.CLINICAL:
        # 医疗评估：使用 ClinicalEvaluator
        reward_info = ClinicalEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
            model=clinical_model,
        )
    elif evaluation_type == EvaluationType.CLINICAL_PROCESS:
        reward_info = ClinicalProcessEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
        )
    elif evaluation_type == EvaluationType.NL_ASSERTIONS:
        reward_info = NLAssertionsEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
        )
    elif evaluation_type == EvaluationType.COMMUNICATE:
        reward_info = CommunicateEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
        )
    elif evaluation_type == EvaluationType.ACTION:
        reward_info = ActionEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
        )
    elif evaluation_type in {
        EvaluationType.ALL,
        EvaluationType.ALL_WITH_NL_ASSERTIONS,
        EvaluationType.ALL_WITH_CLINICAL,
        EvaluationType.ALL_WITH_CLINICAL_GATE,
    }:
        env_reward_info = EnvironmentEvaluator.calculate_reward(
            environment_constructor=registry.get_env_constructor(domain),
            task=task,
            full_trajectory=simulation.messages,
            solo_mode=solo_mode,
        )
        action_reward_info = ActionEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
        )
        communicate_reward_info = CommunicateEvaluator.calculate_reward(
            task=task,
            full_trajectory=simulation.messages,
        )
        nl_reward_info = None
        if evaluation_type in {
            EvaluationType.ALL_WITH_NL_ASSERTIONS,
            EvaluationType.ALL_WITH_CLINICAL,
            EvaluationType.ALL_WITH_CLINICAL_GATE,
        }:
            nl_reward_info = NLAssertionsEvaluator.calculate_reward(
                task=task,
                full_trajectory=simulation.messages,
            )
        clinical_reward_info = None
        if evaluation_type in {
            EvaluationType.ALL_WITH_CLINICAL,
            EvaluationType.ALL_WITH_CLINICAL_GATE,
        }:
            clinical_reward_info = ClinicalEvaluator.calculate_reward(
                task=task,
                full_trajectory=simulation.messages,
                model=clinical_model,
            )

        ## Combine all the rewards.
        reward = 1.0
        env_bases = {RewardType.DB, RewardType.ENV_ASSERTION}
        action_bases = {RewardType.ACTION}
        nl_bases = {RewardType.NL_ASSERTION}
        comm_bases = {RewardType.COMMUNICATE}
        clinical_bases = {RewardType.CLINICAL}
        clinical_process_bases = {RewardType.CLINICAL_PROCESS}
        task_reward_basis = set(task.evaluation_criteria.reward_basis)

        reward_breakdown = {}
        if task_reward_basis & env_bases:
            if env_reward_info.reward_breakdown is not None:
                reward_breakdown.update(env_reward_info.reward_breakdown)
            reward *= env_reward_info.reward
        if task_reward_basis & action_bases:
            if action_reward_info.reward_breakdown is not None:
                reward_breakdown.update(action_reward_info.reward_breakdown)
            reward *= action_reward_info.reward
        if task_reward_basis & nl_bases:
            if nl_reward_info is None:
                raise ValueError(
                    "NL assertions are part of the reward basis, but they are not being evaluated. "
                    "Use ALL_WITH_NL_ASSERTIONS, ALL_WITH_CLINICAL, or ALL_WITH_CLINICAL_GATE."
                )
            if nl_reward_info.reward_breakdown is not None:
                reward_breakdown.update(nl_reward_info.reward_breakdown)
            reward *= nl_reward_info.reward
        if task_reward_basis & comm_bases:
            if communicate_reward_info.reward_breakdown is not None:
                reward_breakdown.update(communicate_reward_info.reward_breakdown)
            reward *= communicate_reward_info.reward
        if task_reward_basis & clinical_bases:
            if clinical_reward_info is None:
                raise ValueError(
                    "Clinical evaluation is part of the reward basis, but it is not being evaluated. "
                    "Use ALL_WITH_CLINICAL or ALL_WITH_CLINICAL_GATE."
                )
            if evaluation_type == EvaluationType.ALL_WITH_CLINICAL_GATE:
                # Apply 3-value gate: >= 3.0 → 1.0, >= 2.0 → 0.5, < 2.0 → 0.0
                raw_score = _get_clinical_raw_score(clinical_reward_info)
                gated_reward = apply_clinical_gate(raw_score)
                reward_breakdown[RewardType.CLINICAL] = gated_reward
                reward *= gated_reward
            else:
                if clinical_reward_info.reward_breakdown is not None:
                    reward_breakdown.update(clinical_reward_info.reward_breakdown)
                reward *= clinical_reward_info.reward
        if task_reward_basis & clinical_process_bases:
            clinical_process_reward_info = ClinicalProcessEvaluator.calculate_reward(
                task=task,
                full_trajectory=simulation.messages,
            )
            if clinical_process_reward_info.reward_breakdown is not None:
                reward_breakdown.update(clinical_process_reward_info.reward_breakdown)
            reward *= clinical_process_reward_info.reward

        reward_info = RewardInfo(
            reward=reward,
            db_check=env_reward_info.db_check,
            env_assertions=env_reward_info.env_assertions,
            action_checks=action_reward_info.action_checks,
            nl_assertions=nl_reward_info.nl_assertions
            if nl_reward_info is not None
            else None,
            communicate_checks=communicate_reward_info.communicate_checks,
            clinical_checks=clinical_reward_info.clinical_checks
            if clinical_reward_info is not None
            else None,
            reward_basis=task.evaluation_criteria.reward_basis,
            reward_breakdown=reward_breakdown,
            info={
                "env": env_reward_info.info,
                "nl": nl_reward_info.info if nl_reward_info is not None else None,
                "communicate": communicate_reward_info.info,
                "action": action_reward_info.info,
                "clinical": clinical_reward_info.info if clinical_reward_info is not None else None,
            },
        )
    else:
        raise ValueError(f"Unknown evaluation type: {evaluation_type}")
    return reward_info


def _get_clinical_raw_score(clinical_reward_info: RewardInfo) -> float:
    """Extract the raw 0-5 clinical score from a ClinicalEvaluator RewardInfo.

    The ClinicalEvaluator normalizes the score to 0-1 (score / 5.0).
    We reverse this to get the original 0-5 scale for the gate.
    If clinical_checks are available, use the overall_score directly.
    """
    if clinical_reward_info.clinical_checks:
        return clinical_reward_info.clinical_checks[0].overall_score
    # Fallback: reverse the normalization
    return clinical_reward_info.reward * 5.0
