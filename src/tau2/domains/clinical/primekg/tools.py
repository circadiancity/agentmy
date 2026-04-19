"""Comprehensive clinical toolkit for the PrimeKG domain."""

from typing import Dict, List, Optional

from tau2.domains.clinical.primekg.data_model import (
    ClinicalDB,
    PatientRecord,
    RecordedDiagnosis,
    RecordedFollowUp,
    RecordedPrescription,
    RecordedReferral,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class ClinicalTools(ToolKitBase):
    """Clinical tools for the PrimeKG domain.

    Provides patient access, diagnostic, knowledge lookup, clinical action,
    and safety tools for realistic clinical workflows.
    """

    db: ClinicalDB

    def __init__(self, db: ClinicalDB) -> None:
        super().__init__(db)

    # === Private Helpers ===

    def _get_patient(self, patient_id: str) -> PatientRecord:
        """Get a patient record from the database.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            The patient record.

        Raises:
            ValueError: If the patient is not found.
        """
        if patient_id not in self.db.patients:
            raise ValueError(f"Patient '{patient_id}' not found")
        return self.db.patients[patient_id]

    def _normalize_key(self, key: str) -> str:
        """Normalize a lookup key to lowercase with underscores."""
        return key.strip().lower().replace(" ", "_").replace("-", "_")

    def _fuzzy_lookup(self, query: str, candidates: Dict[str, object]) -> Optional[str]:
        """Find the best matching key in a dictionary using normalized matching.

        Args:
            query: The search query.
            candidates: Dictionary to search in.

        Returns:
            The matching key, or None if not found.
        """
        norm_query = self._normalize_key(query)
        # Exact normalized match
        for key in candidates:
            if self._normalize_key(key) == norm_query:
                return key
        # Substring match
        for key in candidates:
            norm_key = self._normalize_key(key)
            if norm_query in norm_key or norm_key in norm_query:
                return key
        return None

    # =========================================================================
    # Patient Access Tools (READ)
    # =========================================================================

    @is_tool(ToolType.READ)
    def get_patient_info(self, patient_id: str) -> dict:
        """Get patient demographics, chief complaint, and overview.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            Dictionary with patient demographics and chief complaint.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        return {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "chief_complaint": patient.chief_complaint,
            "active_conditions": patient.conditions,
            "insurance": patient.insurance,
        }

    @is_tool(ToolType.READ)
    def get_patient_vitals(self, patient_id: str) -> dict:
        """Get patient vital signs including BP, HR, temperature, SpO2, and BMI.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            Dictionary with vital signs and calculated BMI.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        v = patient.vitals
        bmi = round(v.weight_kg / ((v.height_cm / 100) ** 2), 1)
        return {
            "patient_id": patient_id,
            "blood_pressure": v.blood_pressure,
            "heart_rate": v.heart_rate,
            "temperature_f": v.temperature,
            "respiratory_rate": v.respiratory_rate,
            "spo2": v.spo2,
            "weight_kg": v.weight_kg,
            "height_cm": v.height_cm,
            "bmi": bmi,
        }

    @is_tool(ToolType.READ)
    def get_patient_medications(self, patient_id: str) -> dict:
        """Get the patient's current medication list.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            Dictionary with the list of current medications.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        return {
            "patient_id": patient_id,
            "current_medications": patient.current_medications,
        }

    @is_tool(ToolType.READ)
    def get_patient_allergies(self, patient_id: str) -> dict:
        """Get the patient's allergy list.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            Dictionary with the list of known allergies.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        return {
            "patient_id": patient_id,
            "allergies": patient.allergies,
        }

    @is_tool(ToolType.READ)
    def get_patient_history(self, patient_id: str) -> dict:
        """Get patient's past medical, surgical, family, and social history.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            Dictionary with full medical history.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        h = patient.history
        return {
            "patient_id": patient_id,
            "past_medical_history": h.past_medical,
            "surgical_history": h.surgical,
            "family_history": h.family,
            "social_history": h.social,
        }

    # =========================================================================
    # Diagnostic Tools (READ)
    # =========================================================================

    @is_tool(ToolType.READ)
    def order_lab_test(self, patient_id: str, test_name: str) -> dict:
        """Order a laboratory test and get results from pre-populated data.

        Available tests include: CBC, BMP, CMP, LFTs, lipid_panel, HbA1c,
        TSH, urinalysis, troponin, BNP, coagulation, ESR_CRP, iron_studies,
        thyroid_panel, blood_glucose, and others in the lab catalog.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            test_name: Name of the lab test to order (e.g., 'CBC', 'BMP', 'HbA1c').

        Returns:
            Dictionary with test results and interpretation.

        Raises:
            ValueError: If the patient is not found or the test is not available.
        """
        patient = self._get_patient(patient_id)

        # Track ordered labs
        if patient_id not in self.db.ordered_labs:
            self.db.ordered_labs[patient_id] = []
        self.db.ordered_labs[patient_id].append(test_name)

        # Look up pre-populated results
        if patient_id in self.db.patient_labs:
            for lab in self.db.patient_labs[patient_id]:
                if self._normalize_key(lab.test_name) == self._normalize_key(test_name):
                    # Get reference ranges from catalog
                    catalog_key = self._fuzzy_lookup(test_name, self.db.lab_catalog)
                    ref_range = self.db.lab_catalog[catalog_key].reference_range if catalog_key else "N/A"
                    return {
                        "patient_id": patient_id,
                        "test_name": lab.test_name,
                        "values": lab.values,
                        "interpretation": lab.interpretation,
                        "reference_range": ref_range,
                        "notes": lab.notes,
                    }

        # Check if test exists in catalog
        catalog_key = self._fuzzy_lookup(test_name, self.db.lab_catalog)
        if catalog_key is None:
            raise ValueError(
                f"Lab test '{test_name}' not found in catalog. "
                f"Available tests: {', '.join(sorted(self.db.lab_catalog.keys()))}"
            )

        return {
            "patient_id": patient_id,
            "test_name": test_name,
            "values": {"result": "Within normal limits"},
            "interpretation": "Normal",
            "reference_range": self.db.lab_catalog[catalog_key].reference_range,
            "notes": "No patient-specific results pre-populated; default normal returned.",
        }

    @is_tool(ToolType.READ)
    def get_lab_results(self, patient_id: str) -> dict:
        """Get all ordered lab results for a patient.

        Args:
            patient_id: The patient identifier (e.g., 'P001').

        Returns:
            Dictionary with all ordered lab results.

        Raises:
            ValueError: If the patient is not found.
        """
        self._get_patient(patient_id)
        ordered = self.db.ordered_labs.get(patient_id, [])
        results = []
        if patient_id in self.db.patient_labs:
            for lab in self.db.patient_labs[patient_id]:
                if lab.test_name in ordered or self._normalize_key(lab.test_name) in [
                    self._normalize_key(o) for o in ordered
                ]:
                    results.append({
                        "test_name": lab.test_name,
                        "values": lab.values,
                        "interpretation": lab.interpretation,
                        "notes": lab.notes,
                    })
        return {
            "patient_id": patient_id,
            "ordered_tests": ordered,
            "results": results,
        }

    @is_tool(ToolType.READ)
    def order_imaging(self, patient_id: str, imaging_type: str, body_region: str) -> dict:
        """Order an imaging study and get pre-populated findings.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            imaging_type: Type of imaging (e.g., 'X-ray', 'CT', 'MRI', 'Ultrasound').
            body_region: Body region to image (e.g., 'chest', 'abdomen', 'head').

        Returns:
            Dictionary with imaging findings and impression.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)

        study_key = f"{imaging_type}_{body_region}"

        # Track ordered imaging
        if patient_id not in self.db.ordered_imaging:
            self.db.ordered_imaging[patient_id] = []
        self.db.ordered_imaging[patient_id].append(study_key)

        # Look up pre-populated results
        if patient_id in self.db.patient_imaging:
            for img in self.db.patient_imaging[patient_id]:
                if (self._normalize_key(img.imaging_type) == self._normalize_key(imaging_type)
                        and self._normalize_key(img.body_region) == self._normalize_key(body_region)):
                    return {
                        "patient_id": patient_id,
                        "imaging_type": img.imaging_type,
                        "body_region": img.body_region,
                        "findings": img.findings,
                        "impression": img.impression,
                    }

        return {
            "patient_id": patient_id,
            "imaging_type": imaging_type,
            "body_region": body_region,
            "findings": "No acute abnormalities identified.",
            "impression": "Unremarkable study.",
        }

    @is_tool(ToolType.READ)
    def assess_symptoms(self, patient_id: str, symptom: str) -> dict:
        """Perform detailed assessment of a specific symptom.

        Provides structured information about onset, duration, severity,
        character, radiation, and associated symptoms based on the patient's
        chief complaint and condition data.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            symptom: The symptom to assess (e.g., 'chest pain', 'headache').

        Returns:
            Dictionary with detailed symptom assessment.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)

        # Look up disease info for the patient's conditions to find associated symptoms
        associated = []
        for condition in patient.conditions:
            disease_key = self._fuzzy_lookup(condition, self.db.diseases)
            if disease_key:
                disease = self.db.diseases[disease_key]
                associated.extend(
                    s for s in disease.typical_symptoms
                    if self._normalize_key(s) != self._normalize_key(symptom)
                )

        return {
            "patient_id": patient_id,
            "symptom": symptom,
            "present_in_chief_complaint": symptom.lower() in patient.chief_complaint.lower(),
            "patient_conditions": patient.conditions,
            "associated_symptoms": list(set(associated))[:10],
            "assessment": {
                "onset": "Refer to patient history for onset details",
                "severity": "Requires patient interview to determine",
                "character": "Requires patient interview to determine",
                "aggravating_factors": "Requires patient interview to determine",
                "relieving_factors": "Requires patient interview to determine",
            },
        }

    # =========================================================================
    # Knowledge Lookup Tools (READ)
    # =========================================================================

    @is_tool(ToolType.READ)
    def search_disease_info(self, disease_name: str) -> dict:
        """Search for disease information including symptoms, diagnostic criteria, and ICD-10 code.

        Args:
            disease_name: Name of the disease to look up (e.g., 'type 2 diabetes', 'hypertension').

        Returns:
            Dictionary with disease information.

        Raises:
            ValueError: If the disease is not found.
        """
        key = self._fuzzy_lookup(disease_name, self.db.diseases)
        if key is None:
            available = sorted(self.db.diseases.keys())[:20]
            raise ValueError(
                f"Disease '{disease_name}' not found. "
                f"Some available diseases: {', '.join(available)}"
            )
        d = self.db.diseases[key]
        return {
            "disease_name": d.disease_name,
            "icd10_code": d.icd10_code,
            "description": d.description,
            "typical_symptoms": d.typical_symptoms,
            "diagnostic_criteria": d.diagnostic_criteria,
            "risk_factors": d.risk_factors,
            "complications": d.complications,
            "category": d.category,
        }

    @is_tool(ToolType.READ)
    def search_drug_info(self, drug_name: str) -> dict:
        """Search for drug information including class, indications, side effects, and dosing.

        Args:
            drug_name: Generic or brand name of the drug (e.g., 'metformin', 'lisinopril').

        Returns:
            Dictionary with drug information.

        Raises:
            ValueError: If the drug is not found.
        """
        # Try generic name lookup first
        key = self._fuzzy_lookup(drug_name, self.db.drugs)
        if key is None:
            # Try brand name search
            norm_query = self._normalize_key(drug_name)
            for k, drug in self.db.drugs.items():
                for brand in drug.brand_names:
                    if self._normalize_key(brand) == norm_query or norm_query in self._normalize_key(brand):
                        key = k
                        break
                if key:
                    break

        if key is None:
            available = sorted(self.db.drugs.keys())[:20]
            raise ValueError(
                f"Drug '{drug_name}' not found. "
                f"Some available drugs: {', '.join(available)}"
            )
        drug = self.db.drugs[key]
        return {
            "drug_name": drug.drug_name,
            "brand_names": drug.brand_names,
            "drug_class": drug.drug_class,
            "indications": drug.indications,
            "contraindications": drug.contraindications,
            "common_side_effects": drug.common_side_effects,
            "serious_side_effects": drug.serious_side_effects,
            "typical_dose": drug.typical_dose,
            "pregnancy_category": drug.pregnancy_category,
        }

    @is_tool(ToolType.READ)
    def check_drug_interactions(self, drug_list: List[str]) -> dict:
        """Check for drug-drug interactions among a list of medications.

        Args:
            drug_list: List of drug names to check for interactions (e.g., ['metformin', 'lisinopril', 'aspirin']).

        Returns:
            Dictionary with any detected interactions and their severity levels.
        """
        interactions = []
        checked_pairs = set()

        for i, drug_a_name in enumerate(drug_list):
            key_a = self._fuzzy_lookup(drug_a_name, self.db.drugs)
            if key_a is None:
                continue
            drug_a = self.db.drugs[key_a]

            for j, drug_b_name in enumerate(drug_list):
                if i >= j:
                    continue
                pair = tuple(sorted([drug_a_name, drug_b_name]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                key_b = self._fuzzy_lookup(drug_b_name, self.db.drugs)
                if key_b is None:
                    continue

                # Check interactions in drug_a
                for interact_name, severity in drug_a.interactions.items():
                    if self._normalize_key(interact_name) == self._normalize_key(key_b):
                        interactions.append({
                            "drug_a": drug_a.drug_name,
                            "drug_b": self.db.drugs[key_b].drug_name,
                            "severity": severity,
                        })

                # Check interactions in drug_b
                drug_b = self.db.drugs[key_b]
                for interact_name, severity in drug_b.interactions.items():
                    if self._normalize_key(interact_name) == self._normalize_key(key_a):
                        if not any(
                            ix["drug_a"] in (drug_a.drug_name, drug_b.drug_name)
                            and ix["drug_b"] in (drug_a.drug_name, drug_b.drug_name)
                            for ix in interactions
                        ):
                            interactions.append({
                                "drug_a": drug_b.drug_name,
                                "drug_b": drug_a.drug_name,
                                "severity": severity,
                            })

        return {
            "drugs_checked": drug_list,
            "interactions_found": len(interactions),
            "interactions": interactions,
        }

    @is_tool(ToolType.READ)
    def get_treatment_guidelines(self, condition: str) -> dict:
        """Get evidence-based treatment guidelines for a condition.

        Args:
            condition: Name of the condition (e.g., 'type 2 diabetes', 'hypertension').

        Returns:
            Dictionary with treatment recommendations.

        Raises:
            ValueError: If no guidelines are found for the condition.
        """
        key = self._fuzzy_lookup(condition, self.db.treatment_guidelines)
        if key is None:
            available = sorted(self.db.treatment_guidelines.keys())[:20]
            raise ValueError(
                f"No treatment guidelines found for '{condition}'. "
                f"Available guidelines: {', '.join(available)}"
            )
        g = self.db.treatment_guidelines[key]
        return {
            "condition": g.condition,
            "first_line_treatments": g.first_line,
            "second_line_treatments": g.second_line,
            "lifestyle_modifications": g.lifestyle_modifications,
            "monitoring": g.monitoring,
            "referral_criteria": g.referral_criteria,
            "red_flags": g.red_flags,
        }

    # =========================================================================
    # Clinical Action Tools (WRITE)
    # =========================================================================

    @is_tool(ToolType.WRITE)
    def record_diagnosis(
        self, patient_id: str, diagnosis: str, confidence: str, reasoning: str
    ) -> dict:
        """Record a primary diagnosis for a patient with confidence level and clinical reasoning.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            diagnosis: The diagnosis name (e.g., 'Type 2 Diabetes Mellitus').
            confidence: Confidence level — must be 'high', 'moderate', or 'low'.
            reasoning: Clinical reasoning supporting this diagnosis.

        Returns:
            Dictionary confirming the recorded diagnosis.

        Raises:
            ValueError: If the patient is not found or confidence level is invalid.
        """
        self._get_patient(patient_id)

        if confidence not in {"high", "moderate", "low"}:
            raise ValueError("Confidence must be 'high', 'moderate', or 'low'")

        record = RecordedDiagnosis(
            diagnosis=diagnosis, confidence=confidence, reasoning=reasoning
        )
        if patient_id not in self.db.recorded_diagnoses:
            self.db.recorded_diagnoses[patient_id] = []
        self.db.recorded_diagnoses[patient_id].append(record)

        return {
            "patient_id": patient_id,
            "diagnosis": diagnosis,
            "confidence": confidence,
            "reasoning": reasoning,
            "status": "recorded",
        }

    @is_tool(ToolType.WRITE)
    def record_differential(self, patient_id: str, differentials: List[str]) -> dict:
        """Record differential diagnoses for a patient.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            differentials: List of differential diagnoses in order of likelihood (e.g., ['Type 2 Diabetes', 'Metabolic Syndrome', 'Cushing Syndrome']).

        Returns:
            Dictionary confirming recorded differentials.

        Raises:
            ValueError: If the patient is not found.
        """
        self._get_patient(patient_id)

        self.db.recorded_differentials[patient_id] = differentials

        return {
            "patient_id": patient_id,
            "differentials": differentials,
            "count": len(differentials),
            "status": "recorded",
        }

    @is_tool(ToolType.WRITE)
    def prescribe_medication(
        self,
        patient_id: str,
        drug_name: str,
        dose: str,
        frequency: str,
        duration: str,
    ) -> dict:
        """Prescribe a medication for a patient. Automatically checks allergies and drug interactions.

        The system will check the prescribed drug against the patient's allergies
        and current medications for interactions before confirming the prescription.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            drug_name: Generic name of the drug to prescribe (e.g., 'metformin').
            dose: Dosage (e.g., '500mg').
            frequency: Dosing frequency (e.g., 'twice daily').
            duration: Duration of treatment (e.g., '30 days').

        Returns:
            Dictionary with prescription details and safety check results.

        Raises:
            ValueError: If the patient is not found or allergy/contraindication detected.
        """
        patient = self._get_patient(patient_id)

        # Safety: allergy check
        allergy_result = self._check_allergy_internal(patient, drug_name)
        if allergy_result["has_allergy"]:
            raise ValueError(
                f"ALLERGY ALERT: Patient is allergic to '{allergy_result['matched_allergy']}'. "
                f"Cannot prescribe '{drug_name}'."
            )

        # Safety: contraindication check
        contra_result = self._check_contraindication_internal(patient, drug_name)

        # Safety: interaction check
        all_drugs = patient.current_medications + [drug_name]
        interaction_result = self.check_drug_interactions(all_drugs)

        major_interactions = [
            ix for ix in interaction_result["interactions"] if ix["severity"] == "major"
        ]
        if major_interactions:
            conflicting = [
                ix["drug_b"] if ix["drug_a"] == drug_name else ix["drug_a"]
                for ix in major_interactions
            ]
            raise ValueError(
                f"MAJOR INTERACTION ALERT: {drug_name} has major interactions with "
                f"{conflicting}. Review before prescribing."
            )

        record = RecordedPrescription(
            drug_name=drug_name,
            dose=dose,
            frequency=frequency,
            duration=duration,
            allergy_checked=True,
            interaction_checked=True,
        )
        if patient_id not in self.db.recorded_prescriptions:
            self.db.recorded_prescriptions[patient_id] = []
        self.db.recorded_prescriptions[patient_id].append(record)

        warnings = []
        if contra_result["contraindications_found"]:
            warnings.append(f"Contraindication warnings: {contra_result['contraindications']}")
        moderate_interactions = [
            ix for ix in interaction_result["interactions"] if ix["severity"] == "moderate"
        ]
        if moderate_interactions:
            pairs = [f"{ix['drug_a']}-{ix['drug_b']}" for ix in moderate_interactions]
            warnings.append(f"Moderate interactions detected: {pairs}")

        return {
            "patient_id": patient_id,
            "prescription": {
                "drug_name": drug_name,
                "dose": dose,
                "frequency": frequency,
                "duration": duration,
            },
            "safety_checks": {
                "allergy_checked": True,
                "allergy_clear": True,
                "interaction_checked": True,
                "major_interactions": False,
            },
            "warnings": warnings,
            "status": "prescribed",
        }

    @is_tool(ToolType.WRITE)
    def refer_to_specialist(self, patient_id: str, specialty: str, reason: str) -> dict:
        """Refer a patient to a specialist.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            specialty: The specialty to refer to (e.g., 'cardiology', 'endocrinology', 'neurology').
            reason: Reason for the referral.

        Returns:
            Dictionary confirming the referral.

        Raises:
            ValueError: If the patient is not found.
        """
        self._get_patient(patient_id)

        record = RecordedReferral(specialty=specialty, reason=reason)
        if patient_id not in self.db.recorded_referrals:
            self.db.recorded_referrals[patient_id] = []
        self.db.recorded_referrals[patient_id].append(record)

        return {
            "patient_id": patient_id,
            "referral": {
                "specialty": specialty,
                "reason": reason,
            },
            "status": "referral_created",
        }

    @is_tool(ToolType.WRITE)
    def create_follow_up_plan(self, patient_id: str, plan: str, timeframe: str) -> dict:
        """Create a follow-up plan for a patient.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            plan: Description of the follow-up plan.
            timeframe: Timeframe for follow-up (e.g., '2 weeks', '1 month', '3 months').

        Returns:
            Dictionary confirming the follow-up plan.

        Raises:
            ValueError: If the patient is not found.
        """
        self._get_patient(patient_id)

        record = RecordedFollowUp(plan=plan, timeframe=timeframe)
        if patient_id not in self.db.recorded_follow_ups:
            self.db.recorded_follow_ups[patient_id] = []
        self.db.recorded_follow_ups[patient_id].append(record)

        return {
            "patient_id": patient_id,
            "follow_up": {
                "plan": plan,
                "timeframe": timeframe,
            },
            "status": "follow_up_created",
        }

    # =========================================================================
    # Safety Tools (READ)
    # =========================================================================

    def _check_allergy_internal(self, patient: PatientRecord, drug_name: str) -> dict:
        """Internal allergy check helper."""
        norm_drug = self._normalize_key(drug_name)

        # Check drug class for cross-reactivity
        drug_key = self._fuzzy_lookup(drug_name, self.db.drugs)
        drug_class = self.db.drugs[drug_key].drug_class if drug_key else ""

        for allergy in patient.allergies:
            norm_allergy = self._normalize_key(allergy)
            if norm_allergy in norm_drug or norm_drug in norm_allergy:
                return {"has_allergy": True, "matched_allergy": allergy}
            # Check if allergic to the drug class
            if norm_allergy in self._normalize_key(drug_class):
                return {"has_allergy": True, "matched_allergy": f"{allergy} (class: {drug_class})"}

        return {"has_allergy": False, "matched_allergy": None}

    def _check_contraindication_internal(self, patient: PatientRecord, drug_name: str) -> dict:
        """Internal contraindication check helper."""
        drug_key = self._fuzzy_lookup(drug_name, self.db.drugs)
        if drug_key is None:
            return {"contraindications_found": False, "contraindications": []}

        drug = self.db.drugs[drug_key]
        found = []
        for contra in drug.contraindications:
            norm_contra = self._normalize_key(contra)
            for condition in patient.conditions:
                if self._normalize_key(condition) in norm_contra or norm_contra in self._normalize_key(condition):
                    found.append(f"{contra} (patient has: {condition})")

        return {
            "contraindications_found": len(found) > 0,
            "contraindications": found,
        }

    @is_tool(ToolType.READ)
    def check_contraindications(self, patient_id: str, drug_name: str) -> dict:
        """Check a drug against the patient's active conditions and allergies for contraindications.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            drug_name: Name of the drug to check (e.g., 'metformin').

        Returns:
            Dictionary with contraindication check results.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        allergy_result = self._check_allergy_internal(patient, drug_name)
        contra_result = self._check_contraindication_internal(patient, drug_name)

        return {
            "patient_id": patient_id,
            "drug_name": drug_name,
            "allergy_alert": allergy_result["has_allergy"],
            "matched_allergy": allergy_result["matched_allergy"],
            "contraindications_found": contra_result["contraindications_found"],
            "contraindications": contra_result["contraindications"],
            "safe_to_prescribe": not allergy_result["has_allergy"] and not contra_result["contraindications_found"],
        }

    @is_tool(ToolType.READ)
    def check_allergies(self, patient_id: str, drug_name: str) -> dict:
        """Check if a specific drug triggers any of the patient's known allergies.

        Args:
            patient_id: The patient identifier (e.g., 'P001').
            drug_name: Name of the drug to check (e.g., 'amoxicillin').

        Returns:
            Dictionary with allergy check results.

        Raises:
            ValueError: If the patient is not found.
        """
        patient = self._get_patient(patient_id)
        result = self._check_allergy_internal(patient, drug_name)

        return {
            "patient_id": patient_id,
            "drug_name": drug_name,
            "has_allergy": result["has_allergy"],
            "matched_allergy": result["matched_allergy"],
            "patient_allergies": patient.allergies,
        }

    # =========================================================================
    # Generic Tools
    # =========================================================================

    # transfer_to_human_agents temporarily disabled — agents call it too eagerly
    # at step 2, causing 0% task success rate. Re-enable when policy prompt is tuned.
    # @is_tool(ToolType.GENERIC)
    # def transfer_to_human_agents(self, summary: str) -> str:
    #     """Transfer the patient to a human clinician."""
    #     return "Transfer successful. Patient has been referred to a human clinician."
