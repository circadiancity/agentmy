#!/usr/bin/env python3
"""
PrimeKG Clinical Benchmark Runner

End-to-end benchmark runner for the PrimeKG clinical domain.
Loads enriched tasks, runs simulations with appropriate evaluation per
difficulty level, and reports per-difficulty metrics.

Usage:
    # Dry run — validate tasks and tools without running simulations
    python scripts/evaluation/run_primekg_benchmark.py --dry-run

    # Run 10 tasks with defaults
    python scripts/evaluation/run_primekg_benchmark.py --num-tasks 10

    # Full run with custom model
    python scripts/evaluation/run_primekg_benchmark.py --agent-llm azure/gpt-5.2 --max-concurrency 5
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from tau2.data_model.tasks import RewardType, Task
from tau2.evaluator.evaluator import EvaluationType
from tau2.evaluator.metrics.clinical_scoring import (
    DIFFICULTY_REWARD_BASIS,
    get_evaluation_template,
)
from tau2.registry import registry
from tau2.run import run_tasks
from tau2.metrics.agent_metrics import compute_metrics
from tau2.utils.display import ConsoleDisplay

logger = logging.getLogger(__name__)

DOMAIN = "primekg"

# Map difficulty → EvaluationType (determines which evaluators fire)
DIFFICULTY_EVAL_TYPE: dict[str, EvaluationType] = {
    "L0": EvaluationType.ALL,
    "L1": EvaluationType.ALL_WITH_NL_ASSERTIONS,
    "L2": EvaluationType.ALL_WITH_NL_ASSERTIONS,
    "L3": EvaluationType.ALL_WITH_CLINICAL_GATE,
}


def _extract_difficulty(task: Task) -> str:
    """Extract difficulty level (L0-L3) from task metadata."""
    # Try from description.purpose: "Clinical consultation - diagnostic_uncertainty (L1)"
    if task.description and task.description.purpose:
        m = re.search(r"\(L(\d)\)", task.description.purpose)
        if m:
            return f"L{m.group(1)}"
    # Try from task ID: "primekg_L1_32707_42"
    m = re.search(r"_L(\d)_", task.id)
    if m:
        return f"L{m.group(1)}"
    # Try from description.notes
    if task.description and task.description.notes:
        m = re.search(r"Difficulty:\s*(L\d)", task.description.notes)
        if m:
            return m.group(1)
    return "L1"  # default


def dry_run(tasks: list[Task]) -> bool:
    """Validate tasks, tools, and evaluation criteria without running simulations."""
    print(f"\n{'='*60}")
    print("  DRY RUN — Validation Only")
    print(f"{'='*60}\n")

    errors = []

    # 1. Check domain is registered
    try:
        env_constructor = registry.get_env_constructor(DOMAIN)
        env = env_constructor()
        tools = env.tools
        tool_dict = tools.get_tools() if hasattr(tools, "get_tools") else {}
        tool_names = set(tool_dict.keys()) if isinstance(tool_dict, dict) else {t.name for t in tool_dict}
        print(f"[OK] Domain '{DOMAIN}' registered. Tools available: {len(tool_names)}")
        if tool_names:
            print(f"     Tools: {', '.join(sorted(tool_names)[:10])}{'...' if len(tool_names) > 10 else ''}")
    except Exception as e:
        errors.append(f"Domain registration: {e}")
        print(f"[FAIL] Domain '{DOMAIN}': {e}")

    # 2. Group tasks by difficulty
    by_difficulty = defaultdict(list)
    for t in tasks:
        by_difficulty[_extract_difficulty(t)].append(t)

    print(f"\n[OK] Loaded {len(tasks)} tasks")
    for diff in sorted(by_difficulty):
        count = len(by_difficulty[diff])
        eval_type = DIFFICULTY_EVAL_TYPE.get(diff, EvaluationType.ALL)
        print(f"     {diff}: {count} tasks → evaluation={eval_type.value}")

    # 3. Validate evaluation criteria
    missing_actions = 0
    missing_nl = 0
    for t in tasks:
        if t.evaluation_criteria is None:
            errors.append(f"Task {t.id}: no evaluation_criteria")
            continue
        if not t.evaluation_criteria.actions:
            missing_actions += 1
        if not t.evaluation_criteria.nl_assertions:
            missing_nl += 1

    print(f"\n     Tasks with actions: {len(tasks) - missing_actions}/{len(tasks)}")
    print(f"     Tasks with NL assertions: {len(tasks) - missing_nl}/{len(tasks)}")

    # 4. Validate reward_basis vs evaluation_type compatibility
    compat_errors = 0
    for t in tasks:
        if t.evaluation_criteria is None:
            continue
        diff = _extract_difficulty(t)
        eval_type = DIFFICULTY_EVAL_TYPE.get(diff, EvaluationType.ALL)
        basis = set(t.evaluation_criteria.reward_basis)
        if RewardType.NL_ASSERTION in basis and eval_type == EvaluationType.ALL:
            compat_errors += 1
        if RewardType.CLINICAL in basis and eval_type not in {
            EvaluationType.ALL_WITH_CLINICAL,
            EvaluationType.ALL_WITH_CLINICAL_GATE,
        }:
            compat_errors += 1

    if compat_errors:
        print(f"\n[WARN] {compat_errors} tasks have reward_basis/eval_type mismatch")
        print("       These tasks' reward_basis will be used as-is; ensure eval_type covers them.")

    # 5. Summary
    print(f"\n{'='*60}")
    if errors:
        print(f"  DRY RUN FAILED — {len(errors)} error(s)")
        for err in errors:
            print(f"    - {err}")
        return False
    else:
        print("  DRY RUN PASSED")
        return True


def run_benchmark(args: argparse.Namespace) -> None:
    """Run the full benchmark pipeline."""
    # Load tasks
    print(f"Loading tasks from domain '{DOMAIN}'...")
    task_loader = registry.get_tasks_loader(DOMAIN)
    all_tasks = task_loader()
    print(f"Loaded {len(all_tasks)} tasks")

    if args.num_tasks is not None:
        all_tasks = all_tasks[:args.num_tasks]
        print(f"Selected first {len(all_tasks)} tasks")

    # Dry run check
    if args.dry_run:
        dry_run(all_tasks)
        return

    # Group by difficulty for per-group evaluation
    by_difficulty = defaultdict(list)
    for t in all_tasks:
        by_difficulty[_extract_difficulty(t)].append(t)

    # Azure/LLM setup
    llm_args = {"temperature": args.temperature}
    azure_key = os.environ.get("AZURE_API_KEY")
    if azure_key:
        os.environ.setdefault("AZURE_API_BASE", os.environ.get("AZURE_API_BASE", ""))
        os.environ.setdefault("AZURE_API_VERSION", os.environ.get("AZURE_API_VERSION", "2024-12-01-preview"))

    print(f"\nBenchmark configuration:")
    print(f"  Agent LLM: {args.agent_llm}")
    print(f"  User LLM:  {args.user_llm}")
    print(f"  Max steps: {args.max_steps}")
    print(f"  Concurrency: {args.max_concurrency}")
    for diff in sorted(by_difficulty):
        eval_type = DIFFICULTY_EVAL_TYPE.get(diff, EvaluationType.ALL)
        print(f"  {diff}: {len(by_difficulty[diff])} tasks → {eval_type.value}")

    # Determine evaluation type
    # Use the highest-level evaluation type that covers all tasks,
    # or allow override via CLI
    if args.evaluation_type:
        eval_type = EvaluationType(args.evaluation_type)
    else:
        # Default: ALL_WITH_CLINICAL_GATE covers all reward basis types
        eval_type = EvaluationType.ALL_WITH_CLINICAL_GATE

    print(f"\n  Evaluation type: {eval_type.value}")
    print()

    # Prepare output path
    output_dir = PROJECT_ROOT / "data" / "simulations"
    output_dir.mkdir(parents=True, exist_ok=True)
    save_name = args.save_to or f"primekg_benchmark_{args.agent_llm.replace('/', '_')}"
    save_path = str(output_dir / f"{save_name}.json")

    start_time = time.time()

    results = run_tasks(
        domain=DOMAIN,
        tasks=all_tasks,
        agent="llm_agent",
        user="user_simulator",
        llm_agent=args.agent_llm,
        llm_args_agent=llm_args,
        llm_user=args.user_llm,
        llm_args_user=llm_args,
        max_steps=args.max_steps,
        num_trials=1,
        save_to=save_path,
        console_display=True,
        evaluation_type=eval_type,
        max_concurrency=args.max_concurrency,
        log_level="INFO",
    )

    elapsed = time.time() - start_time

    # Compute overall metrics
    metrics = compute_metrics(results)
    ConsoleDisplay.display_agent_metrics(metrics)

    # Per-difficulty breakdown
    print(f"\n{'='*60}")
    print("  Per-Difficulty Breakdown")
    print(f"{'='*60}")

    task_id_to_diff = {t.id: _extract_difficulty(t) for t in all_tasks}
    diff_rewards = defaultdict(list)
    for sim in results.simulations:
        diff = task_id_to_diff.get(sim.task_id, "unknown")
        diff_rewards[diff].append(sim.reward_info.reward if sim.reward_info else 0.0)

    for diff in sorted(diff_rewards):
        rewards = diff_rewards[diff]
        avg = sum(rewards) / len(rewards) if rewards else 0.0
        passed = sum(1 for r in rewards if r > 0.0)
        print(f"  {diff}: avg_reward={avg:.3f}, pass@1={passed}/{len(rewards)} ({100*passed/len(rewards):.1f}%)")

    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Results saved to: {save_path}")

    # Save summary JSON alongside
    summary = {
        "domain": DOMAIN,
        "agent_llm": args.agent_llm,
        "user_llm": args.user_llm,
        "evaluation_type": eval_type.value,
        "num_tasks": len(all_tasks),
        "elapsed_seconds": round(elapsed, 1),
        "overall_avg_reward": metrics.get("avg_reward", 0.0) if isinstance(metrics, dict) else 0.0,
        "per_difficulty": {
            diff: {
                "count": len(rewards),
                "avg_reward": round(sum(rewards) / len(rewards), 4) if rewards else 0.0,
                "pass_at_1": sum(1 for r in rewards if r > 0.0),
            }
            for diff, rewards in sorted(diff_rewards.items())
        },
    }
    summary_path = save_path.replace(".json", "_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="PrimeKG Clinical Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--num-tasks", type=int, default=None,
                        help="Number of tasks to run (default: all)")
    parser.add_argument("--max-concurrency", type=int, default=3,
                        help="Max parallel simulations (default: 3)")
    parser.add_argument("--max-steps", type=int, default=50,
                        help="Max conversation steps per task (default: 50)")
    parser.add_argument("--agent-llm", type=str, default="azure/gpt-5.2",
                        help="Agent LLM model (default: azure/gpt-5.2)")
    parser.add_argument("--user-llm", type=str, default="azure/gpt-5.2",
                        help="User simulator LLM model (default: azure/gpt-5.2)")
    parser.add_argument("--evaluation-type", type=str, default=None,
                        choices=[e.value for e in EvaluationType],
                        help="Override evaluation type (default: auto per difficulty)")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="LLM temperature (default: 0.0)")
    parser.add_argument("--save-to", type=str, default=None,
                        help="Save results filename (without .json)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate tasks and tools without running simulations")

    args = parser.parse_args()
    run_benchmark(args)


if __name__ == "__main__":
    main()
