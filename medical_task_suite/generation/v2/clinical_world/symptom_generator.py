#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symptom Generator — Generate symptoms with controlled noise/missing/misleading.

v1: all real symptoms revealed upfront.
v2: symptoms distributed across visibility tiers based on scenario uncertainty.
v2.9: fully deterministic — all randomness via local RNG, no global random state.
"""

import random as _random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec, ClinicalGroundTruth
from ..scenario_engine.uncertainty_model import UncertaintyModel, UncertaintyConfig
from .disease_sampler import DiseaseSampler
from .patient_language import PatientLanguageLayer


# v2.7: Try expanded pools first, fall back to original
try:
    from .expanded_symptom_pools import (
        EXPANDED_NOISE_SYMPTOM_POOL, EXPANDED_MISLEADING_SYMPTOM_MAP,
        ATYPICAL_SYMPTOMS, SYMPTOM_VARIANTS, STRUCTURAL_UNCERTAINTY_CONFIG,
    )
    _NOISE_POOL = EXPANDED_NOISE_SYMPTOM_POOL
    _MISLEADING_MAP = EXPANDED_MISLEADING_SYMPTOM_MAP
    _ATYPICAL = ATYPICAL_SYMPTOMS
    _VARIANTS = SYMPTOM_VARIANTS
    _STRUCT_CFG = STRUCTURAL_UNCERTAINTY_CONFIG
except ImportError:
    _ATYPICAL = {}
    _VARIANTS = {}
    _STRUCT_CFG = {}
    # Original pools (fallback)
    _NOISE_POOL = [
        "mild headache", "occasional dizziness", "minor skin rash",
        "slight nausea", "mild fatigue", "intermittent back pain",
        "occasional heartburn", "mild joint stiffness", "slight blurry vision",
        "trouble sleeping", "dry mouth", "mild anxiety",
        "occasional ringing in ears", "slight swelling in ankles",
        "mild constipation", "bloating", "mild throat irritation",
        "occasional muscle cramps", "slight hand numbness",
    ]
    _MISLEADING_MAP = {
        "type 2 diabetes": ["weight loss", "frequent infections"],
        "hypertension": ["nosebleed", "visual changes"],
        "coronary artery disease": ["jaw pain", "left arm pain"],
        "copd": ["morning headache", "swollen ankles"],
        "asthma": ["chronic cough", "difficulty swallowing"],
        "heart failure": ["abdominal swelling", "loss of appetite"],
        "stroke": ["ear pain", "toothache"],
        "atrial fibrillation": ["chest pressure", "sweating"],
        "gerd": ["chronic cough", "sore throat"],
        "anxiety disorder": ["chest pain", "shortness of breath"],
    }

# Keep original names as aliases for backward compatibility
NOISE_SYMPTOM_POOL = _NOISE_POOL
MISLEADING_SYMPTOM_MAP = _MISLEADING_MAP

# Component hash offsets for deriving sub-RNGs from a single seed
_SYMPTOM_RNG_OFFSET = 0
_STRUCT_RNG_OFFSET = 1000
_NOISE_RNG_OFFSET = 2000
_MISLEAD_RNG_OFFSET = 3000


@dataclass
class SymptomSet:
    """Complete symptom configuration for a scenario."""
    # Real symptoms of the target disease
    real_symptoms: List[str] = field(default_factory=list)

    # Distribution across visibility tiers
    volunteer: List[str] = field(default_factory=list)
    if_asked: List[str] = field(default_factory=list)
    resistant: List[str] = field(default_factory=list)
    hidden: List[str] = field(default_factory=list)

    # Non-real symptoms
    noise: List[str] = field(default_factory=list)
    misleading: List[str] = field(default_factory=list)

    # Discriminative quality metric
    discriminative_ratio: float = 0.0

    # All symptoms the patient might mention (for dialogue generation)
    @property
    def presented_symptoms(self) -> List[str]:
        return self.volunteer + self.noise + self.misleading

    @property
    def all_known_symptoms(self) -> List[str]:
        return self.volunteer + self.if_asked + self.resistant


class SymptomGenerator:
    """Generate symptoms with controlled uncertainty for a scenario.

    Fully deterministic: all randomness via local RNG instances derived
    from the seed. No global random state is used or modified.
    """

    def __init__(self, clinical_kb, primekg=None):
        self.kb = clinical_kb
        self.primekg = primekg
        self.uncertainty = UncertaintyModel()
        self.language = PatientLanguageLayer()

    def generate(
        self,
        disease: str,
        scenario: ScenarioSpec,
        seed: Optional[int] = None,
    ) -> SymptomSet:
        """
        Generate a complete symptom set for the disease-scenario pair.

        v2.9: Fully deterministic. Creates local RNG instances from seed.
        No global random state is touched.
        """
        base_seed = seed if seed is not None else 42

        # Derive sub-RNGs for each stage (isolated, reproducible)
        symptom_rng = _random.Random(base_seed + _SYMPTOM_RNG_OFFSET)
        struct_rng = _random.Random(base_seed + _STRUCT_RNG_OFFSET)
        noise_rng = _random.Random(base_seed + _NOISE_RNG_OFFSET)
        mislead_rng = _random.Random(base_seed + _MISLEAD_RNG_OFFSET)

        # 1. Get real symptoms for the PRIMARY disease
        real_symptoms = self._get_real_symptoms(disease)
        if not real_symptoms:
            real_symptoms = ["fatigue", "general discomfort"]

        # 2. Merge comorbidity symptoms
        gt = scenario.ground_truth
        comorbidity_symptoms = []
        for comorb in gt.comorbidities:
            comorb_name = comorb.name if hasattr(comorb, 'name') else str(comorb)
            c_symptoms = self._get_real_symptoms(comorb_name)
            contribution = comorb.contribution if hasattr(comorb, 'contribution') else 0.3
            n_include = max(1, int(len(c_symptoms) * contribution))
            comorbidity_symptoms.extend(c_symptoms[:n_include])

        # 3. Get confounder symptoms (needed BEFORE structural uncertainty)
        confounder_symptoms = []
        confounder_names = []
        for conf in gt.confounders:
            conf_name = conf.name if hasattr(conf, 'name') else str(conf)
            confounder_names.append(conf_name)
            c_symptoms = self._get_real_symptoms(conf_name)
            # Confounders contribute up to 3 overlapping/mimicking symptoms
            confounder_symptoms.extend(c_symptoms[:3])

        # 1b. STRUCTURAL UNCERTAINTY: randomly modify canonical symptom set
        #     Pass confounder symptoms so discriminative signals are preserved.
        #     Uses struct_rng for full determinism.
        real_symptoms = self._apply_structural_uncertainty(
            real_symptoms, disease, scenario.difficulty,
            confounder_symptoms=confounder_symptoms,
            rng=struct_rng,
        )

        # 4. Build uncertainty config
        config = UncertaintyConfig.from_difficulty(scenario.difficulty, scenario.task_type)

        # 5. Distribute TRUE symptoms: push critical ones to hidden/resistant
        #    Pass symptom_rng for deterministic shuffling.
        all_real = real_symptoms + comorbidity_symptoms
        distribution = self.uncertainty.apply_uncertainty(all_real, config, rng=symptom_rng)

        # 6. CONFOUNDER DOMINANCE: redistribute tiers
        #    Confounder symptoms → volunteer + if_asked (front-loaded)
        #    True symptoms → if_asked + hidden + resistant (back-loaded)
        volunteer_conf = confounder_symptoms[:2]  # Top 2 confounder symptoms: volunteered
        if_asked_conf = confounder_symptoms[2:4]  # Next confounder symptoms: if_asked

        # Remove confounder symptoms from true distribution (avoid double-counting)
        conf_set = set(s.lower() for s in confounder_symptoms)
        for tier in ("volunteer", "if_asked"):
            distribution[tier] = [s for s in distribution.get(tier, [])
                                  if s.lower() not in conf_set]

        # Push remaining true symptoms toward hidden/resistant
        true_volunteer = distribution.get("volunteer", [])
        true_if_asked = distribution.get("if_asked", [])
        true_hidden = distribution.get("hidden", [])
        true_resistant = distribution.get("resistant", [])

        # Keep only 1 true symptom in volunteer (the least informative one)
        if len(true_volunteer) > 1:
            demoted = true_volunteer[1:]
            true_volunteer = true_volunteer[:1]
            true_hidden.extend(demoted)

        # Move if_asked true symptoms to hidden for higher difficulty
        if scenario.difficulty in ("L2", "L3") and true_if_asked:
            # Keep first in if_asked, push rest to hidden
            demoted = true_if_asked[1:]
            true_if_asked = true_if_asked[:1]
            true_resistant.extend(demoted)

        # 7. Final tier assignment
        final_volunteer = volunteer_conf + true_volunteer
        final_if_asked = if_asked_conf + true_if_asked
        final_hidden = true_hidden
        final_resistant = true_resistant

        # 8. Generate noise (uses noise_rng)
        noise = self._generate_noise(scenario, config, rng=noise_rng)

        # 9. Misleading = confounder symptoms that aren't already in volunteer/if_asked
        remaining_conf = [s for s in confounder_symptoms
                          if s not in volunteer_conf and s not in if_asked_conf]
        misleading = remaining_conf if remaining_conf else self._generate_misleading(
            disease, scenario, config, rng=mislead_rng)

        # 10. Floor: ensure at least 3 true symptoms for discrimination
        MIN_SYMPTOMS = 3
        true_count = len(true_volunteer) + len(true_if_asked) + len(true_hidden) + len(true_resistant)
        if true_count < MIN_SYMPTOMS:
            existing = set(all_real)
            supplement_pool = self._fallback_symptoms(disease)
            supplement_pool = [s for s in supplement_pool if s not in existing]
            if not supplement_pool:
                supplement_pool = ["fatigue", "headache", "nausea", "dizziness", "appetite loss"]
                supplement_pool = [s for s in supplement_pool if s not in existing]
            needed = MIN_SYMPTOMS - true_count
            symptom_rng.shuffle(supplement_pool)
            extra = supplement_pool[:needed]
            for i, s in enumerate(extra):
                tier = "hidden" if i % 2 == 0 else "resistant"
                if tier == "hidden":
                    final_hidden.append(s)
                else:
                    final_resistant.append(s)

        # 11. Convert to patient-friendly language
        volunteer = [self.language.to_patient(s) for s in final_volunteer]
        if_asked = [self.language.to_patient(s) for s in final_if_asked]
        hidden = [self.language.to_patient(s) for s in final_hidden]
        resistant = [self.language.to_patient(s) for s in final_resistant]
        noise = [self.language.to_patient(s) for s in noise]
        misleading = [self.language.to_patient(s) for s in misleading]

        # 12. Compute discriminative ratio
        # True disease symptoms = volunteer + if_asked + hidden + resistant (excluding confounder-contributed)
        true_syms = final_volunteer + final_if_asked + final_hidden + final_resistant
        conf_lower = [s.lower() for s in confounder_symptoms]
        noise_lower = [s.lower() for s in noise]
        misleading_lower = [s.lower() for s in misleading]
        disc_ratio = self.compute_discriminative_ratio(
            true_syms, conf_lower, noise_lower, misleading_lower,
        )

        return SymptomSet(
            real_symptoms=all_real,
            volunteer=volunteer,
            if_asked=if_asked,
            resistant=resistant,
            hidden=hidden,
            noise=noise,
            misleading=misleading,
            discriminative_ratio=round(disc_ratio, 4),
        )

    # Disease-name terms that should not appear as symptoms
    _DISEASE_NAME_TERMS = {
        "kidney disease", "heart disease", "lung disease", "liver disease",
        "thyroid disease", "blood disease", "skin disease", "bone disease",
        "bowel disease", "vascular disease", "autoimmune disease",
        "inflammatory disease", "degenerative disease", "metabolic disease",
        "connective tissue disease", "valvular disease",
        "lupus", "arthritis", "diabetes", "hypertension",
    }

    def _get_real_symptoms(self, disease: str) -> List[str]:
        """Get real symptoms for a disease from clinical KB."""
        profile = self.kb.get_disease_profile(disease)
        symptoms = []

        # Try differential_questions for symptom-like content
        if hasattr(profile, 'differential_questions'):
            raw = [
                q.replace("?", "").strip()
                for q in (profile.differential_questions or [])
                if len(q) < 40
            ]
            # Filter out disease-name phrases
            for s in raw:
                s_lower = s.lower().strip()
                if s_lower in self._DISEASE_NAME_TERMS:
                    continue
                # Also skip if it matches a known disease abbreviation
                if len(s_lower) <= 4 and s_lower.isupper():
                    continue
                symptoms.append(s)

        # Do NOT use aliases as symptoms — they are disease names, not symptoms.
        # Skip straight to fallback.

        # Fallback to disease-specific common symptoms
        if not symptoms:
            symptoms = self._fallback_symptoms(disease)

        return symptoms

    def _fallback_symptoms(self, disease: str) -> List[str]:
        """Fallback symptom list for common diseases."""
        fallback = {
            "type 2 diabetes": ["frequent urination", "fatigue", "blurred vision", "thirst"],
            "hypertension": ["headache", "dizziness", "chest pain"],
            "coronary artery disease": ["chest pain", "shortness of breath", "fatigue"],
            "copd": ["cough", "shortness of breath", "fatigue"],
            "asthma": ["wheezing", "shortness of breath", "cough"],
            "heart failure": ["shortness of breath", "swelling", "fatigue"],
            "chronic kidney disease": ["fatigue", "swelling", "nausea"],
            "anemia": ["fatigue", "dizziness", "shortness of breath"],
            "stroke": ["weakness", "confusion", "headache"],
            "atrial fibrillation": ["palpitations", "dizziness", "shortness of breath"],
            "gout": ["joint pain", "swelling", "redness"],
            "osteoporosis": ["back pain", "joint pain", "weakness"],
            "gerd": ["heartburn", "chest pain", "cough"],
            "migraine": ["headache", "nausea", "blurred vision"],
            "epilepsy": ["seizure", "confusion", "headache"],
            "parkinson disease": ["tremor", "stiffness", "weakness"],
            "rheumatoid arthritis": ["joint pain", "swelling", "stiffness"],
            "anxiety disorder": ["anxiety", "insomnia", "fatigue"],
            "hyperthyroidism": ["weight loss", "tremor", "anxiety"],
            "nephrolithiasis": ["back pain", "abdominal pain", "nausea"],
            "pulmonary embolism": ["shortness of breath", "chest pain", "cough"],
            "meningitis": ["fever", "headache", "confusion"],
            "covid-19": ["fever", "cough", "fatigue"],
            "pneumonia": ["cough", "fever", "shortness of breath"],
        }
        return fallback.get(disease.lower(), ["fatigue", "pain"])

    def _generate_noise(
        self, scenario: ScenarioSpec, config: UncertaintyConfig,
        rng: _random.Random = None,
    ) -> List[str]:
        """Generate unrelated noise symptoms from expanded pool."""
        if rng is None:
            rng = _random.Random(42)
        n_noise = max(0, int(config.noise_fraction * 5))  # Scale to ~5 base symptoms
        if n_noise == 0:
            return []

        pool = [s for s in _NOISE_POOL]
        rng.shuffle(pool)
        return pool[:n_noise]

    def _generate_misleading(
        self, disease: str, scenario: ScenarioSpec, config: UncertaintyConfig,
        rng: _random.Random = None,
    ) -> List[str]:
        """Generate misleading symptoms that point to wrong diagnosis."""
        if rng is None:
            rng = _random.Random(42)
        if config.misleading_fraction <= 0:
            return []

        # Check for disease-specific misleading symptoms (expanded map)
        candidates = list(_MISLEADING_MAP.get(disease.lower(), []))  # Copy to avoid mutating module data

        if not candidates:
            # Generic misleading pool
            candidates = [
                "unexplained weight change", "night sweats",
                "new skin changes", "change in appetite",
            ]

        n = max(1, int(config.misleading_fraction * 3))
        rng.shuffle(candidates)
        return candidates[:n]

    def _apply_structural_uncertainty(
        self,
        symptoms: List[str],
        disease: str,
        difficulty: str,
        confounder_symptoms: Optional[List[str]] = None,
        rng: _random.Random = None,
    ) -> List[str]:
        """Apply structural uncertainty: drop, perturb, and inject atypical symptoms.

        Three transformations applied per-task (seed-controlled):
        1. DROP: randomly remove some canonical symptoms
           → Protected: at least 2 high-discriminative symptoms always kept
        2. PERTURB: replace some canonical symptom descriptions with variants
        3. INJECT: add atypical/rare symptoms not in the canonical list
           → Protected: injected count ≤ discriminative signal count

        This makes the same disease produce different symptom sets across tasks,
        preventing agents from memorizing disease-symptom mappings, while
        preserving enough discriminative signal for correct diagnosis.

        Fully deterministic: uses local rng parameter.
        """
        if rng is None:
            rng = _random.Random(42)

        if not symptoms or not _STRUCT_CFG:
            return symptoms

        cfg = _STRUCT_CFG.get(difficulty, _STRUCT_CFG.get("L2", {}))
        result = list(symptoms)

        # ── Pre-compute discriminative (unique-to-disease) symptoms ──
        confounder_syms_lower = set()
        if confounder_symptoms:
            confounder_syms_lower = {s.lower() for s in confounder_symptoms}

        discriminative = []
        for s in result:
            s_lower = s.lower()
            is_overlap = any(
                s_lower in cs or cs in s_lower
                for cs in confounder_syms_lower
            )
            if not is_overlap:
                discriminative.append(s)

        # ── 1. DROP canonical symptoms ──
        drop_low, drop_high = cfg.get("canonical_drop_rate", (0.0, 0.15))
        drop_rate = rng.uniform(drop_low, drop_high)
        min_keep = 2
        min_discriminative = 2

        if len(result) > min_keep:
            n_to_drop = max(0, int(len(result) * drop_rate))
            if n_to_drop > 0 and len(result) - n_to_drop >= min_keep:
                non_disc = [s for s in result if s not in discriminative]
                disc_remaining = list(discriminative)

                # Drop from non-discriminative pool first
                dropped = 0
                result_after_drop = []
                for s in result:
                    if dropped < n_to_drop and s in non_disc:
                        dropped += 1
                    else:
                        result_after_drop.append(s)

                # If still need to drop more, drop from discriminative tail
                if dropped < n_to_drop and len(disc_remaining) > min_discriminative:
                    can_drop_from_disc = len(disc_remaining) - min_discriminative
                    extra_drop = min(n_to_drop - dropped, can_drop_from_disc)
                    if extra_drop > 0:
                        disc_to_remove = set(disc_remaining[-extra_drop:])
                        result_after_drop = [
                            s for s in result_after_drop
                            if s not in disc_to_remove
                        ]

                result = result_after_drop

        # ── 2. PERTURB symptom descriptions ──
        variant_rate = cfg.get("variant_replace_rate", 0.1)
        perturbed = []
        for s in result:
            s_lower = s.lower().strip()
            replaced = False
            for canonical, variants in _VARIANTS.items():
                if canonical in s_lower and rng.random() < variant_rate:
                    perturbed.append(rng.choice(variants))
                    replaced = True
                    break
            if not replaced:
                perturbed.append(s)
        result = perturbed

        # ── 3. INJECT atypical/rare symptoms ──
        inj_low, inj_high = cfg.get("atypical_inject_rate", (0.0, 0.2))
        inject_prob = rng.uniform(inj_low, inj_high)
        max_atypical = cfg.get("max_atypical_added", 1)

        atypical_pool = list(_ATYPICAL.get(disease.lower(), []))  # Copy to avoid mutating module data
        if atypical_pool and rng.random() < inject_prob:
            current_discriminative = sum(
                1 for s in result
                if not any(s.lower() in cs or cs in s.lower()
                           for cs in confounder_syms_lower)
            )
            max_inject = min(max_atypical, current_discriminative)

            if max_inject >= 1:
                n_inject = rng.randint(1, max_inject)
                rng.shuffle(atypical_pool)
                injected = atypical_pool[:n_inject]
                existing_lower = {s.lower() for s in result}
                for s in injected:
                    if s.lower() not in existing_lower:
                        result.append(s)
                        existing_lower.add(s.lower())

        return result

    def compute_discriminative_ratio(
        self,
        disease_symptoms: List[str],
        confounder_symptoms: List[str],
        noise: List[str],
        misleading: List[str],
    ) -> float:
        """Compute discriminative ratio: fraction of symptoms unique to correct disease.

        discriminative_ratio = (# symptoms unique to correct disease) /
                               (# total symptoms in the scenario)

        A symptom is "unique to correct disease" if it does NOT overlap with
        any confounder/noise/misleading symptom (case-insensitive substring match).
        """
        # All non-disease symptoms (the "distractor" pool)
        distractor_lower = set()
        for s in confounder_symptoms + noise + misleading:
            distractor_lower.add(s.lower().strip())

        if not disease_symptoms:
            return 0.0

        # Count disease symptoms that are NOT in distractor pool
        unique_count = 0
        for s in disease_symptoms:
            s_lower = s.lower().strip()
            is_shared = any(
                s_lower in d or d in s_lower
                for d in distractor_lower
            )
            if not is_shared:
                unique_count += 1

        # Total = all disease symptoms + distractors
        total = len(disease_symptoms) + len(confounder_symptoms) + len(noise) + len(misleading)
        if total == 0:
            return 1.0  # No distractors at all → fully discriminative

        return unique_count / total
