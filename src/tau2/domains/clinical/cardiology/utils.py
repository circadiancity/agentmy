"""Utility functions for Clinical Cardiology Domain"""

from pathlib import Path

from tau2.utils.utils import DATA_DIR

DOMAIN_NAME = "clinical_cardiology"
CARDIO_DATA_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "cardiology"

TASKS_PATH = CARDIO_DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = CARDIO_DATA_DIR / "split_tasks.json"
POLICY_PATH = CARDIO_DATA_DIR / "policy.md"
DB_PATH = CARDIO_DATA_DIR / "db.json"

CARDIO_KEYWORDS = [
    "heart", "cardiac", "ecg", "ekg", "echo", "chest pain",
    "blood pressure", "hypertension", "arrhythmia", "palpitation",
    "stent", "catheter", "coronary", "myocardial", "infarction"
]
