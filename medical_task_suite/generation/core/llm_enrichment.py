#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Enrichment Pipeline for PrimeKG Walk Results.

Takes skeletal PrimeKG random walk results and uses GPT-5.2 (via Azure)
to generate rich, realistic v3-format clinical tasks with full patient
personas, structured symptoms, progressive reveal, likelihood tables,
ground truth, and evaluation criteria.
"""

import asyncio
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import litellm
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from .random_walk import MultiPathWalkResult, WalkPath

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------
_ENV_LOADED = False


def _ensure_env():
    global _ENV_LOADED
    if not _ENV_LOADED:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        _ENV_LOADED = True


# ---------------------------------------------------------------------------
# Difficulty presets
# ---------------------------------------------------------------------------

DIFFICULTY_PRESETS = {
    "L0": {
        "label": "straightforward",
        "behavior": "cooperative",
        "symptom_complexity": "minimal hidden/resistant symptoms",
        "num_differentials": 1,
        "num_comorbidities": 0,
        "max_turns": 10,
        "min_turns": 2,
        "reward_basis": ["ACTION"],
    },
    "L1": {
        "label": "moderate",
        "behavior": "cooperative",
        "symptom_complexity": "some hidden symptoms, one resistant symptom possible",
        "num_differentials": 3,
        "num_comorbidities": 0,
        "max_turns": 20,
        "min_turns": 3,
        "reward_basis": ["ACTION", "COMMUNICATE"],
    },
    "L2": {
        "label": "complex",
        "behavior": "anxious or stoic",
        "symptom_complexity": "multiple hidden, resistant, and misleading symptoms",
        "num_differentials": 4,
        "num_comorbidities": 1,
        "max_turns": 25,
        "min_turns": 5,
        "reward_basis": ["ACTION", "COMMUNICATE"],
    },
    "L3": {
        "label": "expert",
        "behavior": "evasive or hostile",
        "symptom_complexity": "many hidden, resistant, misleading, and noise symptoms; "
        "comorbidities that confound presentation",
        "num_differentials": 5,
        "num_comorbidities": 2,
        "max_turns": 30,
        "min_turns": 7,
        "reward_basis": ["ACTION", "COMMUNICATE"],
    },
}

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a senior clinical educator generating realistic patient simulation \
scenarios for training AI medical agents. You output ONLY valid JSON — no \
markdown fences, no commentary. All medical content must be clinically \
accurate and consistent with established guidelines."""

_PERSONA_PROMPT = """\
Generate a realistic patient persona for a clinical consultation scenario.

## Clinical Context (from knowledge graph)
- Primary disease: {disease}
- Known symptoms: {symptoms}
- Known drugs: {drugs}
- Difficulty: {difficulty} ({difficulty_label})

## Requirements
- Age should be epidemiologically plausible for {disease}
- Include demographics, education, occupation, economic status
- Behavior type: {behavior_type}
- Communication style should match the education level
- Include realistic misconceptions a patient with this profile might have

Return JSON with this exact structure:
{{
  "profile": {{
    "age": <int>,
    "gender": "<male|female>",
    "education": "<primary_school|middle_school|high_school|college|graduate>",
    "occupation": "<string>",
    "economic_status": "<low|moderate|high>"
  }},
  "behavior": {{
    "type": "<cooperative|anxious|stoic|evasive|hostile>",
    "cooperation": "<excellent|good|moderate|poor>",
    "communication": "<clear|vague|tangential|minimal>",
    "empathy_needed": <true|false>
  }},
  "misconceptions": {{
    "general_concerns": ["<string>", ...],
    "economic_concerns": ["<string>", ...]
  }}
}}"""

