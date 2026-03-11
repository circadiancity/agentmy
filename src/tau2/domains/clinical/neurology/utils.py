"""Utility functions for Clinical Neurology Domain"""

from pathlib import Path

from tau2.utils.utils import DATA_DIR

DOMAIN_NAME = "clinical_neurology"
NEURO_DATA_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "neurology"

TASKS_PATH = NEURO_DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = NEURO_DATA_DIR / "split_tasks.json"
POLICY_PATH = NEURO_DATA_DIR / "policy.md"
DB_PATH = NEURO_DATA_DIR / "db.json"

NEURO_KEYWORDS = [
    "brain", "neuro", "seizure", "stroke", "headache", "migraine",
    "neural", "cognitive", "dementia", "parkinson", "multiple sclerosis",
    "concussion", "spinal", "nerve", "numbness", "weakness"
]
