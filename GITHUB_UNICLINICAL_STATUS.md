# UniClinicalDataEngine - GitHub Repository Status

**Repository**: https://github.com/circadiancity/agentmy/tree/main/UniClinicalDataEngine

**Last Updated**: 2026-03-12

---

## ✅ Complete File Structure

### Root Directory Files (12 files)

| File | Size | Description | Status |
|------|------|-------------|--------|
| `__init__.py` | 200 B | Package initialization | ✅ |
| `cli.py` | 2 KB | Command-line interface | ✅ |
| `engine.py` | 4.7 KB | Main ETL engine | ✅ |
| `models.py` | 3.8 KB | Data models (ClinicalScenario, PatientRecord) | ✅ |
| `task_builder.py` | 5.5 KB | Build tau2 tasks from scenarios | ✅ |
| `task_processor.py` | 17.3 KB | **⭐ TaskDeduplicator + TaskMerger** | ✅ |
| `policy_generator.py` | 2.9 KB | Generate policy.md | ✅ |
| `db_builder.py` | 2.2 KB | Build db.json | ✅ |
| `tool_generator.py` | 7.2 KB | Generate tools.json | ✅ |
| `tools.py` | 18.2 KB | Tool definitions | ✅ |
| `README.md` | 8.3 KB | Documentation | ✅ |
| `requirements.txt` | 628 B | Dependencies | ✅ |

### Subdirectories

#### 1. `adapters/` - Format Converters (6 files)

| File | Size | Description | Status |
|------|------|-------------|--------|
| `__init__.py` | - | Package init | ✅ |
| `base.py` | 2.9 KB | Abstract base class | ✅ |
| `csv_adapter.py` | 6.6 KB | CSV format support | ✅ |
| `excel_adapter.py` | 6.9 KB | Excel format support | ✅ |
| `json_adapter.py` | 8.4 KB | JSON format support | ✅ |
| `nhands_adapter.py` | 7.2 KB | NHands format support | ✅ |
| `medagentbench_adapter.py` | 11.5 KB | MedAgentBench format support | ✅ |

#### 2. `generators/` - Content Generators (7 files)

| File | Size | Description | Status |
|------|------|-------------|--------|
| `__init__.py` | 708 B | Package init | ✅ |
| `base_generator.py` | 3.8 KB | Base generator class | ✅ |
| `clinical_enricher.py` | 25.9 KB | **⭐ NEW! ClinicalDataEnricher** | ✅ |
| `mcq_converter.py` | 16.4 KB | MCQ to dialogue converter | ✅ |
| `output_generator.py` | 15.7 KB | Generate tau2 output files | ✅ |
| `template_manager.py` | 15.9 KB | Dialogue templates | ✅ |
| `utils.py` | 9.4 KB | Generator utilities | ✅ |

#### 3. `models/` - Model Definitions (1 file)

| File | Description | Status |
|------|-------------|--------|
| `__init__.py` | Model exports | ✅ |

#### 4. `tests/` - Test Suite (4 files)

| File | Description | Status |
|------|-------------|--------|
| `__init__.py` | Package init | ✅ |
| `test_adapters.py` | Adapter tests | ✅ |
| `test_engine.py` | Engine tests | ✅ |
| `test_etl.py` | ETL tests | ✅ |

#### 5. `utils/` - Utilities (3 files)

| File | Description | Status |
|------|-------------|--------|
| `__init__.py` | Package init | ✅ |
| `transformations.py` | Data transformations | ✅ |
| `validators.py` | Validation utilities | ✅ |

---

## 🎯 Key Modules on GitHub

### 1. TaskMerger + TaskDeduplicator
**File**: `task_processor.py` (17.3 KB)

**Classes**:
- `TaskDeduplicator` - Remove duplicate scenarios
- `TaskMerger` - Merge 2-5 simple tasks into 1 complex task
- `ScenarioProcessor` - Orchestrate deduplication and merging

**Features**:
- Text similarity detection
- Content hash matching
- Patient-based grouping
- Configurable thresholds

### 2. ClinicalDataEnricher ⭐ NEW!
**File**: `generators/clinical_enricher.py` (25.9 KB)

**Classes**:
- `ClinicalDataEnricher` - Add rich clinical details to tasks

**Features**:
- Automatic scenario type detection (5 types)
- Patient profile enrichment (demographics, history, medications)
- Clinical details generation (symptoms, risk factors, red flags)
- Vital signs and physical exam findings
- Lab results and imaging findings (optional)

**Supported Scenarios**:
- Acute Coronary Syndrome
- Heart Failure
- Arrhythmia
- Hypertensive Urgent
- Valvular Disease

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **Total Files** | 33 |
| **Total Lines of Python** | ~5,000+ |
| **Core Module Size** | 43 KB |
| **Supported Formats** | 5 (JSON, CSV, Excel, NHands, MedAgentBench) |
| **Scenario Types** | 5 (ACS, HF, Arrhythmia, HTN, Valvular) |
| **Last Update** | 2026-03-12 |

---

## 🚀 Usage Examples

### Using TaskMerger

```python
from UniClinicalDataEngine.task_processor import ScenarioProcessor

processor = ScenarioProcessor(
    enable_deduplication=True,
    enable_merging=True,
    merge_min_tasks=2,
    merge_max_tasks=5
)

final_tasks = processor.process(tasks)
```

### Using ClinicalDataEnricher

```python
from UniClinicalDataEngine.generators.clinical_enricher import ClinicalDataEnricher

enricher = ClinicalDataEnricher({
    'enrichment_level': 'moderate',
    'include_vitals': True,
    'include_lab_results': False
})

enriched_task = enricher.enrich_task(original_task)
```

---

## ✅ Verification Checklist

To verify all files are on GitHub, visit:
https://github.com/circadiancity/agentmy/tree/main/UniClinicalDataEngine

You should see:
- ✅ `task_processor.py` (contains TaskMerger + TaskDeduplicator)
- ✅ `generators/clinical_enricher.py` (NEW - contains ClinicalDataEnricher)
- ✅ All 33 files listed above

---

## 📝 Commit History

**Latest Commit** (5004ae7):
```
feat: add ClinicalDataEnricher module for improving clinical task quality

- Add ClinicalDataEnricher in UniClinicalDataEngine/generators/
- Add enrich_cardiology_data.py script
- Add CLINICAL_DATA_IMPROVEMENT_PLAN.md
- Add ENRICHER_DEMO_RESULTS.md
```

---

## 🔗 Quick Links

- **Repository**: https://github.com/circadiancity/agentmy
- **UniClinicalDataEngine**: https://github.com/circadiancity/agentmy/tree/main/UniClinicalDataEngine
- **Task Processor**: https://github.com/circadiancity/agentmy/blob/main/UniClinicalDataEngine/task_processor.py
- **Clinical Enricher**: https://github.com/circadiancity/agentmy/blob/main/UniClinicalDataEngine/generators/clinical_enricher.py

---

**Summary**: All 33 files are present on GitHub, including the new ClinicalDataEnricher module!