_SYMPTOMS_PROMPT = """\
Generate a structured symptom presentation for a patient with {disease}.

## Clinical Context
- Known symptoms from knowledge graph: {symptoms}
- Differential diagnoses: {differentials}
- Comorbidities: {comorbidities}
- Difficulty: {difficulty} ({difficulty_label})
- Complexity guidance: {symptom_complexity}

## Symptom Categories
- volunteer: symptoms the patient mentions upfront (chief complaint + obvious ones)
- if_asked: symptoms revealed only when the doctor asks directly
- hidden: symptoms the patient doesn't realize are relevant (need specific probing)
- resistant: symptoms the patient is reluctant to share (embarrassing, stigmatized)
- misleading: red herrings from patient self-diagnosis or unrelated conditions
- noise: genuinely unrelated symptoms that add realism

## Rules
- The chief complaint MUST be in volunteer
- At least one symptom from the KG must appear in volunteer or if_asked
- Hidden symptoms should be clinically relevant but non-obvious to a layperson
- Misleading symptoms should plausibly lead toward a differential diagnosis
- All symptoms must be described in patient-friendly language, not medical jargon

Return JSON:
{{
  "chief_complaint": "<string in patient's own words>",
  "symptoms": {{
    "volunteer": ["<string>", ...],
    "if_asked": ["<string>", ...],
    "hidden": ["<string>", ...],
    "resistant": ["<string>", ...],
    "misleading": ["<string>", ...],
    "noise": ["<string>", ...]
  }},
  "progressive_reveal": [
    {{
      "after_turn": <int>,
      "symptom": "<string>",
      "trigger": "<description of what causes reveal>"
    }}
  ]
}}"""

_CLINICAL_DATA_PROMPT = """\
Generate realistic clinical data for a patient with {disease}.

## Clinical Context
- Disease: {disease}
- Symptoms: {symptoms}
- Known drugs: {drugs}
- Drug interactions: {drug_interactions}
- Comorbidities: {comorbidities}
- Patient age: {age}, gender: {gender}

## Requirements
- Vitals should be consistent with the disease presentation
- Lab results should include both normal and abnormal values relevant to diagnosis
- Medications should include current medications (if any comorbidities)
- Allergies should be realistic (include at least one if difficulty >= L2)
- Confounders should be conditions/factors that complicate diagnosis

Return JSON:
{{
  "vitals": {{
    "blood_pressure": "<string mmHg>",
    "heart_rate": "<string bpm>",
    "temperature": "<string C>",
    "respiratory_rate": "<string breaths/min>",
    "bmi": "<string>"
  }},
  "labs": {{
    "<test_name>": {{
      "value": "<string with units>",
      "normal_range": "<string>",
      "abnormal": <true|false>
    }}
  }},
  "medications": ["<drug name> <dose> <frequency>", ...],
  "comorbidities": ["<string>", ...],
  "allergies": ["<string>", ...],
  "confounders": ["<string>", ...]
}}"""

_GROUND_TRUTH_PROMPT = """\
Generate ground truth and evaluation criteria for a clinical task.

## Clinical Context
- Primary disease: {disease}
- Differentials: {differentials}
- Symptoms (all): {all_symptoms}
- Drugs: {drugs}
- Drug interactions: {drug_interactions}
- Labs available: {labs}
- Safety concerns: {safety_concerns}
- Difficulty: {difficulty} ({difficulty_label})

## Requirements
Generate the correct diagnosis, treatment plan, safety checks, and communication milestones.

Return JSON:
{{
  "correct_diagnosis": {{
    "primary": "<disease name>",
    "confidence_threshold": <float 0-1>,
    "acceptable_alternatives": ["<string>", ...],
    "required_evidence": ["<string>", ...]
  }},
  "expected_lab_results": {{
    "<test_name>": "<expected finding>"
  }},
  "correct_treatment_plan": {{
    "medications": ["<drug> <dose> <route> <frequency>", ...],
    "non_pharmacological": ["<string>", ...],
    "follow_up": "<timeframe>"
  }},
  "required_safety_checks": [
    {{
      "check": "<allergy_check|drug_interaction_check|contraindication_check>",
      "before": "<prescribing|ordering>",
      "critical": <true|false>
    }}
  ],
  "communication_truth": [
    {{
      "milestone": "<explain_diagnosis|explain_treatment|address_concerns|educate_lifestyle>",
      "must_include": ["<key concept>", ...]
    }}
  ]
}}"""

