# Clinical Science Benchmark Design

## 1. Role Mapping

| Tau2 Role | Clinical Benchmark Role |
|-----------|------------------------|
| User      | Patient                |
| Agent     | Clinician              |

---

## 2. Task Definition Schema

Each task is defined as a JSON object with the following components:

- **Task Definition** (JSON): Describes the clinical scenario, patient context, and expected clinician actions.
- **Tool Definitions** (Markdown): Documents the tools available to the clinician agent.
- **Evaluation Criteria**: What the evaluator checks after the conversation, e.g.:
  - *Action check*: Drug B123 (Cocaine) is prescribed.
  - *Communication check*: Patient is informed they need rest.

### Example Tool

```python
def find_patient_info(name: str) -> Patient:
    """Look up patient record by name."""
    return Patient(year, sex, past_record, weight)
```

### Example Conversation

```
Patient:   My name is Zehui, I feel bad.
Clinician: Hello, sorry to hear that. Do you feel pain in your head?
Patient:   Yes.
Clinician: [calls find_patient_info("Zehui")]
```

### Evaluation

```
evaluator(conversation, criteria) -> reward: 0 / 1 / 2
```

- **0** = Failure (wrong or missing actions/communication)
- **1** = Partial success
- **2** = Full success

---

## 3. Data Pipeline

### Stage 1: UniClinicalDataEngine

Converts raw clinical data (e.g. from NHands or other clinical sources) into candidate task definitions.

```
raw clinical data --> UniClinicalDataEngine --> candidate task definitions
```

### Stage 2: Data Quality Filtering

Two approaches for filtering candidate tasks, both using a score threshold (e.g. 50/100):

#### Approach A: Fully Human Review

```python
def process_with_human_review(task_definitions, threshold=50):
    return [task for task in task_definitions
            if human_check(task) >= threshold]
```

#### Approach B: Semi-Automated Review (LLM + Guidance)

```python
def semi_human_check(llm, guidance, task):
    """Use an LLM with clinical guidance to score a task definition."""
    prompt = "According to the guidance, check if the task definition is good. Give a score."
    return llm(prompt, guidance, task)

def process_with_semi_auto_review(task_definitions, threshold=50):
    return [task for task in task_definitions
            if semi_human_check(llm, guidance, task) >= threshold]
```

### Stage 3: Validate Semi-Automated Review

Use a calibration set of 50 tasks scored by both methods:

1. Compute `pearson_correlation(semi_human_check(task_50_set), human_check(task_50_set))`
2. **Target**: correlation > 0.5 (existing benchmarks typically achieve 0.3 -- 0.5)

---

## 4. Benchmark Scale

| Dimension | Target |
|-----------|--------|
| Domains   | 4      |
| Tasks     | 100    |
| Models    | 5      |

---

## 5. Authentication

Access to patient data tools is gated by a token (password-based auth), consistent with the tau2 orchestrator's token injection mechanism.
