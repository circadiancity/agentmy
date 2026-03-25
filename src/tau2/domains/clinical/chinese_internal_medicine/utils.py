"""Utility functions for Clinical Chinese Internal Medicine Domain"""

from pathlib import Path

from tau2.utils.utils import DATA_DIR

DOMAIN_NAME = "clinical_chinese_internal_medicine"
CHINESE_IM_DATA_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "chinese_internal_medicine"

TASKS_PATH = CHINESE_IM_DATA_DIR / "tasks_advanced.json"
SPLIT_TASKS_PATH = CHINESE_IM_DATA_DIR / "split_tasks.json"
POLICY_PATH = CHINESE_IM_DATA_DIR / "policy.md"
DB_PATH = CHINESE_IM_DATA_DIR / "db.json"
