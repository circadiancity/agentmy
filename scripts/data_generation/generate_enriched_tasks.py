#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate LLM-enriched clinical tasks from PrimeKG random walks.

Takes skeletal PrimeKG walk results, enriches them via GPT-5.2, converts to
tau2 format, and saves with train/test splits.

Usage:
    # Dry run (2-3 tasks)
    python scripts/data_generation/generate_enriched_tasks.py --dry-run

    # Generate 200 tasks with default difficulty distribution
    python scripts/data_generation/generate_enriched_tasks.py --num-tasks 200

    # Custom difficulty mix
    python scripts/data_generation/generate_enriched_tasks.py --num-tasks 50 \
        --difficulty-dist '{"L0": 0.2, "L1": 0.3, "L2": 0.3, "L3": 0.2}'

    # Specify output and seed
    python scripts/data_generation/generate_enriched_tasks.py --num-tasks 100 \
        --output-dir data/tau2/domains/clinical/primekg/ --seed 123
"""

import argparse
import asyncio
import json
import os
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate LLM-enriched clinical tasks from PrimeKG"
    )
    parser.add_argument(
        "--num-tasks", type=int, default=200,
        help="Number of tasks to generate (default: 200)",
    )
    parser.add_argument(
        "--difficulty-dist", type=str,
        default='{"L0": 0.1, "L1": 0.3, "L2": 0.4, "L3": 0.2}',
        help="JSON difficulty distribution",
    )
    parser.add_argument(
        "--output-dir", type=str,
        default="data/tau2/domains/clinical/primekg/",
        help="Output directory for tau2 tasks",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--model", type=str, default="azure/gpt-5.2",
        help="LLM model for enrichment (default: azure/gpt-5.2)",
    )
    parser.add_argument(
        "--max-concurrency", type=int, default=3,
        help="Max parallel LLM calls (default: 3)",
    )
    parser.add_argument(
        "--walk-types", type=str, nargs="+",
        default=["medium", "long", "complex"],
        help="Walk types to use (default: medium long complex)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Generate only 3 tasks for testing",
    )
    parser.add_argument(
        "--test-split", type=float, default=0.2,
        help="Fraction of tasks for test set (default: 0.2)",
    )
    parser.add_argument(
        "--v3-only", action="store_true",
        help="Save only v3 format (skip tau2 conversion)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Symptom pool for walk generation
# ---------------------------------------------------------------------------
SYMPTOM_KEYWORDS = [
    "pain", "fever", "nausea", "headache", "cough", "fatigue",
    "dizziness", "shortness of breath", "chest pain", "weight loss",
    "abdominal pain", "joint pain", "rash", "vomiting", "diarrhea",
    "constipation", "anxiety", "insomnia", "palpitations", "swelling",
    "numbness", "weakness", "blurred vision", "urinary frequency",
    "back pain", "muscle pain", "sore throat", "loss of appetite",
    "itching", "bleeding", "tremor", "confusion",
]


def _pick_difficulty(dist: dict, rng: random.Random) -> str:
    """Sample a difficulty level from the distribution."""
    levels = list(dist.keys())
    weights = [dist[k] for k in levels]
    return rng.choices(levels, weights=weights, k=1)[0]


def _pick_walk_type(difficulty: str, walk_types: list, rng: random.Random) -> str:
    """Map difficulty to walk complexity, with some randomness."""
    preference = {
        "L0": ["short", "medium"],
        "L1": ["medium", "long"],
        "L2": ["long", "complex"],
        "L3": ["complex", "comorbid"],
    }
    candidates = [w for w in preference.get(difficulty, walk_types) if w in walk_types]
    if not candidates:
        candidates = walk_types
    return rng.choice(candidates)


# ---------------------------------------------------------------------------
# Walk generation
# ---------------------------------------------------------------------------

def generate_walks(
    num_tasks: int,
    walk_types: list,
    difficulty_dist: dict,
    seed: int,
):
    """Generate PrimeKG random walks."""
    from medical_task_suite.generation.core.random_walk import (
        PrimeKGRandomWalkPipeline,
        MultiPathWalkGenerator,
    )

    rng = random.Random(seed)
    print("[1/4] Initializing PrimeKG pipeline...")
    pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
    multi_gen = MultiPathWalkGenerator(pipeline.real_kg)

    walks = []
    difficulties = []
    symptoms_used = []
    attempts = 0
    max_attempts = num_tasks * 5

    print(f"[2/4] Generating {num_tasks} random walks...")
    while len(walks) < num_tasks and attempts < max_attempts:
        attempts += 1
        keyword = rng.choice(SYMPTOM_KEYWORDS)
        difficulty = _pick_difficulty(difficulty_dist, rng)
        wtype = _pick_walk_type(difficulty, walk_types, rng)

        try:
            # Resolve symptom in KG
            results = pipeline.real_kg.search_nodes(
                keyword, node_type="effect/phenotype", limit=3
            )
            if not results:
                continue

            symptom_node = rng.choice(results)
            symptom_id = symptom_node["id"]

            # Generate multi-path walk
            walk_result = multi_gen.generate_complex_walk(
                start_symptom_id=symptom_id,
                walk_type=wtype,
            )

            if walk_result and walk_result.main_path.nodes:
                walks.append(walk_result)
                difficulties.append(difficulty)
                symptoms_used.append(keyword)
                if len(walks) % 10 == 0:
                    print(f"  ... {len(walks)}/{num_tasks} walks generated")

        except Exception as e:
            # Silently skip failed walks
            continue

    print(f"  Generated {len(walks)} walks in {attempts} attempts")
    return walks, difficulties


# ---------------------------------------------------------------------------
# Tau2 conversion
# ---------------------------------------------------------------------------

def convert_v3_to_tau2_task(v3_task: dict):
    """Convert a single v3 task to a tau2 Task object."""
    from tau2.data_model.tasks import (
        Task, Description, UserScenario, StructuredUserInstructions,
        EvaluationCriteria, Action, RewardType,
    )

    patient = v3_task["patient"]
    clinical = v3_task["clinical"]
    ground_truth = v3_task["ground_truth"]
    task_config = v3_task["task_config"]
    eval_meta = v3_task.get("_eval", {})

    chief_complaint = patient["chief_complaint"]
    profile = patient["profile"]
    diagnosis = clinical["diagnosis"]["primary"]

    # Build user instructions
    persona = (
        f"{profile.get('age', 50)}-year-old {profile.get('gender', 'unknown')} patient, "
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
        task_instructions=patient.get(
            "instructions",
            f"You are a patient with {chief_complaint}. Answer the doctor's questions.",
        ),
    )

    user_scenario = UserScenario(persona=persona, instructions=instructions)

    # Build evaluation actions from tool_call_sequence
    eval_actions = []
    for i, tc in enumerate(eval_meta.get("tool_call_sequence", [])):
        tool_name = tc if isinstance(tc, str) else tc.get("tool", "")
        args = {} if isinstance(tc, str) else tc.get("required_args", {})
        eval_actions.append(Action(
            action_id=f"tool_{i}_{tool_name}",
            requestor="assistant",
            name=tool_name,
            arguments=args,
            compare_args=list(args.keys()) if args else [],
        ))

    # NL assertions
    nl_assertions = list(eval_meta.get("nl_assertions", []))
    for comm in ground_truth.get("communication_truth", []):
        milestone = comm.get("milestone", "")
        must_include = comm.get("must_include", [])
        nl_assertions.append(
            f"Agent must {milestone}: {', '.join(must_include)}"
        )
    nl_assertions.append(
        f"Agent should arrive at or consider the diagnosis: {diagnosis}"
    )
    # Safety assertions
    for sc in ground_truth.get("required_safety_checks", []):
        if sc.get("critical"):
            nl_assertions.append(
                f"Agent must perform {sc['check']} before {sc['before']}"
            )

    # Communicate info
    communicate_info = []
    for comm in ground_truth.get("communication_truth", []):
        for item in comm.get("must_include", []):
            communicate_info.append(item)

    # Map reward basis strings to RewardType
    reward_map = {
        "ACTION": RewardType.ACTION,
        "COMMUNICATE": RewardType.COMMUNICATE,
        "NL_ASSERTION": RewardType.NL_ASSERTION,
        "CLINICAL": RewardType.CLINICAL,
        "DB": RewardType.DB,
    }
    reward_basis = [
        reward_map[r] for r in eval_meta.get("reward_basis", ["ACTION", "COMMUNICATE"])
        if r in reward_map
    ]

    evaluation_criteria = EvaluationCriteria(
        actions=eval_actions if eval_actions else None,
        communicate_info=communicate_info if communicate_info else None,
        nl_assertions=nl_assertions if nl_assertions else None,
        reward_basis=reward_basis,
    )

    description = Description(
        purpose=(
            f"Clinical consultation - {task_config.get('task_type', 'diagnostic_uncertainty')} "
            f"({task_config.get('difficulty', 'L1')})"
        ),
        notes=(
            f"PrimeKG enriched task. Disease: {diagnosis}. "
            f"Differentials: {', '.join(clinical['diagnosis'].get('differentials', []))}. "
            f"Difficulty: {task_config.get('difficulty')}. Seed: {task_config.get('seed')}"
        ),
    )

    return Task(
        id=v3_task["id"],
        description=description,
        user_scenario=user_scenario,
        evaluation_criteria=evaluation_criteria,
        initial_state=None,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def generate_enriched_tasks(args):
    """Main generation pipeline."""
    from medical_task_suite.generation.core.llm_enrichment import (
        ClinicalTaskEnricher,
        enrich_batch,
    )

    num_tasks = 3 if args.dry_run else args.num_tasks
    difficulty_dist = json.loads(args.difficulty_dist)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate walks
    walks, difficulties = generate_walks(
        num_tasks=num_tasks,
        walk_types=args.walk_types,
        difficulty_dist=difficulty_dist,
        seed=args.seed,
    )

    if not walks:
        print("ERROR: No walks generated. Check PrimeKG data availability.")
        return

    # 2. Enrich via LLM
    print(f"[3/4] Enriching {len(walks)} walks via {args.model}...")
    v3_tasks = await enrich_batch(
        walk_results=walks,
        difficulties=difficulties,
        model=args.model,
        max_concurrency=args.max_concurrency,
        seed_start=args.seed,
    )
    print(f"  Enriched {len(v3_tasks)} tasks successfully")

    if not v3_tasks:
        print("ERROR: No tasks enriched. Check API credentials.")
        return

    # 3. Save v3 format
    v3_file = output_dir / "enriched_tasks_v3.json"
    with open(v3_file, "w") as f:
        json.dump(v3_tasks, f, indent=2, ensure_ascii=False)
    print(f"  Saved v3 tasks to {v3_file}")

    # 4. Convert to tau2 and save
    if not args.v3_only:
        print("[4/4] Converting to tau2 format...")
        tau2_tasks = []
        for v3_task in v3_tasks:
            try:
                tau2_task = convert_v3_to_tau2_task(v3_task)
                tau2_tasks.append(tau2_task)
            except Exception as e:
                print(f"  WARNING: Failed to convert {v3_task.get('id', '?')}: {e}")

        # Train/test split
        rng = random.Random(args.seed)
        indices = list(range(len(tau2_tasks)))
        rng.shuffle(indices)
        split_point = int(len(indices) * (1 - args.test_split))
        train_indices = sorted(indices[:split_point])
        test_indices = sorted(indices[split_point:])

        train_tasks = [tau2_tasks[i] for i in train_indices]
        test_tasks = [tau2_tasks[i] for i in test_indices]

        # Save
        all_tau2 = [t.model_dump() for t in tau2_tasks]
        with open(output_dir / "tasks.json", "w") as f:
            json.dump(all_tau2, f, indent=2, ensure_ascii=False)

        split_data = {
            "train": [t.model_dump() for t in train_tasks],
            "test": [t.model_dump() for t in test_tasks],
        }
        with open(output_dir / "split_tasks.json", "w") as f:
            json.dump(split_data, f, indent=2, ensure_ascii=False)

        # Statistics
        difficulty_counts = {}
        for t in v3_tasks:
            d = t.get("task_config", {}).get("difficulty", "?")
            difficulty_counts[d] = difficulty_counts.get(d, 0) + 1

        stats = {
            "total_tasks": len(tau2_tasks),
            "train_tasks": len(train_tasks),
            "test_tasks": len(test_tasks),
            "difficulty_distribution": difficulty_counts,
            "seed": args.seed,
            "model": args.model,
        }
        with open(output_dir / "stats.json", "w") as f:
            json.dump(stats, f, indent=2)

        print(f"  Saved {len(tau2_tasks)} tau2 tasks to {output_dir}")
        print(f"  Train: {len(train_tasks)}, Test: {len(test_tasks)}")
        print(f"  Difficulties: {difficulty_counts}")
    else:
        print("[4/4] Skipping tau2 conversion (--v3-only)")

    print("\nDone!")


def main():
    args = parse_args()
    asyncio.run(generate_enriched_tasks(args))


if __name__ == "__main__":
    main()
