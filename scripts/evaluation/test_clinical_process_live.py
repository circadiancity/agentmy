#!/usr/bin/env python3
"""
Live simulation test for ClinicalProcessEvaluator.

Runs 5 primekg tasks with azure/gpt-5.2 in solo mode,
evaluates with CLINICAL_PROCESS, and prints detailed results.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from tau2.run import run_tasks, get_tasks
from tau2.evaluator.evaluator import EvaluationType
from tau2.data_model.message import AssistantMessage, UserMessage


def analyze_trajectory(sim):
    """Extract tool call sequence and key stats from a simulation."""
    tool_calls = []
    assistant_text_len = 0
    for msg in sim.messages:
        if isinstance(msg, (AssistantMessage, UserMessage)) and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(tc.name)
        if isinstance(msg, AssistantMessage) and msg.content:
            assistant_text_len += len(msg.content)
    return tool_calls, assistant_text_len


def main():
    print("=" * 70)
    print(" ClinicalProcessEvaluator — Live Simulation Test")
    print("=" * 70)

    # Load first 10 tasks
    tasks = get_tasks("primekg")[:10]
    print(f"\nLoaded {len(tasks)} tasks:")
    for i, t in enumerate(tasks):
        rb = t.evaluation_criteria.reward_basis if t.evaluation_criteria else "N/A"
        print(f"  {i+1}. {t.id} (reward_basis: {[str(r) for r in rb]})")

    # Output dir
    output_dir = Path("results/clinical_process_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"clinical_process_{ts}.json"

    # Run simulation with llm_agent + user_simulator (conversational mode)
    print(f"\nRunning simulation with azure/gpt-5.2 ...")
    results = run_tasks(
        domain="primekg",
        tasks=tasks,
        agent="llm_agent",
        user="user_simulator",
        llm_agent="azure/gpt-5.2",
        llm_args_agent={"temperature": 0.0, "max_tokens": 2000, "timeout": 120},
        llm_user="azure/gpt-5.2",
        llm_args_user={"temperature": 0.0, "max_tokens": 1000, "timeout": 120},
        num_trials=1,
        max_steps=50,
        max_errors=5,
        save_to=str(output_file),
        console_display=True,
        evaluation_type=EvaluationType.CLINICAL_PROCESS,
        max_concurrency=3,
        seed=42,
        log_level="INFO",
    )

    # Analyze results
    print(f"\n{'=' * 70}")
    print(" RESULTS ANALYSIS")
    print(f"{'=' * 70}")

    scores = []
    for sim in results.simulations:
        task = next(t for t in results.tasks if t.id == sim.task_id)
        reward = sim.reward_info.reward if sim.reward_info else None
        scores.append(reward)

        print(f"\n--- Task: {sim.task_id} ---")
        print(f"  Termination: {sim.termination_reason.value}")
        print(f"  Messages: {len(sim.messages)}")
        print(f"  Duration: {sim.duration:.1f}s")
        print(f"  Agent cost: ${sim.agent_cost:.4f}" if sim.agent_cost else "  Agent cost: N/A")

        if sim.reward_info:
            print(f"  REWARD: {sim.reward_info.reward}")
            if sim.reward_info.clinical_checks:
                check = sim.reward_info.clinical_checks[0]
                print(f"  Dimensions: {json.dumps(check.dimension_scores, indent=4)}")
                print(f"  Comments: {check.comments}")
            if sim.reward_info.info:
                dims = sim.reward_info.info.get("dimensions", {})
                for dim_name, dim_info in dims.items():
                    print(f"  [{dim_name}]:")
                    for k, v in dim_info.items():
                        print(f"    {k}: {v}")

            # Tool call analysis
            tool_calls, text_len = analyze_trajectory(sim)
            print(f"  Tool calls ({len(tool_calls)}): {tool_calls}")
            print(f"  Assistant text length: {text_len} chars")
        else:
            print(f"  NO REWARD INFO (premature termination?)")

    # Summary statistics
    valid_scores = [s for s in scores if s is not None]
    print(f"\n{'=' * 70}")
    print(" SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Tasks run: {len(results.simulations)}")
    print(f"  Valid scores: {len(valid_scores)}")
    if valid_scores:
        print(f"  Score range: [{min(valid_scores):.3f}, {max(valid_scores):.3f}]")
        print(f"  Mean score: {sum(valid_scores)/len(valid_scores):.3f}")
        print(f"  Scores: {valid_scores}")
        safety_gated = sum(1 for s in valid_scores if s == 0.0)
        perfect = sum(1 for s in valid_scores if s >= 0.95)
        print(f"  Safety gated (0.0): {safety_gated}/{len(valid_scores)}")
        print(f"  Near-perfect (>=0.95): {perfect}/{len(valid_scores)}")

    # Distribution check
    print(f"\n  Distribution analysis:")
    if len(set(valid_scores)) == 1:
        print(f"  WARNING: All scores identical ({valid_scores[0]}) — evaluator may be too strict or too lenient")
    else:
        print(f"  OK: Scores are distributed across {len(set(valid_scores))} distinct values")

    print(f"\n  Results saved to: {output_file}")


if __name__ == "__main__":
    main()
