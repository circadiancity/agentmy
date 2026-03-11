"""Utility functions for Clinical Endocrinology Domain"""

from pathlib import Path

from tau2.utils.utils import DATA_DIR

DOMAIN_NAME = "clinical_endocrinology"
ENDO_DATA_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "endocrinology"

TASKS_PATH = ENDO_DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = ENDO_DATA_DIR / "split_tasks.json"
POLICY_PATH = ENDO_DATA_DIR / "policy.md"
DB_PATH = ENDO_DATA_DIR / "db.json"

ENDO_KEYWORDS = [
    "diabetes", "thyroid", "hormone", "insulin", "glucose",
    "hba1c", "tsh", "t4", "metabolism", "cortisol", "parathyroid"
]
