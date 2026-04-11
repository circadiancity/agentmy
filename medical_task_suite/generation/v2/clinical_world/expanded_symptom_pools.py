#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expanded Symptom Pools — Larger noise/misleading pools from PrimeKG + curation.

Replaces the hand-coded 19-item NOISE_SYMPTOM_POOL and 10-item MISLEADING_SYMPTOM_MAP
with expanded versions derived from PrimeKG phenotype analysis and clinical curation.

Usage:
    from .expanded_symptom_pools import EXPANDED_NOISE_SYMPTOM_POOL, EXPANDED_MISLEADING_SYMPTOM_MAP
"""

from typing import Dict, List


# ============================================================
# Expanded Noise Symptom Pool (60+ symptoms)
# ============================================================

EXPANDED_NOISE_SYMPTOM_POOL: List[str] = [
    # Original 19 (kept)
    "mild headache", "occasional dizziness", "minor skin rash",
    "slight nausea", "mild fatigue", "intermittent back pain",
    "occasional heartburn", "mild joint stiffness", "slight blurry vision",
    "trouble sleeping", "dry mouth", "mild anxiety",
    "occasional ringing in ears", "slight swelling in ankles",
    "mild constipation", "bloating", "mild throat irritation",
    "occasional muscle cramps", "slight hand numbness",

    # New: General symptoms (patient-reportable, low specificity)
    "dry skin", "brittle nails", "hair thinning",
    "mild eye dryness", "occasional eye floaters",
    "mild jaw clicking", "clicking in knee",
    "occasional tingling in fingers", "cold hands and feet",
    "mild sweating at night", "occasional hot flashes",
    "mild sensitivity to light", "occasional ear fullness",
    "slight tremor in hands", "mild unsteadiness when walking",
    "occasional food craving", "metallic taste in mouth",
    "mild body odor change", "slight change in urine color",
    "occasional shallow breathing", "mild weakness in arms",

    # New: Common benign symptoms
    "morning stiffness", "occasional heart pounding after exercise",
    "mild itching without rash", "slight sensitivity to cold",
    "occasional clicking jaw", "mild foot arch pain",
    "slight memory fog", "occasional word-finding difficulty",
    "mild neck tension", "slight shoulder tightness",
    "occasional twitching eyelid", "mild teeth grinding",
    "slight change in appetite", "mild indigestion after spicy food",
    "occasional yawning", "slight voice hoarseness in morning",
    "mild sensitivity to noise", "occasional deja vu",
]


# ============================================================
# Expanded Misleading Symptom Map (30+ diseases)
# ============================================================

EXPANDED_MISLEADING_SYMPTOM_MAP: Dict[str, List[str]] = {
    # Original 10 (kept)
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

    # New: Cardiovascular
    "hyperlipidemia": ["yellow skin bumps", "arcus corneae"],
    "pulmonary embolism": ["leg swelling", "calf pain"],
    "deep vein thrombosis": ["leg warmth", "leg redness"],

    # New: Endocrine
    "hyperthyroidism": ["heat intolerance", "bulging eyes"],
    "hypothyroidism": ["cold intolerance", "puffy face"],
    "metabolic syndrome": ["darkened skin folds", "increased thirst"],

    # New: Respiratory
    "pneumonia": ["chest pain with breathing", "night sweats"],
    "bronchitis": ["wheezing", "low-grade fever"],
    "sleep apnea": ["morning headache", "difficulty concentrating"],

    # New: Neurological
    "migraine": ["neck stiffness", "visual spots"],
    "epilepsy": ["confusion", "memory loss"],
    "parkinson disease": ["soft voice", "small handwriting"],
    "multiple sclerosis": ["eye pain with movement", "electric shock sensation"],

    # New: GI
    "cirrhosis": ["spider-like blood vessels", "red palms"],
    "pancreatitis": ["back pain", "fatty stools"],
    "peptic ulcer disease": ["nighttime stomach pain", "bloating"],
    "irritable bowel syndrome": ["urgency", "incomplete evacuation"],

    # New: Musculoskeletal
    "rheumatoid arthritis": ["morning stiffness over 1 hour", "symmetrical joint pain"],
    "gout": ["red hot joint", "intense pain at night"],
    "osteoporosis": ["height loss", "stooped posture"],
    "fibromyalgia": ["tender points", "widespread pain"],

    # New: Renal/Heme
    "chronic kidney disease": ["metallic taste", "itching all over"],
    "anemia": ["pale skin", "cold hands"],
    "nephrolithiasis": ["groin pain", "blood in urine"],

    # New: Other
    "depression": ["unexplained aches", "social withdrawal"],
    "anemia": ["pale skin", "cold hands"],
    "psoriasis": ["joint pain", "nail pitting"],
    "meningitis": ["light sensitivity", "stiff neck"],
}


# ============================================================
# Atypical / Rare Symptom Presentations (Structural Uncertainty)
# ============================================================
# These are REAL but uncommon ways a disease can present.
# Injecting them per-task prevents agents from memorizing canonical
# disease-symptom mappings — the same disease produces different
# symptom sets across tasks.

ATYPICAL_SYMPTOMS: Dict[str, List[str]] = {
    # Endocrine
    "type 2 diabetes": [
        "recurrent skin infections", "slow wound healing",
        "darkened skin patches on neck", "frequent yeast infections",
        "numbness in feet and toes", "bladder control problems",
        "erectile dysfunction", "vision fluctuations throughout day",
        "unexplained irritability", "tingling in hands at night",
    ],
    "hyperthyroidism": [
        "proximal muscle weakness", "pretibial myxedema",
        "lid lag when looking down", "increased appetite with weight loss",
        "heat intolerance at room temperature", "hair thinning",
        "frequent bowel movements", "difficulty climbing stairs",
    ],
    "hypothyroidism": [
        "carpal tunnel syndrome", "constipation alternating with normal",
        "depression resistant to treatment", "puffy face and eyes",
        "thinning eyebrows outer third", "hoarse voice",
        "elevated cholesterol despite diet", "cold intolerance in warm rooms",
    ],
    "hyperlipidemia": [
        "xanthelasma around eyes", "tendon xanthomas on hands",
        "corneal arcus in young age", "recurrent pancreatitis",
    ],
    "hypertension": [
        "early morning occipital headache", "spontaneous nosebleeds",
        "visual disturbances without eye disease", "facial flushing",
        "pounding sensation in ears", "blood spots in eyes",
        "difficulty concentrating in morning", "nocturia",
    ],

    # Cardiovascular
    "coronary artery disease": [
        "pain between shoulder blades", "jaw discomfort during exertion",
        "unusual fatigue preceding chest pain", "indigestion-like chest discomfort",
        "cold sweat without exertion", "left arm tingling without chest pain",
        "new onset erectile dysfunction", "shortness of breath lying flat",
    ],
    "heart failure": [
        "orthopnea requiring multiple pillows", "paroxysmal nocturnal dyspnea",
        "abdominal fullness after small meals", "unexplained weight gain overnight",
        "difficulty bending over to tie shoes", "waking up gasping",
        "swelling in scrotum", "loss of appetite despite not eating",
    ],
    "atrial fibrillation": [
        "irregular pulse noticed incidentally", "exercise intolerance out of proportion",
        "lightheadedness on standing", "nocturnal palpitations",
        "sudden onset after heavy meal", "vagal triggers like cold water",
    ],
    "stroke": [
        "sudden vision loss in one eye (TIA)", "difficulty finding words",
        "sudden unsteady gait without dizziness", "new onset severe headache",
        "sudden hemianopia", "difficulty swallowing",
        "personality change after fall", "facial droop noticed by family",
    ],
    "pulmonary embolism": [
        "calf swelling after long flight", "hemoptysis with pleuritic pain",
        "sudden syncope", "low-grade fever with chest pain",
        "tachycardia at rest", "worsening dyspnea over days",
    ],

    # Respiratory
    "copd": [
        "morning headache that improves with activity", "barrel chest appearance",
        "pursed lip breathing noticed by family", "difficulty cooking due to breathlessness",
        "ankle swelling worse at night", "cyanotic lips",
        "frequent winter exacerbations", "decreased ability to whistle",
    ],
    "asthma": [
        "cough-variant without wheezing", "exercise-induced only",
        "nighttime cough without daytime symptoms", "cold air trigger",
        "difficulty singing or speaking in full sentences", "throat clearing",
    ],
    "pneumonia": [
        "confusion in elderly without fever", "rigors followed by fever",
        "pleuritic chest pain on deep breath", "rust-colored sputum",
        "rapid breathing at rest", "delirium as sole presenting symptom",
    ],

    # Renal
    "chronic kidney disease": [
        "metallic taste in mouth", "persistent itching all over",
        "restless legs at night", "urinating multiple times at night",
        "foamy urine", "muscle cramps at night",
        "difficulty keeping blood pressure controlled", "anemia resistant to iron",
    ],
    "nephrolithiasis": [
        "groin pain radiating from flank", "hematuria visible or microscopic",
        "urinary urgency with stone", "referred pain to testicle",
        "nausea with flank pain", "inability to find comfortable position",
    ],

    # GI
    "gerd": [
        "chronic cough worse at night", "hoarseness in morning",
        "globus sensation in throat", "dental erosion without cause",
        "asthma symptoms worse after meals", "sour taste waking from sleep",
    ],
    "cirrhosis": [
        "spider angiomas on chest", "palmar erythema",
        "gynecomastia", "testicular atrophy",
        "bruising easily", "forgetfulness and confusion",
    ],
    "pancreatitis": [
        "pain radiating straight through to back", "relief by leaning forward",
        "fatty foul-smelling stools", "new onset diabetes",
    ],

    # Neurological
    "migraine": [
        "aura without headache", "vestibular symptoms",
        "neck stiffness preceding headache", "visual scintillating scotoma",
        "hemiplegic migraine with weakness", "brainstem symptoms",
    ],
    "epilepsy": [
        "deja vu before seizure", "automatisms like lip smacking",
        "post-ictal confusion lasting hours", "nocturnal seizures only",
        "focal aware seizures without loss of awareness", "olfactory aura",
    ],
    "parkinson disease": [
        "micrographia", "hypophonia (soft voice)",
        "reduced arm swing on one side", "loss of smell",
        "REM sleep behavior disorder", "constipation preceding motor symptoms",
    ],

    # Musculoskeletal
    "rheumatoid arthritis": [
        "morning stiffness lasting over 1 hour", "symmetrical joint involvement",
        "rheumatoid nodules on elbows", "dry eyes and mouth (secondary Sjogren)",
        "flexor tenosynovitis", "cervical spine involvement",
    ],
    "gout": [
        "podagra (first MTP joint)", "intense pain waking from sleep",
        "tophi on ears and elbows", "red hot joint mimicking cellulitis",
        "triggered by alcohol or rich food", "polyarticular flare",
    ],
    "osteoporosis": [
        "height loss over time", "stooped posture developing gradually",
        "fracture from minimal trauma", "back pain from compression fracture",
    ],
    "osteoarthritis": [
        "joint stiffness less than 30 minutes", "bony enlargement at joints",
        "crepitus with joint movement", "worse with use better with rest",
    ],

    # Psychiatric
    "anxiety disorder": [
        "physical symptoms dominating presentation", "health anxiety",
        "chronic tension headaches", "muscle tension in neck and shoulders",
        "irritable bowel symptoms", "dizziness without vestibular cause",
        "difficulty swallowing (globus)", "insomnia with racing thoughts",
    ],
    "depression": [
        "unexplained chronic pain", "multiple somatic complaints",
        "social withdrawal noticed by family", "cognitive decline in elderly",
        "weight changes without trying", "loss of interest in hobbies",
    ],

    # Hematologic
    "anemia": [
        "pica (craving ice or dirt)", "restless legs",
        "sore tongue", "brittle nails with spoon shape",
        "cold intolerance", "shortness of breath on minimal exertion",
    ],
}

# ============================================================
# Symptom Perturbation Map (structural variation of descriptions)
# ============================================================
# Maps canonical symptom → variant descriptions.
# Per-task, one variant may replace the canonical form.

SYMPTOM_VARIANTS: Dict[str, List[str]] = {
    "fatigue": ["feeling tired all the time", "no energy for daily activities",
                "exhaustion even after rest", "worn out by afternoon"],
    "headache": ["pressure in head", "throbbing head pain",
                 "dull ache across forehead", "splitting headache"],
    "chest pain": ["tightness in chest", "pressure in chest",
                   "squeezing sensation in chest", "heavy feeling on chest"],
    "shortness of breath": ["can't catch breath", "breathless with minimal effort",
                            "trouble breathing lying down", "gasping for air"],
    "dizziness": ["room spinning", "feeling lightheaded",
                  "unsteady on feet", "about to faint"],
    "nausea": ["feeling sick to stomach", "queasy",
               "want to throw up", "stomach turning"],
    "cough": ["hacking cough", "persistent cough",
              "dry annoying cough", "cough that won't go away"],
    "joint pain": ["aching joints", "sore joints",
                   "joints that hurt to move", "stiff and painful joints"],
    "swelling": ["puffy ankles", "retaining water",
                 "bloated and swollen", "shoes feel tight from swelling"],
    "weakness": ["no strength", "muscles feel like jelly",
                 "can barely lift things", "everything feels heavy"],
}

# ============================================================
# Expanded Confounder Pool (Structural Uncertainty)
# ============================================================
# Wider pool of diseases that can mimic the primary.
# The scenario generator randomly samples from this pool,
# so the hypothesis space varies across tasks.

EXPANDED_CONFOUNDER_MAP: Dict[str, List[str]] = {
    "type 2 diabetes": [
        "hyperthyroidism", "diabetes insipidus", "anxiety disorder",
        "chronic kidney disease", "hypercalcemia", "acromegaly",
        "Cushing syndrome", "pancreatitis",
    ],
    "hypertension": [
        "anxiety disorder", "pain crisis", "sleep apnea",
        "hyperthyroidism", "coarctation of aorta", "pheochromocytoma",
        "Cushing syndrome", "primary aldosteronism", "renal artery stenosis",
    ],
    "coronary artery disease": [
        "gerd", "anxiety disorder", "musculoskeletal chest pain",
        "pericarditis", "aortic dissection", "pulmonary embolism",
        "costochondritis", "esophageal spasm", "peptic ulcer disease",
    ],
    "copd": [
        "asthma", "heart failure", "lung cancer", "bronchiectasis",
        "tuberculosis", "pneumonia", "pulmonary fibrosis",
        "occupational lung disease",
    ],
    "asthma": [
        "copd", "vocal cord dysfunction", "gerd", "heart failure",
        "pulmonary embolism", "cystic fibrosis", "allergic bronchopulmonary aspergillosis",
    ],
    "heart failure": [
        "copd", "pneumonia", "pulmonary embolism", "anemia",
        "nephrotic syndrome", "cirrhosis", "thyroid disease",
        "pericardial effusion",
    ],
    "stroke": [
        "migraine", "hypoglycemia", "seizure", "bell palsy",
        "brain tumor", "multiple sclerosis", "functional neurological disorder",
        "subdural hematoma",
    ],
    "atrial fibrillation": [
        "anxiety disorder", "hyperthyroidism", "excessive caffeine",
        "heart failure", "pulmonary embolism", "alcohol withdrawal",
        "electrolyte imbalance", "sick sinus syndrome",
    ],
    "chronic kidney disease": [
        "anemia", "hypertension", "heart failure", "diabetes insipidus",
        "nephrotic syndrome", "urinary tract obstruction", "renal artery stenosis",
    ],
    "rheumatoid arthritis": [
        "osteoarthritis", "gout", "lupus", "psoriatic arthritis",
        "reactive arthritis", "viral arthritis", "Lyme disease",
    ],
    "gerd": [
        "asthma", "coronary artery disease", "esophageal spasm",
        "achalasia", "eosinophilic esophagitis", "peptic ulcer disease",
    ],
    "hyperlipidemia": [
        "hypothyroidism", "nephrotic syndrome", "cholestasis",
        "diabetes", "Cushing syndrome",
    ],
    "pneumonia": [
        "copd exacerbation", "asthma", "heart failure", "pulmonary embolism",
        "lung cancer", "tuberculosis", "bronchiolitis",
    ],
    "migraine": [
        "tension headache", "stroke", "sinusitis", "cluster headache",
        "subarachnoid hemorrhage", "temporal arteritis", "idiopathic intracranial hypertension",
    ],
    "epilepsy": [
        "syncope", "psychogenic nonepileptic seizure", "TIA",
        "migraine with aura", "sleep disorder", "cardiac arrhythmia",
    ],
    "parkinson disease": [
        "essential tremor", "multiple system atrophy", "drug-induced parkinsonism",
        "normal pressure hydrocephalus", "Lewy body dementia",
        "progressive supranuclear palsy", "Wilson disease",
    ],
    "gout": [
        "rheumatoid arthritis", "osteoarthritis", "cellulitis",
        "pseudogout", "reactive arthritis", "septic arthritis",
    ],
    "osteoporosis": [
        "osteomalacia", "multiple myeloma", "metastatic bone disease",
        "hyperparathyroidism", "Paget disease", "Cushing syndrome",
    ],
    "anemia": [
        "chronic disease", "iron deficiency", "b12 deficiency",
        "thalassemia", "bone marrow failure", "hemolysis",
    ],
    "anxiety disorder": [
        "hyperthyroidism", "cardiac arrhythmia", "pheochromocytoma",
        "caffeine excess", "alcohol withdrawal", "depression",
    ],
    "depression": [
        "hypothyroidism", "anemia", "dementia", "chronic fatigue syndrome",
        "vitamin D deficiency", "bipolar disorder depressive phase",
    ],
    "nephrolithiasis": [
        "appendicitis", "ectopic pregnancy", "ovarian torsion",
        "pyelonephritis", "aortic aneurysm", "musculoskeletal back pain",
    ],
    "pulmonary embolism": [
        "pneumonia", "pleurisy", "anxiety disorder", "heart failure",
        "copd exacerbation", "aortic dissection", "pneumothorax",
    ],
    "hyperthyroidism": [
        "anxiety disorder", "pheochromocytoma", "caffeine excess",
        "heart failure", "mania", "chronic lung disease",
    ],
}

# ============================================================
# Structural Uncertainty Configuration
# ============================================================
# Drop/perturbation rates per difficulty level.
# Higher difficulty = more structural variation.

STRUCTURAL_UNCERTAINTY_CONFIG = {
    "L1": {
        "canonical_drop_rate": (0.0, 0.15),   # Keep most canonical symptoms
        "atypical_inject_rate": (0.0, 0.2),   # Rarely add atypical symptoms
        "variant_replace_rate": 0.1,           # 10% chance to perturb a symptom
        "max_atypical_added": 1,              # At most 1 atypical symptom
    },
    "L2": {
        "canonical_drop_rate": (0.1, 0.3),    # May drop 10-30% of canonical
        "atypical_inject_rate": (0.2, 0.5),   # 20-50% chance to add atypical
        "variant_replace_rate": 0.25,          # 25% chance to perturb
        "max_atypical_added": 2,
    },
    "L3": {
        "canonical_drop_rate": (0.2, 0.45),   # May drop 20-45% of canonical
        "atypical_inject_rate": (0.4, 0.7),   # 40-70% chance to add atypical
        "variant_replace_rate": 0.4,           # 40% chance to perturb
        "max_atypical_added": 3,
    },
}


def generate_misleading_from_overlap(
    disease: str,
    disease_symptoms: List[str],
    overlap_diseases: Dict[str, float],
    overlap_symptom_map: Dict[str, List[str]],
) -> List[str]:
    """
    Generate misleading symptoms from symptom overlap between diseases.

    For each overlapping disease, pick symptoms present in the overlap disease
    but NOT in the target disease. These are naturally misleading because they
    suggest the wrong diagnosis.

    Args:
        disease: Target disease name
        disease_symptoms: Target disease's symptoms
        overlap_diseases: {other_disease: jaccard_score}
        overlap_symptom_map: {disease: [symptoms]}

    Returns:
        List of misleading symptoms
    """
    target_set = {s.lower() for s in disease_symptoms}
    misleading = []

    # Sort by overlap score (highest overlap = most confusing)
    sorted_overlaps = sorted(overlap_diseases.items(), key=lambda x: -x[1])

    for other_disease, overlap_score in sorted_overlaps[:3]:
        other_symptoms = overlap_symptom_map.get(other_disease, [])
        # Symptoms in other disease but NOT in target = misleading
        for symptom in other_symptoms:
            if symptom.lower() not in target_set and symptom not in misleading:
                misleading.append(symptom)
                if len(misleading) >= 3:
                    return misleading

    return misleading
