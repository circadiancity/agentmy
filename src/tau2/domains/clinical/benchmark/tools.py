"""Clinical benchmark tools for medical consultation agents."""

import json
from typing import Dict, List, Optional

from tau2.domains.clinical.benchmark.data_model import BenchmarkDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class ClinicalBenchmarkTools(ToolKitBase):
    """Tools for clinical consultation and decision support."""

    db: BenchmarkDB

    def __init__(self, db: BenchmarkDB) -> None:
        super().__init__(db)

    # ==================== Helper Methods ====================

    def _get_patient(self, patient_id: str):
        """Get patient by ID."""
        if patient_id not in self.db.patients:
            raise ValueError(f"Patient {patient_id} not found")
        return self.db.patients[patient_id]

    def _get_drug(self, drug_name: str):
        """Get drug info by name."""
        for drug in self.db.drugs.values():
            if drug.name.lower() == drug_name.lower():
                return drug
        raise ValueError(f"Drug {drug_name} not found")

    def _get_disease(self, disease_name: str):
        """Get disease info by name."""
        for disease in self.db.diseases.values():
            if disease.name.lower() == disease_name.lower():
                return disease
        raise ValueError(f"Disease {disease_name} not found")

    # ==================== Patient Information Tools ====================

    @is_tool(ToolType.READ)
    def get_patient_record(self, patient_id: str) -> str:
        """Get complete patient record with vitals, history, medications, and allergies.

        Args:
            patient_id: The patient identifier.

        Returns:
            JSON string containing complete patient information.
        """
        patient = self._get_patient(patient_id)
        record = {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "chief_complaint": patient.chief_complaint,
            "symptoms": patient.symptoms,
            "vitals": patient.vitals.model_dump(exclude_none=True),
            "past_medical_history": patient.past_medical_history,
            "current_medications": [
                {
                    "name": m.drug_name,
                    "dose": m.dose,
                    "frequency": m.frequency,
                    "indication": m.indication,
                }
                for m in patient.current_medications
            ],
            "allergies": patient.allergies,
        }
        return json.dumps(record, indent=2)

    @is_tool(ToolType.READ)
    def get_lab_results(self, patient_id: str, test_name: Optional[str] = None) -> str:
        """Get laboratory results for a patient.

        Args:
            patient_id: The patient identifier.
            test_name: Optional specific test name (e.g., 'CBC', 'BMP'). If None, returns all results.

        Returns:
            JSON string containing lab results.
        """
        patient = self._get_patient(patient_id)

        if test_name:
            if test_name not in patient.lab_results:
                return json.dumps(
                    {"error": f"Lab test {test_name} not found for patient"},
                    indent=2,
                )
            result = patient.lab_results[test_name]
            return json.dumps(result.model_dump(), indent=2)
        else:
            results = {
                name: result.model_dump()
                for name, result in patient.lab_results.items()
            }
            return json.dumps(results, indent=2)

    @is_tool(ToolType.READ)
    def get_medications(self, patient_id: str) -> str:
        """Get current medications for a patient.

        Args:
            patient_id: The patient identifier.

        Returns:
            JSON string containing current medications.
        """
        patient = self._get_patient(patient_id)
        meds = [
            {
                "name": m.drug_name,
                "dose": m.dose,
                "frequency": m.frequency,
                "indication": m.indication,
            }
            for m in patient.current_medications
        ]
        return json.dumps({"medications": meds}, indent=2)

    # ==================== Clinical Decision Support Tools ====================

    @is_tool(ToolType.READ)
    def search_disease_info(self, disease_name: str) -> str:
        """Search for disease information including symptoms, risk factors, and treatment.

        Args:
            disease_name: Name of the disease to search for.

        Returns:
            JSON string containing disease information.
        """
        try:
            disease = self._get_disease(disease_name)
            info = {
                "disease": disease.name,
                "symptoms": disease.symptoms,
                "risk_factors": disease.risk_factors,
                "diagnostic_criteria": disease.diagnostic_criteria,
                "treatment_options": disease.treatment_options,
                "prevalence": disease.prevalence,
            }
            return json.dumps(info, indent=2)
        except ValueError:
            return json.dumps(
                {
                    "error": f"Disease information for {disease_name} not found in knowledge base"
                },
                indent=2,
            )

    @is_tool(ToolType.READ)
    def check_drug_interactions(self, drug_names: List[str]) -> str:
        """Check for potential drug interactions between multiple drugs.

        Args:
            drug_names: List of drug names to check.

        Returns:
            JSON string with interaction information.
        """
        drugs = []
        interactions = []

        for drug_name in drug_names:
            try:
                drug = self._get_drug(drug_name)
                drugs.append({"name": drug.name, "class": drug.class_})
                if drug.interactions:
                    for interaction in drug.interactions:
                        if any(d.lower() in interaction.lower() for d in drug_names):
                            interactions.append(
                                {
                                    "drugs": f"{drug.name} + other agent",
                                    "interaction": interaction,
                                    "severity": "moderate",
                                }
                            )
            except ValueError:
                pass

        return json.dumps(
            {
                "drugs_checked": drugs,
                "interactions_found": len(interactions),
                "interactions": interactions if interactions else "No major interactions found",
            },
            indent=2,
        )

    @is_tool(ToolType.READ)
    def get_drug_info(self, drug_name: str) -> str:
        """Get detailed information about a specific drug.

        Args:
            drug_name: Name of the drug.

        Returns:
            JSON string containing drug information.
        """
        try:
            drug = self._get_drug(drug_name)
            info = {
                "drug": drug.name,
                "class": drug.class_,
                "indications": drug.indications,
                "contraindications": drug.contraindications,
                "common_side_effects": drug.common_side_effects,
                "interactions": drug.interactions,
            }
            return json.dumps(info, indent=2)
        except ValueError:
            return json.dumps(
                {"error": f"Drug information for {drug_name} not found"},
                indent=2,
            )

    @is_tool(ToolType.READ)
    def get_diagnostic_criteria(self, disease_name: str) -> str:
        """Get diagnostic criteria for a disease.

        Args:
            disease_name: Name of the disease.

        Returns:
            JSON string containing diagnostic criteria.
        """
        try:
            disease = self._get_disease(disease_name)
            return json.dumps(
                {
                    "disease": disease.name,
                    "diagnostic_criteria": disease.diagnostic_criteria or "Criteria not available",
                    "common_tests": [
                        "History and physical exam",
                        "Lab work as indicated",
                        "Imaging as indicated",
                    ],
                },
                indent=2,
            )
        except ValueError:
            return json.dumps(
                {"error": f"Diagnostic criteria for {disease_name} not found"},
                indent=2,
            )

    @is_tool(ToolType.READ)
    def get_treatment_guidelines(
        self, disease_name: str, patient_context: Optional[str] = None
    ) -> str:
        """Get evidence-based treatment guidelines for a disease.

        Args:
            disease_name: Name of the disease.
            patient_context: Optional patient context (e.g., 'elderly', 'pregnant').

        Returns:
            JSON string containing treatment guidelines.
        """
        try:
            disease = self._get_disease(disease_name)
            return json.dumps(
                {
                    "disease": disease.name,
                    "treatment_options": disease.treatment_options,
                    "patient_context": patient_context or "General population",
                    "follow_up": "Reassess at next visit or as clinically indicated",
                },
                indent=2,
            )
        except ValueError:
            return json.dumps(
                {"error": f"Treatment guidelines for {disease_name} not found"},
                indent=2,
            )

    # ==================== Clinical Action Tools ====================

    @is_tool(ToolType.WRITE)
    def order_lab_test(self, patient_id: str, test_name: str, urgency: str = "routine") -> str:
        """Order a laboratory test for a patient.

        Args:
            patient_id: The patient identifier.
            test_name: Name of the test to order (e.g., 'CBC', 'BMP', 'TSH').
            urgency: Urgency level ('routine', 'stat', 'urgent').

        Returns:
            Confirmation message with order details.
        """
        patient = self._get_patient(patient_id)
        order = {
            "type": "lab_test",
            "test_name": test_name,
            "patient_id": patient_id,
            "urgency": urgency,
            "status": "pending",
        }
        patient.orders.append(order)
        self.db.patients[patient_id] = patient

        return json.dumps(
            {
                "status": "success",
                "message": f"Lab test '{test_name}' ordered for {patient.name}",
                "urgency": urgency,
                "order_id": f"LAB_{len(patient.orders)}",
            },
            indent=2,
        )

    @is_tool(ToolType.WRITE)
    def prescribe_medication(
        self,
        patient_id: str,
        drug_name: str,
        dose: str,
        duration: str,
        indication: Optional[str] = None,
    ) -> str:
        """Prescribe medication for a patient.

        Args:
            patient_id: The patient identifier.
            drug_name: Name of the drug to prescribe.
            dose: Dosage (e.g., '500mg').
            duration: Duration of treatment (e.g., '7 days', '30 days').
            indication: Medical indication for the prescription.

        Returns:
            Confirmation message with prescription details.
        """
        patient = self._get_patient(patient_id)

        # Check for allergies
        if any(allergy.lower() in drug_name.lower() for allergy in patient.allergies):
            return json.dumps(
                {
                    "status": "error",
                    "message": f"ALLERGY ALERT: Patient is allergic to {drug_name}",
                },
                indent=2,
            )

        order = {
            "type": "prescription",
            "drug_name": drug_name,
            "dose": dose,
            "duration": duration,
            "indication": indication,
            "patient_id": patient_id,
            "status": "pending",
        }
        patient.orders.append(order)
        self.db.patients[patient_id] = patient

        return json.dumps(
            {
                "status": "success",
                "message": f"Medication '{drug_name}' prescribed for {patient.name}",
                "dose": dose,
                "duration": duration,
                "indication": indication or "Not specified",
                "order_id": f"RX_{len(patient.orders)}",
            },
            indent=2,
        )

    @is_tool(ToolType.WRITE)
    def refer_to_specialist(
        self, patient_id: str, specialty: str, reason: str
    ) -> str:
        """Refer patient to a specialist.

        Args:
            patient_id: The patient identifier.
            specialty: Medical specialty (e.g., 'Cardiology', 'Neurology').
            reason: Clinical reason for referral.

        Returns:
            Confirmation message with referral details.
        """
        patient = self._get_patient(patient_id)
        referral = {
            "specialty": specialty,
            "reason": reason,
            "patient_id": patient_id,
            "status": "pending",
        }
        patient.referrals.append(referral)
        self.db.patients[patient_id] = patient

        return json.dumps(
            {
                "status": "success",
                "message": f"Referral to {specialty} sent for {patient.name}",
                "reason": reason,
                "referral_id": f"REF_{len(patient.referrals)}",
            },
            indent=2,
        )

    @is_tool(ToolType.WRITE)
    def schedule_followup(
        self, patient_id: str, timeframe: str, reason: str
    ) -> str:
        """Schedule follow-up appointment for patient.

        Args:
            patient_id: The patient identifier.
            timeframe: When to schedule (e.g., '1 week', '2 months').
            reason: Reason for follow-up.

        Returns:
            Confirmation message with appointment details.
        """
        patient = self._get_patient(patient_id)
        appointment = {
            "type": "follow_up",
            "timeframe": timeframe,
            "reason": reason,
            "patient_id": patient_id,
            "status": "scheduled",
        }
        patient.orders.append(appointment)
        self.db.patients[patient_id] = patient

        return json.dumps(
            {
                "status": "success",
                "message": f"Follow-up scheduled for {patient.name}",
                "timeframe": timeframe,
                "reason": reason,
                "appointment_id": f"APT_{len(patient.orders)}",
            },
            indent=2,
        )

    # ==================== Escalation Tool ====================

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_physician(self, summary: str) -> str:
        """Transfer case to human physician for complex cases.

        Args:
            summary: Summary of the case and reason for escalation.

        Returns:
            Confirmation message.
        """
        return json.dumps(
            {
                "status": "success",
                "message": "Case transferred to human physician",
                "summary_received": summary[:100] + "..." if len(summary) > 100 else summary,
                "next_action": "Physician will review and contact patient shortly",
            },
            indent=2,
        )
