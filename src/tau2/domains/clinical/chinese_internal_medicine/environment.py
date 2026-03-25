"""Environment Setup for Clinical Chinese Internal Medicine Domain"""

from pathlib import Path
from typing import Dict, List, Optional

import json
from pydantic import BaseModel

from tau2.data_model.tasks import Task
from tau2.domains.clinical.chinese_internal_medicine.tools import ChineseInternalMedicineTools
from tau2.domains.clinical.chinese_internal_medicine.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools
from tau2.environment.environment import Environment
from tau2.utils import load_file


class PatientRecord(BaseModel):
    """Patient record for Chinese internal medicine"""
    patient_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnoses: List[str] = []
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class ChineseInternalMedicineDB(BaseModel):
    """Chinese Internal Medicine domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "ChineseInternalMedicineDB":
        path = Path(db_path)
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        return self.patients.get(patient_id)


def get_environment(db: Optional[ChineseInternalMedicineDB] = None, solo_mode: bool = False) -> Environment:
    """Create Chinese internal medicine domain environment"""
    if db is None:
        try:
            db = ChineseInternalMedicineDB.load(str(DB_PATH))
        except Exception:
            db = ChineseInternalMedicineDB()
    tools = ChineseInternalMedicineTools(db)

    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(
        domain_name="clinical_chinese_internal_medicine",
        policy=policy,
        tools=tools,
        user_tools=user_tools
    )


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load Chinese internal medicine tasks"""
    tasks = load_file(TASKS_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(f"Invalid split: {task_split_name}")
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """Load task splits"""
    split_file = Path(TASKS_PATH).parent / "split_tasks.json"
    return load_file(split_file)


def _get_default_policy() -> str:
    """Default Chinese internal medicine policy"""
    return """# Clinical Chinese Internal Medicine Domain Policy

## Overview
This domain covers Chinese internal medicine (内科) consultation tasks.

## Clinical Guidelines
- Assess patient symptoms and provide appropriate medical advice
- Consider traditional and modern medical approaches
- Evaluate vital signs and recommend follow-up as needed
- Provide clear explanations in context of the patient's concerns

## Available Tools
- get_patient_by_mrn: Find patients by MRN
- assess_blood_pressure: Classify blood pressure
"""
