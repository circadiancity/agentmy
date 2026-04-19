#!/usr/bin/env python3
"""
Run generated_tasks_v3/all_tasks.json through tau2-bench.

Converts v3 task format to tau2 Task format, then runs via tau2 run_tasks().

Usage:
    # Run all 150 tasks
    python scripts/run_v3_tasks.py

    # Run first N tasks
    python scripts/run_v3_tasks.py --num-tasks 5

    # Use a specific model
    python scripts/run_v3_tasks.py --agent-llm azure/gpt-5.2 --num-tasks 3

    # Custom tasks file
    python scripts/run_v3_tasks.py --tasks-file /path/to/all_tasks.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from tau2.data_model.tasks import (
    Task, Description, UserScenario, StructuredUserInstructions,
    EvaluationCriteria, Action, RewardType, InitialState,
)
from tau2.evaluator.evaluator import EvaluationType
from tau2.evaluator.metrics.clinical_scoring import (
    DIFFICULTY_REWARD_BASIS,
    get_evaluation_template,
)
from tau2.run import run_tasks
from tau2.metrics.agent_metrics import compute_metrics
from tau2.utils.display import ConsoleDisplay

# Map v3 tool names to PrimeKG clinical tool names
_V3_TOOL_MAP = {
    "ask": "ASK",
    "order_lab": "ORDER_LAB",
    "get_results": "GET_RESULTS",
    "diagnose": "DIAGNOSE",
    "prescribe": "PRESCRIBE",
    "check_allergy": "CHECK_ALLERGY",
    "check_interaction": "CHECK_INTERACTION",
    "check_contraindication": "CHECK_CONTRAINDICATION",
    "educate": "EDUCATE",
    "schedule_followup": "SCHEDULE_FOLLOWUP",
    "refer": "REFER",
    "end": "END",
}


def convert_v3_to_tau2(v3_task: dict) -> Task:
    """Convert a v3 format task to a tau2 Task."""
    patient = v3_task["patient"]
    clinical = v3_task["clinical"]
    ground_truth = v3_task["ground_truth"]
    task_config = v3_task["task_config"]
    actions_spec = v3_task.get("actions", {})

    chief_complaint = patient["chief_complaint"]
    profile = patient["profile"]
    diagnosis = clinical["diagnosis"]["primary"]

    # Build user instructions from patient data
    persona = (
        f"{profile['age']}-year-old {profile['gender']} patient, "
        f"education: {profile.get('education', 'unknown')}, "
        f"occupation: {profile.get('occupation', 'unknown')}"
    )

    instructions = StructuredUserInstructions(
        domain=task_config.get("domain", "internal_medicine"),
        reason_for_call=chief_complaint,
        known_info=(
            f"Chief complaint: {chief_complaint}. "
            f"Vitals: {json.dumps(clinical.get('vitals', {}))}. "
            f"Current medications: {', '.join(clinical.get('medications', [])) or 'none'}. "
            f"Allergies: {', '.join(clinical.get('allergies', [])) or 'none'}."
        ),
        unknown_info=diagnosis,
        task_instructions=patient.get("instructions", f"You are a patient with {chief_complaint}. Answer the doctor's questions."),
    )

    user_scenario = UserScenario(
        persona=persona,
        instructions=instructions,
    )

    # Build evaluation criteria from ground truth + actions
    eval_actions = []

    # Add expected tool calls from actions spec, mapping to clinical tool names
    tool_sequence = actions_spec.get("tool_call_sequence", [])
    for i, tool_call in enumerate(tool_sequence):
        tool_name = tool_call if isinstance(tool_call, str) else tool_call.get("tool", "")
        # Normalize tool name via map
        tool_name = _V3_TOOL_MAP.get(tool_name.lower(), tool_name)
        args = {} if isinstance(tool_call, str) else tool_call.get("required_args", {})
        eval_actions.append(Action(
            action_id=f"tool_{i}_{tool_name}",
            requestor="assistant",
            name=tool_name,
            arguments=args,
            compare_args=list(args.keys()) if args else [],
        ))

    # NL assertions from ground truth communication milestones
    nl_assertions = []
    for comm in ground_truth.get("communication_truth", []):
        milestone = comm.get("milestone", "")
        must_include = comm.get("must_include", [])
        nl_assertions.append(
            f"Agent must {milestone}: {', '.join(must_include)}"
        )

    # Add diagnosis assertion
    nl_assertions.append(
        f"Agent should arrive at or consider the diagnosis: {diagnosis}"
    )

    # Determine reward_basis from difficulty level and scenario type
    difficulty = task_config.get("difficulty", "L1")
    scenario_type = task_config.get("task_type", None)
    eval_template = get_evaluation_template(scenario_type=scenario_type, difficulty=difficulty)
    reward_basis = eval_template.reward_basis

    evaluation_criteria = EvaluationCriteria(
        actions=eval_actions if eval_actions else None,
        nl_assertions=nl_assertions if nl_assertions else None,
        reward_basis=reward_basis,
    )

    description = Description(
        purpose=f"Clinical consultation - {task_config.get('task_type', 'unknown')} ({task_config.get('difficulty', 'unknown')})",
        relevant_policies=None,
        notes=(
            f"v3 task. Disease: {diagnosis}. "
            f"Differentials: {', '.join(clinical['diagnosis'].get('differentials', []))}. "
            f"Difficulty: {task_config.get('difficulty')}. "
            f"Seed: {task_config.get('seed')}"
        ),
    )

    return Task(
        id=v3_task["id"],
        description=description,
        user_scenario=user_scenario,
        evaluation_criteria=evaluation_criteria,
        initial_state=None,
    )


def main():
    parser = argparse.ArgumentParser(description="Run v3 tasks through tau2-bench")
    parser.add_argument("--tasks-file", type=str, default=None,
                        help="Path to all_tasks.json. If not provided, downloads from GitHub.")
    parser.add_argument("--num-tasks", type=int, default=None,
                        help="Number of tasks to run (default: all)")
    parser.add_argument("--agent-llm", type=str, default="azure/gpt-5.2",
                        help="Agent LLM model (default: azure/gpt-5.2)")
    parser.add_argument("--user-llm", type=str, default="azure/gpt-5.2",
                        help="User simulator LLM model (default: azure/gpt-5.2)")
    parser.add_argument("--domain", type=str, default="clinical_cardiology",
                        help="Domain environment to use for tools/policy (default: clinical_cardiology)")
    parser.add_argument("--max-steps", type=int, default=30,
                        help="Max conversation steps per task (default: 30)")
    parser.add_argument("--max-concurrency", type=int, default=3,
                        help="Max parallel simulations (default: 3)")
    parser.add_argument("--save-to", type=str, default=None,
                        help="Save results filename (without .json)")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="LLM temperature (default: 0.0)")
    args = parser.parse_args()

    # Load tasks
    tasks_file = args.tasks_file
    if tasks_file is None:
        tasks_file = PROJECT_ROOT / "generated_tasks_v3" / "all_tasks.json"
        if not tasks_file.exists():
            # Download from GitHub
            print("Downloading all_tasks.json from GitHub...")
            import urllib.request
            tasks_file.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(
                "https://raw.githubusercontent.com/circadiancity/agentmy/main/generated_tasks_v3/all_tasks.json",
                str(tasks_file),
            )
            print(f"Downloaded to {tasks_file}")

    print(f"Loading tasks from {tasks_file}...")
    with open(tasks_file) as f:
        v3_tasks = json.load(f)

    print(f"Found {len(v3_tasks)} v3 tasks")

    # Convert to tau2 format
    tau2_tasks = []
    for v3_task in v3_tasks:
        try:
            tau2_tasks.append(convert_v3_to_tau2(v3_task))
        except Exception as e:
            print(f"WARNING: Failed to convert task {v3_task.get('id', '?')}: {e}")

    print(f"Converted {len(tau2_tasks)} tasks to tau2 format")

    if args.num_tasks is not None:
        tau2_tasks = tau2_tasks[:args.num_tasks]
        print(f"Running {len(tau2_tasks)} tasks")

    # Set up Azure OpenAI environment
    azure_key = os.environ.get("AZURE_API_KEY")
    azure_base = os.environ.get("AZURE_API_BASE")
    azure_version = os.environ.get("AZURE_API_VERSION", "2024-12-01-preview")

    if azure_key:
        # LiteLLM reads these env vars automatically for azure/ prefix models
        os.environ["AZURE_API_KEY"] = azure_key
        os.environ["AZURE_API_BASE"] = azure_base or ""
        os.environ["AZURE_API_VERSION"] = azure_version
        print(f"Using Azure OpenAI: {azure_base}")
    else:
        print("WARNING: AZURE_API_KEY not set. Make sure your LLM credentials are configured.")

    llm_args = {"temperature": args.temperature}

    save_to = args.save_to or f"v3_tasks_{args.agent_llm.replace('/', '_')}"

    print(f"\nStarting tau2 simulation:")
    print(f"  Agent LLM: {args.agent_llm}")
    print(f"  User LLM:  {args.user_llm}")
    print(f"  Domain:    {args.domain}")
    print(f"  Tasks:     {len(tau2_tasks)}")
    print(f"  Max steps: {args.max_steps}")
    print(f"  Save to:   data/simulations/{save_to}.json")
    print()

    # Determine the evaluation type that covers all reward basis types in the task set.
    # ALL_WITH_CLINICAL_GATE is the most comprehensive and handles any reward_basis.
    has_clinical = any(
        RewardType.CLINICAL in t.evaluation_criteria.reward_basis
        for t in tau2_tasks if t.evaluation_criteria
    )
    has_nl = any(
        RewardType.NL_ASSERTION in t.evaluation_criteria.reward_basis
        for t in tau2_tasks if t.evaluation_criteria
    )
    if has_clinical:
        eval_type = EvaluationType.ALL_WITH_CLINICAL_GATE
    elif has_nl:
        eval_type = EvaluationType.ALL_WITH_NL_ASSERTIONS
    else:
        eval_type = EvaluationType.ALL

    print(f"  Eval type: {eval_type.value}")
    print()

    # Run
    results = run_tasks(
        domain=args.domain,
        tasks=tau2_tasks,
        agent="llm_agent",
        user="user_simulator",
        llm_agent=args.agent_llm,
        llm_args_agent=llm_args,
        llm_user=args.user_llm,
        llm_args_user=llm_args,
        max_steps=args.max_steps,
        num_trials=1,
        save_to=str(PROJECT_ROOT / "data" / "simulations" / f"{save_to}.json"),
        console_display=True,
        evaluation_type=eval_type,
        max_concurrency=args.max_concurrency,
        log_level="INFO",
    )

    # Print metrics
    metrics = compute_metrics(results)
    ConsoleDisplay.display_agent_metrics(metrics)

    print(f"\nResults saved to: data/simulations/{save_to}.json")
    print(f"View results with: tau2 view --file data/simulations/{save_to}.json")


if __name__ == "__main__":
    main()