_LIKELIHOOD_TABLE_PROMPT = """\
Generate a symptom-to-disease likelihood table for differential diagnosis.

## Clinical Context
- Primary disease: {disease}
- Differentials: {differentials}
- All symptoms: {all_symptoms}

## Requirements
For each symptom, estimate the probability it would be present given each disease.
Values should be between 0.0 and 1.0.
The primary disease should generally have the highest likelihoods for the key symptoms.

Return JSON — a dictionary mapping each symptom string to a dictionary of disease→probability:
{{
  "<symptom>": {{
    "<disease>": <float>,
    ...
  }},
  ...
}}"""

_EVALUATION_PROMPT = """\
Generate evaluation criteria for a clinical agent benchmark task.

## Clinical Context
- Disease: {disease}
- Difficulty: {difficulty}
- Required safety checks: {safety_checks}
- Communication milestones: {communication_milestones}
- Available actions: ASK, ORDER_LAB, GET_RESULTS, DIAGNOSE, CHECK_ALLERGY, \
CHECK_INTERACTION, PRESCRIBE, EDUCATE, SCHEDULE_FOLLOWUP, END

## Requirements
Define the expected tool call sequence, NL assertions for quality, and solution paths.

Return JSON:
{{
  "tool_call_sequence": [
    {{
      "tool": "<action_name>",
      "required_args": {{}},
      "description": "<why this step>"
    }}
  ],
  "nl_assertions": [
    "<assertion about agent behavior>"
  ],
  "solution_space": {{
    "minimal_paths": [
      {{
        "path_id": "<string>",
        "description": "<string>",
        "must_collect": ["<symptom>", ...],
        "steps": ["<step>", ...],
        "is_optimal": <true|false>
      }}
    ],
    "acceptable_variants": [
      {{
        "description": "<string>",
        "steps": ["<step>", ...]
      }}
    ]
  }}
}}"""

_PATIENT_INSTRUCTIONS_PROMPT = """\
Generate natural-language patient instructions for a simulated patient.

## Patient Profile
- Name: {name}
- Age: {age}, Gender: {gender}
- Education: {education}, Occupation: {occupation}
- Chief complaint: {chief_complaint}
- Behavior type: {behavior_type}
- Communication style: {communication}
- Symptoms to volunteer: {volunteer_symptoms}
- Symptoms if asked: {if_asked_symptoms}
- Hidden symptoms: {hidden_symptoms}
- Resistant symptoms: {resistant_symptoms}
- Misleading symptoms: {misleading_symptoms}
- Economic concerns: {economic_concerns}

Write 2nd-person instructions ("You are ...") that tell the simulated patient how to behave. \
Include when to volunteer info, when to withhold, what misconceptions to express, \
and how to respond to empathy. Keep it under 200 words.

Return JSON:
{{
  "instructions": "<string>"
}}"""


# ---------------------------------------------------------------------------
# ClinicalTaskEnricher
# ---------------------------------------------------------------------------

