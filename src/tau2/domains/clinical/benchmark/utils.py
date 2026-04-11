"""Path constants for the clinical benchmark domain."""

from pathlib import Path

from tau2.utils.utils import DATA_DIR

BENCHMARK_DATA_DIR = DATA_DIR / "tau2" / "domains" / "clinical" / "benchmark"
BENCHMARK_DB_PATH = BENCHMARK_DATA_DIR / "db.json"
BENCHMARK_POLICY_PATH = BENCHMARK_DATA_DIR / "policy.md"
BENCHMARK_TASK_SET_PATH = BENCHMARK_DATA_DIR / "tasks.json"
BENCHMARK_KNOWLEDGE_BASE_PATH = BENCHMARK_DATA_DIR / "knowledge_base.json"
