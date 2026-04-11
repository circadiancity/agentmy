"""Data models for the PrimeKG clinical domain."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from tau2.environment.db import DB


# === Patient Records ===

class PatientVitals(BaseModel):
    """Patient vital signs."""
    blood_pressure: str = Field(description="Blood pressure (e.g., '120/80')")
    heart_rate: int = Field(description="Heart rate in bpm")
    temperature: float = Field(description="Temperature in Fahrenheit")
    respiratory_rate: int = Field(description="Respiratory rate per minute")
    spo2: float = Field(description="Oxygen saturation percentage")
    weight_kg: float = Field(description="Weight in kilograms")
    height_cm: float = Field(description="Height in centimeters")


class PatientHistory(BaseModel):
    """Patient medical history."""
    past_medical: List[str] = Field(default_factory=list, description="Past medical conditions")
    surgical: List[str] = Field(default_factory=list, description="Past surgical procedures")
    family: List[str] = Field(default_factory=list, description="Family medical history")
    social: Dict[str, str] = Field(default_factory=dict, description="Social history (smoking, alcohol, etc.)")


class PatientRecord(BaseModel):
    """A patient record in the clinical database."""
    patient_id: str = Field(description="Unique patient identifier")
    name: str = Field(description="Patient full name")
    age: int = Field(description="Patient age")
    gender: str = Field(description="Patient gender")
    chief_complaint: str = Field(description="Primary reason for visit")
    vitals: PatientVitals = Field(description="Current vital signs")
    history: PatientHistory = Field(description="Medical history")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    current_medications: List[str] = Field(default_factory=list, description="Current medications")
    conditions: List[str] = Field(default_factory=list, description="Active conditions/diagnoses")
    insurance: Optional[str] = Field(None, description="Insurance provider")


# === Lab Results ===

class LabTestTemplate(BaseModel):
    """Template for a lab test with reference ranges."""
    test_name: str = Field(description="Name of the lab test")
    category: str = Field(description="Test category (e.g., 'hematology', 'chemistry')")
    unit: str = Field(description="Unit of measurement")
    reference_range: str = Field(description="Normal reference range")
    components: Optional[Dict[str, Dict[str, str]]] = Field(
        None, description="Sub-components with their own ranges (e.g., CBC components)"
    )


class PatientLabResult(BaseModel):
    """A lab result for a specific patient."""
    test_name: str = Field(description="Name of the lab test")
    values: Dict[str, str] = Field(description="Test values (component -> value)")
    interpretation: str = Field(description="Normal/Abnormal/Critical")
    notes: Optional[str] = Field(None, description="Additional clinical notes")


# === Drug Database ===

class DrugEntry(BaseModel):
    """A drug entry in the clinical database."""
    drug_name: str = Field(description="Generic drug name")
    brand_names: List[str] = Field(default_factory=list, description="Brand names")
    drug_class: str = Field(description="Pharmacological class")
    indications: List[str] = Field(description="Approved indications")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    common_side_effects: List[str] = Field(default_factory=list, description="Common side effects")
    serious_side_effects: List[str] = Field(default_factory=list, description="Serious/rare side effects")
    interactions: Dict[str, str] = Field(
        default_factory=dict,
        description="Drug interactions: drug_name -> severity (minor/moderate/major)"
    )
    typical_dose: str = Field(description="Typical adult dosing")
    pregnancy_category: Optional[str] = Field(None, description="FDA pregnancy category")


# === Disease Database ===

class DiseaseEntry(BaseModel):
    """A disease entry in the clinical database."""
    disease_name: str = Field(description="Disease name")
    icd10_code: str = Field(description="ICD-10 code")
    description: str = Field(description="Disease description")
    typical_symptoms: List[str] = Field(description="Common symptoms")
    diagnostic_criteria: List[str] = Field(default_factory=list, description="Diagnostic criteria")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    complications: List[str] = Field(default_factory=list, description="Potential complications")
    category: str = Field(description="Medical specialty/category")


# === Imaging ===

class ImagingTemplate(BaseModel):
    """Template for an imaging study."""
    imaging_type: str = Field(description="Type of imaging (X-ray, CT, MRI, Ultrasound)")
    body_region: str = Field(description="Body region")
    description: str = Field(description="What the study evaluates")
    typical_indications: List[str] = Field(description="Common indications for ordering")


class PatientImagingResult(BaseModel):
    """An imaging result for a specific patient."""
    imaging_type: str = Field(description="Type of imaging performed")
    body_region: str = Field(description="Body region imaged")
    findings: str = Field(description="Radiological findings")
    impression: str = Field(description="Radiologist impression")


# === Treatment Guidelines ===

class TreatmentGuideline(BaseModel):
    """Treatment guideline for a condition."""
    condition: str = Field(description="Condition name")
    first_line: List[str] = Field(description="First-line treatments")
    second_line: List[str] = Field(default_factory=list, description="Second-line treatments")
    lifestyle_modifications: List[str] = Field(default_factory=list, description="Lifestyle changes")
    monitoring: List[str] = Field(default_factory=list, description="Monitoring recommendations")
    referral_criteria: List[str] = Field(default_factory=list, description="When to refer to specialist")
    red_flags: List[str] = Field(default_factory=list, description="Red flags requiring urgent action")


# === Clinical Actions (recorded by agent) ===

class RecordedDiagnosis(BaseModel):
    """A diagnosis recorded by the agent."""
    diagnosis: str = Field(description="Diagnosis name")
    confidence: str = Field(description="Confidence level: high/moderate/low")
    reasoning: str = Field(description="Clinical reasoning")


class RecordedPrescription(BaseModel):
    """A prescription recorded by the agent."""
    drug_name: str = Field(description="Drug prescribed")
    dose: str = Field(description="Dosage")
    frequency: str = Field(description="Frequency")
    duration: str = Field(description="Duration")
    allergy_checked: bool = Field(default=False, description="Whether allergy check was performed")
    interaction_checked: bool = Field(default=False, description="Whether interaction check was performed")


class RecordedReferral(BaseModel):
    """A specialist referral recorded by the agent."""
    specialty: str = Field(description="Specialty referred to")
    reason: str = Field(description="Reason for referral")


class RecordedFollowUp(BaseModel):
    """A follow-up plan recorded by the agent."""
    plan: str = Field(description="Follow-up plan details")
    timeframe: str = Field(description="Follow-up timeframe")


# === Main Database ===

class ClinicalDB(DB):
    """Complete clinical database for the PrimeKG domain."""

    patients: Dict[str, PatientRecord] = Field(
        default_factory=dict, description="Patient records indexed by patient_id"
    )
    lab_catalog: Dict[str, LabTestTemplate] = Field(
        default_factory=dict, description="Available lab tests indexed by test name"
    )
    patient_labs: Dict[str, List[PatientLabResult]] = Field(
        default_factory=dict, description="Patient lab results indexed by patient_id"
    )
    patient_imaging: Dict[str, List[PatientImagingResult]] = Field(
        default_factory=dict, description="Patient imaging results indexed by patient_id"
    )
    drugs: Dict[str, DrugEntry] = Field(
        default_factory=dict, description="Drug database indexed by generic name"
    )
    diseases: Dict[str, DiseaseEntry] = Field(
        default_factory=dict, description="Disease database indexed by disease name"
    )
    imaging_catalog: Dict[str, ImagingTemplate] = Field(
        default_factory=dict, description="Available imaging studies indexed by key"
    )
    treatment_guidelines: Dict[str, TreatmentGuideline] = Field(
        default_factory=dict, description="Treatment guidelines indexed by condition"
    )
    # Recorded actions (populated during agent interaction)
    recorded_diagnoses: Dict[str, List[RecordedDiagnosis]] = Field(
        default_factory=dict, description="Recorded diagnoses by patient_id"
    )
    recorded_differentials: Dict[str, List[str]] = Field(
        default_factory=dict, description="Recorded differential diagnoses by patient_id"
    )
    recorded_prescriptions: Dict[str, List[RecordedPrescription]] = Field(
        default_factory=dict, description="Recorded prescriptions by patient_id"
    )
    recorded_referrals: Dict[str, List[RecordedReferral]] = Field(
        default_factory=dict, description="Recorded referrals by patient_id"
    )
    recorded_follow_ups: Dict[str, List[RecordedFollowUp]] = Field(
        default_factory=dict, description="Recorded follow-up plans by patient_id"
    )
    ordered_labs: Dict[str, List[str]] = Field(
        default_factory=dict, description="Labs ordered (patient_id -> list of test names)"
    )
    ordered_imaging: Dict[str, List[str]] = Field(
        default_factory=dict, description="Imaging ordered (patient_id -> list of study keys)"
    )

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the clinical database."""
        return {
            "num_patients": len(self.patients),
            "num_lab_tests": len(self.lab_catalog),
            "num_drugs": len(self.drugs),
            "num_diseases": len(self.diseases),
            "num_imaging_types": len(self.imaging_catalog),
            "num_treatment_guidelines": len(self.treatment_guidelines),
        }
