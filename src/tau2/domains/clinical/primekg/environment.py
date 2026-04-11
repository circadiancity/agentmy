"""
Environment Setup for PrimeKG Domain
Medical consultation tasks generated from Harvard Medical School PrimeKG knowledge graph
"""

import logging
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.primekg.data_model import ClinicalDB
from tau2.domains.clinical.primekg.tools import ClinicalTools
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools
from tau2.environment.environment import Environment
from tau2.environment.toolkit import ToolKitBase
from tau2.utils import DATA_DIR, load_file

logger = logging.getLogger(__name__)

# === PATHS ===
DOMAIN_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "primekg"
TASKS_PATH = DOMAIN_DIR / "tasks.json"
SPLIT_PATH = DOMAIN_DIR / "split_tasks.json"
POLICY_PATH = DOMAIN_DIR / "policy.md"
DB_PATH = DOMAIN_DIR / "db.json"


def get_environment(solo_mode: bool = False) -> Environment:
    """
    Create and configure the PrimeKG domain environment.

    Args:
        solo_mode: Whether to run in solo mode (agent handles user interactions)

    Returns:
        Configured Environment instance
    """
    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    # Load clinical database and create tools
    try:
        clinical_db = ClinicalDB.load(str(DB_PATH))
        tools = ClinicalTools(clinical_db)
        logger.info(
            "Loaded ClinicalDB: %s", clinical_db.get_statistics()
        )
    except Exception as e:
        logger.warning("Failed to load ClinicalDB from %s: %s. Using empty DB.", DB_PATH, e)
        clinical_db = ClinicalDB()
        tools = ClinicalTools(clinical_db)

    # Load policy
    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()

    # Create environment
    env = Environment(
        domain_name="primekg",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        solo_mode=solo_mode,
    )

    return env


def _get_default_policy() -> str:
    """Fallback policy if policy.md cannot be loaded."""
    return (
        "# PrimeKG Clinical Consultation Policy\n\n"
        "You are a clinical consultation AI assistant. Follow standard clinical workflow: "
        "gather patient information, assess symptoms, order diagnostics, form diagnosis, "
        "plan treatment with safety checks, and arrange follow-up.\n"
    )


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """
    Load PrimeKG domain tasks.

    Args:
        task_split_name: Optional task split name (e.g., "train", "test")

    Returns:
        List of Task objects
    """
    import json

    # Load all tasks with explicit UTF-8 encoding
    with open(TASKS_PATH, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)

    all_tasks = [Task(**task) for task in tasks_data]

    # If no split specified, return all tasks
    if task_split_name is None:
        return all_tasks

    # Load split and filter
    with open(SPLIT_PATH, 'r', encoding='utf-8') as f:
        split_data = json.load(f)

    # "base" means all tasks — return unfiltered
    if task_split_name == "base":
        return all_tasks

    if task_split_name not in split_data:
        raise ValueError(f"Invalid split name: {task_split_name}. Must be one of {list(split_data.keys()) + ['base']}")

    split_ids = split_data[task_split_name]
    # Handle both formats: list of ID strings or list of task objects
    task_ids = set()
    for item in split_ids:
        if isinstance(item, str):
            task_ids.add(item)
        elif isinstance(item, dict) and "id" in item:
            task_ids.add(item["id"])
    filtered_tasks = [t for t in all_tasks if t.id in task_ids]

    return filtered_tasks


def get_tasks_split() -> dict[str, list[str]]:
    """
    Get the train/test split for PrimeKG tasks.

    Returns:
        Dictionary with 'train' and 'test' keys containing lists of task IDs
    """
    import json

    with open(SPLIT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