class ClinicalTaskEnricher:
    """Enriches skeletal PrimeKG walk results into v3-quality clinical tasks."""

    def __init__(
        self,
        model: str = "azure/gpt-5.2",
        temperature: float = 0.7,
        max_retries: int = 3,
    ):
        _ensure_env()
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries

    # ------------------------------------------------------------------
    # LLM call helper
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        reraise=True,
    )
    async def _llm_json(self, system: str, user: str) -> dict:
        """Call LLM and parse JSON response."""
        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)

    # ------------------------------------------------------------------
    # Context extraction from walk result
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_context(walk_result: MultiPathWalkResult) -> dict:
        """Extract clinical context from a PrimeKG walk result."""
        main = walk_result.main_path

        diseases = []
        symptoms = []
        drugs = []
        edge_types = []

        def _node_name(edge_info: dict, node_id: str) -> str:
            """Resolve a human-readable name from edge metadata or fall back to node_id."""
            return edge_info.get("target_name") or edge_info.get("node_name") or node_id

        for i, node in enumerate(main.nodes):
            edge = main.edges[i] if i < len(main.edges) else {}
            etype = edge.get("edge_type", "")
            ntype = edge.get("target_type", "") or edge.get("source_type", "")
            name = _node_name(edge, node)
            edge_types.append(etype)

            if "disease" in ntype.lower() or etype in ("phenotype present",):
                if etype == "phenotype present":
                    diseases.append(name)
                elif "disease" in ntype.lower():
                    diseases.append(name)
            if "effect" in ntype.lower() or "phenotype" in ntype.lower():
                symptoms.append(name)
            if "drug" in ntype.lower() or etype in ("indication", "contraindication"):
                drugs.append(name)

        # Fallback: parse node names from edges
        for edge in main.edges:
            tgt_name = edge.get("target_name", edge.get("target", ""))
            et = edge.get("edge_type", "")
            if et == "phenotype present" and tgt_name and tgt_name not in diseases:
                diseases.append(tgt_name)
            if et in ("indication",) and tgt_name and tgt_name not in drugs:
                drugs.append(tgt_name)

        # Also pull from walk result metadata
        differentials = [d.get("name", d.get("disease", str(d)))
                         for d in walk_result.differential_candidates]
        comorbidities = [d.get("name", d.get("disease", str(d)))
                         for d in walk_result.comorbid_diseases]
        drug_interactions = [
            f"{di.get('drug1', '?')} + {di.get('drug2', '?')}: {di.get('type', '?')}"
            for di in walk_result.drug_interactions
        ]

        # Deduplicate
        diseases = list(dict.fromkeys(diseases))
        symptoms = list(dict.fromkeys(symptoms))
        drugs = list(dict.fromkeys(drugs))

        return {
            "disease": diseases[0] if diseases else "unknown",
            "all_diseases": diseases,
            "symptoms": symptoms,
            "drugs": drugs,
            "differentials": differentials,
            "comorbidities": comorbidities,
            "drug_interactions": drug_interactions,
            "edge_types": edge_types,
            "walk_complexity": walk_result.walk_complexity,
        }

    # ------------------------------------------------------------------
    # Sub-generators
    # ------------------------------------------------------------------

    async def _generate_patient_persona(
        self, context: dict, difficulty: str
    ) -> dict:
        """Use LLM to create a realistic patient persona."""
        preset = DIFFICULTY_PRESETS[difficulty]
        prompt = _PERSONA_PROMPT.format(
            disease=context["disease"],
            symptoms=", ".join(context["symptoms"][:8]),
            drugs=", ".join(context["drugs"][:5]),
            difficulty=difficulty,
            difficulty_label=preset["label"],
            behavior_type=preset["behavior"],
        )
        return await self._llm_json(_SYSTEM_PROMPT, prompt)

    async def _generate_symptom_presentation(
        self, context: dict, difficulty: str
    ) -> dict:
        """Generate structured symptom categories."""
        preset = DIFFICULTY_PRESETS[difficulty]
        prompt = _SYMPTOMS_PROMPT.format(
            disease=context["disease"],
            symptoms=", ".join(context["symptoms"][:10]),
            differentials=", ".join(context["differentials"][:5]),
            comorbidities=", ".join(context["comorbidities"][:3]),
            difficulty=difficulty,
            difficulty_label=preset["label"],
            symptom_complexity=preset["symptom_complexity"],
        )
        return await self._llm_json(_SYSTEM_PROMPT, prompt)

    async def _generate_clinical_data(
        self, context: dict, persona: dict
    ) -> dict:
        """Generate realistic vitals, labs, medications."""
        profile = persona.get("profile", {})
        prompt = _CLINICAL_DATA_PROMPT.format(
            disease=context["disease"],
            symptoms=", ".join(context["symptoms"][:10]),
            drugs=", ".join(context["drugs"][:5]),
            drug_interactions=", ".join(context["drug_interactions"][:3]),
            comorbidities=", ".join(context["comorbidities"][:3]),
            age=profile.get("age", 50),
            gender=profile.get("gender", "unknown"),
        )
        return await self._llm_json(_SYSTEM_PROMPT, prompt)

    async def _generate_ground_truth(
        self, context: dict, clinical_data: dict, difficulty: str
    ) -> dict:
        """Generate diagnosis, treatment, safety checks, communication milestones."""
        preset = DIFFICULTY_PRESETS[difficulty]
        labs_available = list(clinical_data.get("labs", {}).keys())
        safety_concerns = []
        if clinical_data.get("allergies"):
            safety_concerns.append(f"Allergies: {', '.join(clinical_data['allergies'])}")
        if context["drug_interactions"]:
            safety_concerns.append(f"Drug interactions: {', '.join(context['drug_interactions'][:3])}")

        prompt = _GROUND_TRUTH_PROMPT.format(
            disease=context["disease"],
            differentials=", ".join(context["differentials"][:5]),
            all_symptoms=", ".join(context["symptoms"][:10]),
            drugs=", ".join(context["drugs"][:5]),
            drug_interactions=", ".join(context["drug_interactions"][:3]),
            labs=", ".join(labs_available[:8]),
            safety_concerns="; ".join(safety_concerns) or "none",
            difficulty=difficulty,
            difficulty_label=preset["label"],
        )
        return await self._llm_json(_SYSTEM_PROMPT, prompt)

    async def _generate_likelihood_table(
        self, context: dict, all_symptoms: list
    ) -> dict:
        """Generate symptom->disease probability table."""
        prompt = _LIKELIHOOD_TABLE_PROMPT.format(
            disease=context["disease"],
            differentials=", ".join(context["differentials"][:5]),
            all_symptoms=", ".join(all_symptoms[:12]),
        )
        return await self._llm_json(_SYSTEM_PROMPT, prompt)

    async def _generate_evaluation_criteria(
        self, context: dict, ground_truth: dict, difficulty: str
    ) -> dict:
        """Generate tool call sequence, NL assertions, solution paths."""
        prompt = _EVALUATION_PROMPT.format(
            disease=context["disease"],
            difficulty=difficulty,
            safety_checks=json.dumps(
                ground_truth.get("required_safety_checks", []), indent=2
            ),
            communication_milestones=json.dumps(
                ground_truth.get("communication_truth", []), indent=2
            ),
        )
        return await self._llm_json(_SYSTEM_PROMPT, prompt)

    async def _generate_patient_instructions(
        self, persona: dict, symptom_data: dict
    ) -> str:
        """Generate natural-language patient role-play instructions."""
        profile = persona.get("profile", {})
        behavior = persona.get("behavior", {})
        symptoms = symptom_data.get("symptoms", {})
        misconceptions = persona.get("misconceptions", {})

        # Generate a plausible Chinese-style name placeholder
        gender = profile.get("gender", "male")
        name = "ZhangXX" if gender == "male" else "LiXX"

        prompt = _PATIENT_INSTRUCTIONS_PROMPT.format(
            name=name,
            age=profile.get("age", 50),
            gender=gender,
            education=profile.get("education", "high_school"),
            occupation=profile.get("occupation", "worker"),
            chief_complaint=symptom_data.get("chief_complaint", "unknown"),
            behavior_type=behavior.get("type", "cooperative"),
            communication=behavior.get("communication", "clear"),
            volunteer_symptoms=", ".join(symptoms.get("volunteer", [])),
            if_asked_symptoms=", ".join(symptoms.get("if_asked", [])),
            hidden_symptoms=", ".join(symptoms.get("hidden", [])),
            resistant_symptoms=", ".join(symptoms.get("resistant", [])),
            misleading_symptoms=", ".join(symptoms.get("misleading", [])),
            economic_concerns=", ".join(
                misconceptions.get("economic_concerns", [])
            ),
        )
        result = await self._llm_json(_SYSTEM_PROMPT, prompt)
        return result.get("instructions", "")

    # ------------------------------------------------------------------
    # Main enrichment pipeline
    # ------------------------------------------------------------------

    async def enrich_task(
        self,
        walk_result: MultiPathWalkResult,
        difficulty: str = "L1",
        seed: Optional[int] = None,
    ) -> dict:
        """
        Enrich a PrimeKG walk result into a v3-format clinical task.

        Returns a dict matching the v3 task schema (see generated_tasks_v3/).
        """
        if difficulty not in DIFFICULTY_PRESETS:
            difficulty = "L1"
        preset = DIFFICULTY_PRESETS[difficulty]

        # 1. Extract clinical context from walk
        context = self._extract_context(walk_result)

        # 2. Generate persona + symptoms in parallel
        persona_coro = self._generate_patient_persona(context, difficulty)
        symptoms_coro = self._generate_symptom_presentation(context, difficulty)
        persona, symptom_data = await asyncio.gather(persona_coro, symptoms_coro)

        # 3. Generate clinical data (needs persona for age/gender)
        clinical_data = await self._generate_clinical_data(context, persona)

        # 4. Generate ground truth + likelihood table in parallel
        gt_coro = self._generate_ground_truth(context, clinical_data, difficulty)
        all_symptoms = (
            symptom_data.get("symptoms", {}).get("volunteer", [])
            + symptom_data.get("symptoms", {}).get("if_asked", [])
            + symptom_data.get("symptoms", {}).get("hidden", [])
            + symptom_data.get("symptoms", {}).get("resistant", [])
        )
        lt_coro = self._generate_likelihood_table(context, all_symptoms)
        ground_truth, likelihood_table = await asyncio.gather(gt_coro, lt_coro)

        # 5. Generate evaluation criteria
        eval_criteria = await self._generate_evaluation_criteria(
            context, ground_truth, difficulty
        )

        # 6. Generate patient instructions
        patient_instructions = await self._generate_patient_instructions(
            persona, symptom_data
        )

        # 7. Assemble v3 task
        task_seed = seed if seed is not None else random.randint(0, 999999)
        disease_slug = context["disease"].lower().replace(" ", "_")[:30]
        task_id = f"primekg_{difficulty}_{disease_slug}_{task_seed}"
        repro_hash = hashlib.sha256(
            json.dumps(
                {"walk_nodes": walk_result.main_path.nodes, "seed": task_seed},
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]

        v3_task = {
            "id": task_id,
            "task_config": {
                "domain": "internal_medicine",
                "task_type": "diagnostic_uncertainty",
                "difficulty": difficulty,
                "seed": task_seed,
                "max_turns": preset["max_turns"],
                "min_turns": preset["min_turns"],
                "version": "3.0",
                "reproducibility_hash": repro_hash,
            },
            "patient": {
                "profile": persona.get("profile", {}),
                "chief_complaint": symptom_data.get("chief_complaint", ""),
                "behavior": persona.get("behavior", {}),
                "symptoms": symptom_data.get("symptoms", {}),
                "progressive_reveal": symptom_data.get("progressive_reveal", []),
                "misconceptions": persona.get("misconceptions", {}),
                "instructions": patient_instructions,
            },
            "clinical": {
                "vitals": clinical_data.get("vitals", {}),
                "labs": clinical_data.get("labs", {}),
                "medications": clinical_data.get("medications", []),
                "comorbidities": clinical_data.get("comorbidities", []),
                "allergies": clinical_data.get("allergies", []),
                "confounders": clinical_data.get("confounders", []),
                "diagnosis": {
                    "primary": context["disease"],
                    "differentials": context["differentials"][:preset["num_differentials"]],
                },
                "likelihood_table": likelihood_table,
            },
            "ground_truth": ground_truth,
            "actions": {
                "ASK": {"id": 0, "type": "ASK", "subtype": "enum[open_question,targeted_question,clarification]", "cost": 1},
                "ORDER_LAB": {"id": 1, "type": "ORDER_LAB", "subtype": "diagnostic", "cost": 2},
                "GET_RESULTS": {"id": 2, "type": "GET_RESULTS", "cost": 0},
                "DIAGNOSE": {"id": 3, "type": "DIAGNOSE", "cost": 0},
                "CHECK_ALLERGY": {"id": 4, "type": "CHECK_ALLERGY", "cost": 0},
                "CHECK_INTERACTION": {"id": 5, "type": "CHECK_INTERACTION", "cost": 0},
                "PRESCRIBE": {"id": 6, "type": "PRESCRIBE", "subtype": "medication", "cost": 0},
                "EDUCATE": {"id": 7, "type": "EDUCATE", "subtype": "patient", "cost": 1},
                "SCHEDULE_FOLLOWUP": {"id": 8, "type": "SCHEDULE_FOLLOWUP", "cost": 0},
                "END": {"id": 9, "type": "END", "cost": 0},
                "tool_call_sequence": eval_criteria.get("tool_call_sequence", []),
            },
            "ground_truth_validation": {
                "rules": [
                    {
                        "type": "diagnosis_match",
                        "operator": "in",
                        "target": [context["disease"]],
                        "acceptable": context["differentials"][:preset["num_differentials"]],
                    },
                    {
                        "type": "forbidden_action",
                        "action": "PRESCRIBE",
                        "condition": "allergy_check == false",
                    },
                ],
                "diagnosis_target": [context["disease"]],
                "diagnosis_acceptable": context["differentials"][:preset["num_differentials"]],
                "safety_rules": [
                    {
                        "type": "forbidden_action",
                        "action": "PRESCRIBE",
                        "condition": "allergy_check == false",
                    }
                ],
            },
            "observations": {
                "mode": "delta",
                "history_included": False,
                "fields": ["symptoms_revealed", "lab_results", "patient_message", "state", "done"],
                "initial": {
                    "visible": ["patient.age", "patient.gender", "patient.chief_complaint"],
                    "hidden": ["clinical.labs", "clinical.diagnosis", "patient.symptoms.hidden"],
                },
            },
            "scoring": {
                "components": {
                    "diagnosis": {"method": "set_match", "weight": 0.25},
                    "safety": {"method": "rule_check", "weight": 0.25},
                    "communication": {"method": "milestone_check", "weight": 0.25},
                    "efficiency": {"method": "cost_ratio", "weight": 0.25},
                },
            },
            # Evaluation metadata for tau2 conversion
            "_eval": {
                "tool_call_sequence": eval_criteria.get("tool_call_sequence", []),
                "nl_assertions": eval_criteria.get("nl_assertions", []),
                "solution_space": eval_criteria.get("solution_space", {}),
                "reward_basis": preset["reward_basis"],
            },
            # Walk provenance
            "_primekg": {
                "walk_nodes": walk_result.main_path.nodes,
                "walk_complexity": walk_result.walk_complexity,
                "walk_type": walk_result.walk_type,
                "total_depth": walk_result.total_depth,
            },
        }

        return v3_task


# ---------------------------------------------------------------------------
# Batch enrichment helper
# ---------------------------------------------------------------------------

async def enrich_batch(
    walk_results: List[MultiPathWalkResult],
    difficulties: List[str],
    model: str = "azure/gpt-5.2",
    max_concurrency: int = 3,
    seed_start: int = 0,
) -> List[dict]:
    """
    Enrich a batch of walk results with concurrency control.

    Returns list of v3-format task dicts.
    """
    enricher = ClinicalTaskEnricher(model=model)
    semaphore = asyncio.Semaphore(max_concurrency)
    results: List[Optional[dict]] = [None] * len(walk_results)
    completed = {"count": 0, "failed": 0}
    total = len(walk_results)

    async def _enrich_one(idx: int):
        async with semaphore:
            try:
                task = await enricher.enrich_task(
                    walk_results[idx],
                    difficulty=difficulties[idx],
                    seed=seed_start + idx,
                )
                results[idx] = task
                completed["count"] += 1
            except Exception as e:
                print(f"  WARNING: Failed to enrich walk {idx}: {e}", flush=True)
                results[idx] = None
                completed["failed"] += 1
            done = completed["count"] + completed["failed"]
            if done % 5 == 0 or done == total:
                print(
                    f"  ... enriched {done}/{total} "
                    f"(ok={completed['count']}, failed={completed['failed']})",
                    flush=True,
                )

    await asyncio.gather(*[_enrich_one(i) for i in range(len(walk_results))])
    return [r for r in results if r is not None]
