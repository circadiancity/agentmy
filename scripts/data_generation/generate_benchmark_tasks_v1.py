#!/usr/bin/env python3
"""Generate clinical benchmark tasks using PrimeKG random walk + LLM enrichment.

This script:
1. Generates PrimeKG random walk paths
2. Enriches paths with LLM to create realistic medical scenarios
3. Converts to tau2 task format
4. Saves to data/tau2/domains/clinical/benchmark/
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import argparse
import numpy as np
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tau2.data_model.tasks import Task, Description, UserScenario, StructuredUserInstructions, InitialState, EvaluationCriteria, Action
from tau2.domains.clinical.benchmark.utils import (
    BENCHMARK_KNOWLEDGE_BASE_PATH,
    BENCHMARK_TASK_SET_PATH,
)


class StaticKnowledgeGraphLoader:
    """Load knowledge graph from static JSON file."""

    def __init__(self, kb_path: Path):
        self.kb_path = kb_path
        self.diseases = {}
        self.drugs = {}
        self._load()

    def _load(self):
        """Load knowledge base from JSON."""
        if not self.kb_path.exists():
            logger.warning(f"Knowledge base not found: {self.kb_path}")
            return

        with open(self.kb_path, "r") as f:
            kb_data = json.load(f)

        # Index by name
        for disease in kb_data.get("diseases", []):
            self.diseases[disease["name"].lower()] = disease

        for drug in kb_data.get("drugs", []):
            self.drugs[drug["name"].lower()] = drug

        logger.info(f"Loaded {len(self.diseases)} diseases and {len(self.drugs)} drugs")

    def get_disease(self, name: str) -> Optional[Dict]:
        """Get disease by name."""
        return self.diseases.get(name.lower())

    def get_drug(self, name: str) -> Optional[Dict]:
        """Get drug by name."""
        return self.drugs.get(name.lower())

    def sample_diseases(self, n: int = 1) -> List[Dict]:
        """Sample random diseases."""
        return list(np.random.choice(
            list(self.diseases.values()),
            size=min(n, len(self.diseases)),
            replace=False
        ))


class PrimeKGPath:
    """Simulated PrimeKG walk path."""

    def __init__(self, disease: str, symptoms: List[str], drugs: List[str]):
        self.disease = disease
        self.symptoms = symptoms
        self.drugs = drugs


class PrimeKGRandomWalkSimulator:
    """Simulate random walk on PrimeKG."""

    def __init__(self, kg: StaticKnowledgeGraphLoader):
        self.kg = kg

    def generate_walk(self, disease_name: str) -> Optional[PrimeKGPath]:
        """Generate a random walk starting from a disease."""
        disease = self.kg.get_disease(disease_name)
        if not disease:
            return None

        # Extract symptoms and treatments from disease
        symptoms = disease.get("symptoms", [])
        treatment_options = disease.get("treatment_options", [])

        # Match treatment options to drugs
        drugs = []
        for treatment in treatment_options[:3]:
            # Simple matching: if it's in the drugs list, add it
            drug = self.kg.get_drug(treatment.lower().split()[0])
            if drug:
                drugs.append(drug["name"])

        return PrimeKGPath(
            disease=disease["name"],
            symptoms=symptoms[:4],  # Limit symptoms
            drugs=drugs[:3]  # Limit drugs
        )


class LLMTaskEnricher:
    """Enrich PrimeKG paths with LLM using Azure OpenAI."""

    def __init__(self, use_azure: bool = True, dry_run: bool = False):
        self.use_azure = use_azure
        self.dry_run = dry_run

        if use_azure and not dry_run:
            try:
                import litellm
                self.client = litellm
                # Configure Azure endpoint
                self._setup_azure()
            except ImportError:
                logger.warning("litellm not available, falling back to template-based enrichment")
                self.use_azure = False

    def _setup_azure(self):
        """Setup Azure OpenAI configuration."""
        import os
        api_key = os.getenv("AZURE_API_KEY")
        api_base = os.getenv("AZURE_API_BASE")
        api_version = os.getenv("AZURE_API_VERSION")

        if not all([api_key, api_base, api_version]):
            logger.warning("Azure credentials not found in environment")
            self.use_azure = False

    def enrich_task(self, path: PrimeKGPath, task_id: str) -> Optional[Task]:
        """Enrich a PrimeKG path into a full task."""
        if self.dry_run:
            return self._template_enrich(path, task_id)

        if self.use_azure:
            return self._llm_enrich(path, task_id)
        else:
            return self._template_enrich(path, task_id)

    def _template_enrich(self, path: PrimeKGPath, task_id: str) -> Task:
        """Template-based enrichment (for testing)."""
        # Generate patient profile
        ages = [25, 35, 45, 55, 65, 75]
        age = int(np.random.choice(ages))
        gender = np.random.choice(["M", "F"])

        patient_profile = {
            "age": age,
            "gender": gender,
            "chief_complaint": f"Patient with {path.disease}",
            "symptoms": path.symptoms,
            "medications": [],
            "allergies": []
        }

        # Create tau2 task
        description = Description(
            purpose=f"Medical consultation for {path.disease}",
            relevant_policies=None,
            notes=f"Generated from PrimeKG path. Disease: {path.disease}"
        )

        user_instructions = StructuredUserInstructions(
            domain="clinical_benchmark",
            reason_for_call=f"Chief complaint: {path.symptoms[0] if path.symptoms else path.disease}",
            known_info=f"Patient is {age} years old",
            unknown_info="Medical history not yet disclosed",
            task_instructions=f"You are a {age}-year-old {gender.lower()} patient with {path.disease}. "
                            f"Describe your symptoms and answer the doctor's questions."
        )

        user_scenario = UserScenario(
            persona=f"{age}-year-old {gender} patient",
            instructions=user_instructions
        )

        # Create evaluation criteria
        evaluation_criteria = EvaluationCriteria(
            actions=[
                Action(
                    action_id="search_disease",
                    requestor="assistant",
                    name="search_disease_info",
                    arguments={"disease_name": path.disease}
                ),
                Action(
                    action_id="order_test",
                    requestor="assistant",
                    name="order_lab_test",
                    arguments={"test_name": "CBC", "urgency": "routine"}
                )
            ] if path.disease else [],
            communicate_info=["Provide diagnosis", "Explain treatment plan"],
            nl_assertions=None,
            reward_basis=["ACTION", "COMMUNICATE"]
        )

        task = Task(
            id=task_id,
            description=description,
            user_scenario=user_scenario,
            ticket=f"Chief complaint: {path.symptoms[0] if path.symptoms else path.disease}",
            initial_state=InitialState(
                initialization_actions=[
                    {
                        "env_type": "user",
                        "func_name": "set_user_info",
                        "arguments": {
                            "name": f"Patient_{task_id}",
                            "age": age,
                            "gender": gender
                        }
                    }
                ]
            ),
            evaluation_criteria=evaluation_criteria
        )

        return task

    def _llm_enrich(self, path: PrimeKGPath, task_id: str) -> Task:
        """LLM-based enrichment using Azure OpenAI."""
        # For now, fallback to template-based
        logger.info("LLM enrichment not fully implemented, using template enrichment")
        return self._template_enrich(path, task_id)


class BenchmarkTaskGenerator:
    """Generate complete clinical benchmark tasks."""

    def __init__(self, dry_run: bool = False):
        self.kg = StaticKnowledgeGraphLoader(BENCHMARK_KNOWLEDGE_BASE_PATH)
        self.walk_generator = PrimeKGRandomWalkSimulator(self.kg)
        self.enricher = LLMTaskEnricher(dry_run=dry_run)
        self.tasks = []

    def generate_tasks(self, n_tasks: int = 50, difficulty_levels: Optional[List[str]] = None) -> List[Task]:
        """Generate n tasks with specified difficulty levels."""
        if difficulty_levels is None:
            difficulty_levels = ["general", "specialized", "emergency", "pharmacology"]

        logger.info(f"Generating {n_tasks} benchmark tasks...")

        task_count = 0
        failed_count = 0

        for i in range(n_tasks):
            try:
                # Sample a disease
                disease = self.kg.sample_diseases(1)[0]

                # Generate walk path
                path = self.walk_generator.generate_walk(disease["name"])
                if not path:
                    failed_count += 1
                    continue

                # Enrich with LLM
                task_id = f"clinical_benchmark_{task_count:04d}"
                task = self.enricher.enrich_task(path, task_id)

                if task:
                    self.tasks.append(task)
                    task_count += 1
                    logger.debug(f"Generated task {task_count}/{n_tasks}: {task.id}")

                    # Rate limiting
                    if i % 10 == 0:
                        time.sleep(0.1)

            except Exception as e:
                logger.warning(f"Error generating task {i}: {e}")
                failed_count += 1
                continue

        logger.info(f"Generated {task_count} tasks ({failed_count} failures)")
        return self.tasks

    def save_tasks(self, output_dir: Optional[Path] = None):
        """Save generated tasks to JSON files."""
        if output_dir is None:
            output_dir = BENCHMARK_TASK_SET_PATH.parent

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save tasks
        tasks_json = [task.model_dump(exclude_none=True) for task in self.tasks]
        tasks_file = output_dir / "tasks.json"

        with open(tasks_file, "w") as f:
            json.dump(tasks_json, f, indent=2)

        logger.info(f"Saved {len(self.tasks)} tasks to {tasks_file}")

        # Save splits (80/20 train/test)
        task_ids = [t.id for t in self.tasks]
        split_point = int(len(task_ids) * 0.8)

        splits = {
            "base": task_ids,
            "train": task_ids[:split_point],
            "test": task_ids[split_point:]
        }

        split_file = output_dir / "split_tasks.json"
        with open(split_file, "w") as f:
            json.dump(splits, f, indent=2)

        logger.info(f"Saved task splits to {split_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate clinical benchmark tasks from PrimeKG + LLM enrichment"
    )
    parser.add_argument("--n_tasks", type=int, default=50, help="Number of tasks to generate")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for tasks")
    parser.add_argument("--dry_run", action="store_true", help="Use template enrichment only (no LLM)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    logger.info(f"Clinical Benchmark Task Generator v1.0")
    logger.info(f"Configuration: n_tasks={args.n_tasks}, dry_run={args.dry_run}")

    # Generate tasks
    generator = BenchmarkTaskGenerator(dry_run=args.dry_run)
    generator.generate_tasks(n_tasks=args.n_tasks)

    # Save tasks
    output_dir = Path(args.output_dir) if args.output_dir else None
    generator.save_tasks(output_dir)

    logger.info("✓ Task generation complete!")


if __name__ == "__main__":
    main()
