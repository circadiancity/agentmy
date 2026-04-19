"""Data models for the clinical benchmark domain."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from tau2.environment.db import DB


class VitalSigns(BaseModel):
    """Patient vital signs."""

    blood_pressure: Optional[str] = Field(default=None, description="BP in mmHg (e.g., '130/80')")
    heart_rate: Optional[str] = Field(default=None, description="HR in bpm")
    temperature: Optional[str] = Field(default=None, description="Temperature in Celsius")
    respiratory_rate: Optional[str] = Field(default=None, description="RR in breaths/min")
    oxygen_saturation: Optional[str] = Field(default=None, description="SpO2 percentage")


class LabResult(BaseModel):
    """A single laboratory result."""

    test_name: str = Field(description="Name of the lab test (e.g., 'WBC', 'Hemoglobin')")
    value: str = Field(description="Result value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    reference_range: Optional[str] = Field(default=None, description="Normal reference range")
    abnormal: bool = Field(default=False, description="Whether result is abnormal")


class Medication(BaseModel):
    """Current medication information."""

    drug_name: str = Field(description="Name of the medication")
    dose: str = Field(description="Dosage")
    frequency: str = Field(description="Frequency (e.g., 'once daily')")
    indication: Optional[str] = Field(default=None, description="What it's prescribed for")


class PatientRecord(BaseModel):
    """A patient record with medical information."""

    patient_id: str = Field(description="Unique patient identifier")
    name: str = Field(description="Patient name")
    age: int = Field(description="Patient age in years")
    gender: str = Field(description="Patient gender (M/F)")
    chief_complaint: str = Field(description="Chief complaint")
    symptoms: List[str] = Field(default_factory=list, description="Current symptoms")
    vitals: VitalSigns = Field(default_factory=VitalSigns, description="Vital signs")
    lab_results: Dict[str, LabResult] = Field(
        default_factory=dict, description="Dictionary of lab results by test name"
    )
    past_medical_history: List[str] = Field(
        default_factory=list, description="PMH conditions"
    )
    current_medications: List[Medication] = Field(
        default_factory=list, description="Current medications"
    )
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    orders: List[Dict[str, Any]] = Field(
        default_factory=list, description="Ordered tests/prescriptions"
    )
    referrals: List[Dict[str, str]] = Field(
        default_factory=list, description="Specialist referrals"
    )


class DrugInfo(BaseModel):
    """Information about a drug."""

    drug_id: str = Field(description="Unique drug identifier")
    name: str = Field(description="Drug name")
    class_: str = Field(description="Drug class")
    indications: List[str] = Field(default_factory=list, description="Indications")
    contraindications: List[str] = Field(
        default_factory=list, description="Contraindications"
    )
    common_side_effects: List[str] = Field(
        default_factory=list, description="Common side effects"
    )
    interactions: List[str] = Field(
        default_factory=list, description="Known drug interactions"
    )


class DiseaseInfo(BaseModel):
    """Information about a disease."""

    disease_id: str = Field(description="Unique disease identifier")
    name: str = Field(description="Disease name")
    symptoms: List[str] = Field(default_factory=list, description="Common symptoms")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    diagnostic_criteria: Optional[str] = Field(
        default=None, description="Diagnostic criteria"
    )
    treatment_options: List[str] = Field(
        default_factory=list, description="Treatment options"
    )
    prevalence: Optional[str] = Field(default=None, description="Prevalence information")


class BenchmarkDB(DB):
    """Database for the clinical benchmark domain."""

    patients: Dict[str, PatientRecord] = Field(
        default_factory=dict, description="Dictionary of patients by ID"
    )
    drugs: Dict[str, DrugInfo] = Field(
        default_factory=dict, description="Dictionary of drugs by ID"
    )
    diseases: Dict[str, DiseaseInfo] = Field(
        default_factory=dict, description="Dictionary of diseases by ID"
    )

    @classmethod
    def load(cls, db_path: str) -> "BenchmarkDB":
        """Load database from JSON file.

        Args:
            db_path: Path to the db.json file.

        Returns:
            BenchmarkDB instance.
        """
        import json
        from pathlib import Path

        db_path = Path(db_path)
        if db_path.exists():
            with open(db_path, "r") as f:
                data = json.load(f)
            return cls.model_validate(data)
        return cls()
