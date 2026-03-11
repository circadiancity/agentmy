"""
Utility functions for Clinical Gastroenterology Domain
"""

from pathlib import Path

from tau2.utils.utils import DATA_DIR

DOMAIN_NAME = "clinical_gastroenterology"
GASTRO_DATA_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "gastroenterology"

TASKS_PATH = GASTRO_DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = GASTRO_DATA_DIR / "split_tasks.json"
POLICY_PATH = GASTRO_DATA_DIR / "policy.md"
DB_PATH = GASTRO_DATA_DIR / "db.json"

GASTRO_KEYWORDS = [
    "gi", "gastro", "stomach", "digestive", "liver", "hepat",
    "pancreatit", "colon", "diarrhea", "constipat", "endoscop",
    "egd", "colonoscop", "cirrhos", "hepatit", "bilrubin"
]
