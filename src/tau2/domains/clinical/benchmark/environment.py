"""Environment setup for the clinical benchmark domain."""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.benchmark.data_model import BenchmarkDB
from tau2.domains.clinical.benchmark.tools import ClinicalBenchmarkTools
from tau2.domains.clinical.benchmark.utils import (
    BENCHMARK_DB_PATH,
    BENCHMARK_POLICY_PATH,
    BENCHMARK_TASK_SET_PATH,
)
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[BenchmarkDB] = None,
    user_db: Optional[ClinicalUserDB] = None,
    solo_mode: bool = False,
) -> Environment:
    """Create and configure the clinical benchmark environment.

    Args:
        db: Optional pre-configured BenchmarkDB instance.
        user_db: Optional pre-configured ClinicalUserDB instance.
        solo_mode: Whether to run in solo mode.

    Returns:
        Configured Environment instance.
    """
    if db is None:
        db = BenchmarkDB.load(str(BENCHMARK_DB_PATH))

    if user_db is None:
        user_db = ClinicalUserDB()

    # Create tools for both agent and user simulator
    tools = ClinicalBenchmarkTools(db)
    user_tools = ClinicalUserTools(user_db)

    # Load policy
    try:
        with open(BENCHMARK_POLICY_PATH, "r") as fp:
            policy = fp.read()
    except FileNotFoundError:
        policy = _get_default_policy()

    # Create environment
    env = Environment(
        domain_name="clinical_benchmark",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        solo_mode=solo_mode,
    )

    return env


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load clinical benchmark tasks.

    Args:
        task_split_name: Optional task split name (e.g., 'train', 'test', 'base').
                        If None, returns all tasks.

    Returns:
        List of Task objects.
    """
    try:
        tasks = load_file(BENCHMARK_TASK_SET_PATH)
    except FileNotFoundError:
        # Return empty list if tasks file doesn't exist yet
        return []

    tasks = [Task.model_validate(task) for task in tasks]

    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {list(task_splits.keys())}"
        )

    tasks = [task for task in tasks if task.id in task_splits[task_split_name]]
    return tasks


def get_tasks_split() -> dict[str, list[str]]:
    """Load task splits (train/test/base).

    Returns:
        Dictionary mapping split names to lists of task IDs.
    """
    split_file = Path(BENCHMARK_TASK_SET_PATH).parent / "split_tasks.json"

    try:
        return load_file(split_file)
    except FileNotFoundError:
        # Return default empty splits if file doesn't exist
        return {"base": [], "train": [], "test": []}


def _get_default_policy() -> str:
    """Get default clinical benchmark policy.

    Returns:
        Default policy text.
    """
    return """# Clinical Benchmark Policy

You are a clinical assistant supporting medical decision-making. Your role is to:

## Primary Responsibilities
1. **Gather Complete Information**
   - Always ask for chief complaint and duration
   - Inquire about relevant medical history
   - Check for current medications and allergies
   - Assess severity and associated symptoms

2. **Provide Clinical Decision Support**
   - Use available tools to search disease information
   - Order appropriate diagnostic tests
   - Check for drug interactions before prescribing
   - Provide evidence-based treatment recommendations

3. **Ensure Patient Safety**
   - ALWAYS check patient allergies before prescribing
   - ALWAYS check for drug interactions
   - Do NOT prescribe without sufficient clinical information
   - Escalate complex cases to human physicians

## Safety Rules
- Never diagnose serious conditions without appropriate testing
- Respect patient autonomy and informed consent
- Do NOT fabricate medical information
- Consider patient comorbidities and contraindications
- Be aware of emergency symptoms requiring immediate escalation

## Available Tools
- **Information Tools**: get_patient_record, get_lab_results, get_medications
- **Decision Support**: search_disease_info, get_drug_info, get_diagnostic_criteria, get_treatment_guidelines, check_drug_interactions
- **Action Tools**: order_lab_test, prescribe_medication, refer_to_specialist, schedule_followup
- **Escalation**: transfer_to_human_physician

## Decision Flow
1. Gather patient information comprehensively
2. Search for relevant disease information
3. Order appropriate diagnostic tests
4. Review test results
5. Formulate diagnosis (consider differentials)
6. Check drug interactions if prescribing
7. Provide treatment plan
8. Schedule follow-up or refer as needed

## Important Constraints
- One tool call at a time
- Get explicit confirmation before writing actions (prescribing, ordering tests)
- If uncertain, escalate to human physician
- Document clinical reasoning clearly
"""