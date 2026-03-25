"""Clinical Tools for Chinese Internal Medicine Domain"""

from typing import Optional, TYPE_CHECKING
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool

if TYPE_CHECKING:
    from tau2.domains.clinical.chinese_internal_medicine.environment import ChineseInternalMedicineDB


class ChineseInternalMedicineTools(ToolKitBase):
    """Clinical tools for Chinese internal medicine domain"""
    db: 'ChineseInternalMedicineDB'

    def __init__(self, db: 'ChineseInternalMedicineDB') -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_patient_by_mrn(self, mrn: str) -> dict:
        """Find patient by MRN

        Args:
            mrn: Medical Record Number

        Returns:
            Patient information
        """
        for patient_id, patient in self.db.patients.items():
            if patient.patient_id == mrn:
                return {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "diagnoses": patient.diagnoses,
                    "chief_complaint": patient.chief_complaint,
                    "medications": patient.medications
                }
        raise ValueError(f"Patient with MRN {mrn} not found")

    @is_tool(ToolType.READ)
    def assess_blood_pressure(self, systolic: int, diastolic: int, age: int) -> dict:
        """Assess blood pressure and provide classification.

        Args:
            systolic: Systolic BP in mmHg
            diastolic: Diastolic BP in mmHg
            age: Patient age

        Returns:
            BP classification with recommendations
        """
        if systolic < 120 and diastolic < 80:
            category = "Normal"
            recommendation = "Continue healthy lifestyle"
        elif systolic < 130 and diastolic < 80:
            category = "Elevated"
            recommendation = "Lifestyle modifications recommended"
        elif systolic < 140 or diastolic < 90:
            category = "Hypertension Stage 1"
            recommendation = "Lifestyle changes, consider medication"
        elif systolic < 180 or diastolic < 120:
            category = "Hypertension Stage 2"
            recommendation = "Medication likely required"
        else:
            category = "Hypertensive Crisis"
            recommendation = "Immediate medical attention required"

        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "category": category,
            "recommendation": recommendation
        }
