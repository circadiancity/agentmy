# Project Restructuring Plan
## Clinical Domains Standardization

> **Date**: 2025-03-09
> **Status**: Detailed Planning Phase
> **Objective**: Restructure clinical domains to align with tau2-bench standard structure

---

## 📊 Current Structure Analysis

### Current Domain Organization
```
src/tau2/domains/
├── airline/
├── clinical_cardiology/      ⚠️ SCATTERED
├── clinical_endocrinology/   ⚠️ SCATTERED
├── clinical_gastroenterology/ ⚠️ SCATTERED
├── clinical_nephrology/      ⚠️ SCATTERED
├── clinical_neurology/       ⚠️ SCATTERED
├── mock/
├── retail/
└── telecom/

data/tau2/domains/
├── airline/
├── clinical_cardiology/      ⚠️ SCATTERED
├── clinical_endocrinology/   ⚠️ SCATTERED
├── clinical_gastroenterology/ ⚠️ SCATTERED
├── clinical_nephrology/      ⚠️ SCATTERED
├── clinical_neurology/       ⚠️ SCATTERED
├── mock/
├── retail/
└── telecom/

docs/clinical_tools/          ⚠️ SEPARATE LOCATION
├── CARDIOLOGY_*.md
├── NEUROLOGY_*.md
├── NEPHROLOGY_*.md
├── GASTROENTEROLOGY_*.md
├── ENDOCRINOLOGY_*.md
└── MEDICAL_REVIEW_SUMMARY.md
```

### Problems with Current Structure
1. **Clinical domains are scattered** as individual top-level domains
2. **No logical grouping** of clinical specialties
3. **Documentation separated** from domain code
4. **Inconsistent** with non-clinical domain organization

---

## 🎯 Target Structure

### Proposed Standard Structure
```
src/tau2/domains/
├── clinical/                  ✨ NEW GROUPING
│   ├── __init__.py           ✨ NEW
│   ├── cardiology/           ✨ RENAMED (from clinical_cardiology)
│   │   ├── __init__.py
│   │   ├── data_model.py
│   │   ├── environment.py
│   │   ├── tools.py
│   │   ├── user_data_model.py
│   │   ├── user_tools.py
│   │   └── utils.py
│   ├── endocrinology/        ✨ RENAMED (from clinical_endocrinology)
│   │   └── ...
│   ├── gastroenterology/     ✨ RENAMED (from clinical_gastroenterology)
│   │   └── ...
│   ├── nephrology/           ✨ RENAMED (from clinical_nephrology)
│   │   └── ...
│   ├── neurology/            ✨ RENAMED (from clinical_neurology)
│   │   └── ...
│   └── docs/                 ✨ MOVED & CONSOLIDATED
│       ├── cardiology/
│       │   ├── CARDIOLOGY_TOOLS_DEFINITION.md
│       │   └── CARDIOLOGY_POLICY.md
│       ├── endocrinology/
│       ├── gastroenterology/
│       ├── nephrology/
│       ├── neurology/
│       └── MEDICAL_REVIEW_SUMMARY.md
├── airline/
├── mock/
├── retail/
└── telecom/

data/tau2/domains/
├── clinical/                  ✨ NEW GROUPING
│   ├── cardiology/           ✨ RENAMED
│   │   ├── tasks.json
│   │   ├── db.json
│   │   ├── policy.md
│   │   └── split_tasks.json
│   ├── endocrinology/        ✨ RENAMED
│   ├── gastroenterology/     ✨ RENAMED
│   ├── nephrology/           ✨ RENAMED
│   ├── neurology/            ✨ RENAMED
│   └── shared/               ✨ OPTIONAL: Shared clinical resources
│       └── common_tools.json
├── airline/
├── mock/
├── retail/
└── telecom/
```

---

## 📋 Detailed Restructuring Steps

### Phase 1: Pre-Restructuring Preparation
**Duration**: 5 minutes
**Risk**: Low

#### Step 1.1: Create Backup
```bash
# Create timestamped backup
tar -czf tau2-bench-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    src/tau2/domains/clinical_* \
    data/tau2/domains/clinical_* \
    docs/clinical_tools/
```

#### Step 1.2: Stop All Services
- Stop any running evaluation processes
- Close all Python imports
- Ensure no file locks

#### Step 1.3: Document Current State
- [ ] List all files in clinical domains
- [ ] Record current import paths
- [ ] Document any custom configurations
- [ ] Save current registry.py state

---

### Phase 2: Source Code Restructuring
**Duration**: 15 minutes
**Risk**: Medium (requires import path updates)

#### Step 2.1: Create Clinical Directory Structure
```bash
cd "C:\Users\方正\tau2-bench\src\tau2\domains"

# Create new clinical parent directory
mkdir -p clinical
```

#### Step 2.2: Move Clinical Domain Directories
```bash
# Move each clinical domain under clinical/
mv clinical_cardiology clinical/cardiology
mv clinical_endocrinology clinical/endocrinology
mv clinical_gastroenterology clinical/gastroenterology
mv clinical_nephrology clinical/nephrology
mv clinical_neurology clinical/neurology
```

#### Step 2.3: Create Clinical Package Init File
```python
# src/tau2/domains/clinical/__init__.py
"""Clinical domains for tau2 benchmarking.

This package contains all clinical specialty domains for medical
consultation task evaluation.
"""

from tau2.domains.clinical.cardiology import *
from tau2.domains.clinical.endocrinology import *
from tau2.domains.clinical.gastroenterology import *
from tau2.domains.clinical.nephrology import *
from tau2.domains.clinical.neurology import *

__all__ = [
    "cardiology",
    "endocrinology",
    "gastroenterology",
    "nephrology",
    "neurology",
]
```

#### Step 2.4: Update Import Paths in Each Domain

For each clinical domain, update:
1. `__init__.py` - Update imports
2. `environment.py` - Update domain imports
3. `tools.py` - Update data model imports
4. `user_tools.py` - Update data model imports

**Pattern of changes**:
```python
# OLD
from tau2.domains.clinical_cardiology.data_model import CardiologyDB
from tau2.domains.clinical_cardiology.tools import CardiologyTools

# NEW
from tau2.domains.clinical.cardiology.data_model import CardiologyDB
from tau2.domains.clinical.cardiology.tools import CardiologyTools
```

---

### Phase 3: Data Restructuring
**Duration**: 10 minutes
**Risk**: Low (data only)

#### Step 3.1: Create Clinical Data Directory
```bash
cd "C:\Users\方正\tau2-bench\data\tau2\domains"

# Create new clinical parent directory
mkdir -p clinical
```

#### Step 3.2: Move Clinical Data Directories
```bash
# Move each clinical domain data under clinical/
mv clinical_cardiology clinical/cardiology
mv clinical_endocrinology clinical/endocrinology
mv clinical_gastroenterology clinical/gastroenterology
mv clinical_nephrology clinical/nephrology
mv clinical_neurology clinical/neurology
```

#### Step 3.3: Update Data Paths in utils.py

For each clinical domain, update `utils.py`:
```python
# OLD
TASKS_PATH = Path(__file__).parent.parent.parent / "data" / "tau2" / "domains" / "clinical_neurology" / "tasks.json"
DB_PATH = Path(__file__).parent.parent.parent / "data" / "tau2" / "domains" / "clinical_neurology" / "db.json"
POLICY_PATH = Path(__file__).parent.parent.parent / "data" / "tau2" / "domains" / "clinical_neurology" / "policy.md"

# NEW
TASKS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "tau2" / "domains" / "clinical" / "neurology" / "tasks.json"
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "tau2" / "domains" / "clinical" / "neurology" / "db.json"
POLICY_PATH = Path(__file__).parent.parent.parent.parent / "data" / "tau2" / "domains" / "clinical" / "neurology" / "policy.md"
```

---

### Phase 4: Documentation Restructuring
**Duration**: 5 minutes
**Risk**: Low

#### Step 4.1: Move Documentation to Clinical Domain
```bash
cd "C:\Users\方正\tau2-bench"

# Create docs directory structure under clinical
mkdir -p src/tau2/domains/clinical/docs

# Create subdirectories for each specialty
mkdir -p src/tau2/domains/clinical/docs/cardiology
mkdir -p src/tau2/domains/clinical/docs/endocrinology
mkdir -p src/tau2/domains/clinical/docs/gastroenterology
mkdir -p src/tau2/domains/clinical/docs/nephrology
mkdir -p src/tau2/domains/clinical/docs/neurology

# Move documentation files
mv docs/clinical_tools/CARDIOLOGY_*.md src/tau2/domains/clinical/docs/cardiology/
mv docs/clinical_tools/NEUROLOGY_*.md src/tau2/domains/clinical/docs/neurology/
mv docs/clinical_tools/NEPHROLOGY_*.md src/tau2/domains/clinical/docs/nephrology/
mv docs/clinical_tools/GASTROENTEROLOGY_*.md src/tau2/domains/clinical/docs/gastroenterology/
mv docs/clinical_tools/ENDOCRINOLOGY_*.md src/tau2/domains/clinical/docs/endocrinology/
mv docs/clinical_tools/MEDICAL_REVIEW_SUMMARY.md src/tau2/domains/clinical/docs/

# Optional: Also keep copies in docs/clinical/ for easier access
mkdir -p docs/clinical
cp -r src/tau2/domains/clinical/docs/* docs/clinical/
```

---

### Phase 5: Registry.py Updates
**Duration**: 15 minutes
**Risk**: High (central registration file)

#### Step 5.1: Update Import Statements in registry.py

**OLD imports**:
```python
from tau2.domains.clinical_nephrology.environment import (
    get_environment as clinical_nephrology_get_environment,
)
from tau2.domains.clinical_nephrology.environment import get_tasks as clinical_nephrology_get_tasks
from tau2.domains.clinical_nephrology.environment import (
    get_tasks_split as clinical_nephrology_get_tasks_split,
)
# ... (similar for other clinical domains)
```

**NEW imports**:
```python
from tau2.domains.clinical.nephrology.environment import (
    get_environment as clinical_nephrology_get_environment,
)
from tau2.domains.clinical.nephrology.environment import get_tasks as clinical_nephrology_get_tasks
from tau2.domains.clinical.nephrology.environment import (
    get_tasks_split as clinical_nephrology_get_tasks_split,
)
# ... (similar for other clinical domains)
```

#### Step 5.2: Update Domain Name Strings

In registry.py, domain names remain the same:
- `"clinical_nephrology"`
- `"clinical_cardiology"`
- etc.

This maintains backward compatibility with task configurations.

---

### Phase 6: Script Updates
**Duration**: 10 minutes
**Risk**: Medium

#### Step 6.1: Update run_evaluation.py

Check `run_evaluation.py` for any hardcoded paths:
```python
# Check if any path references exist
# OLD: domains/clinical_neurology
# NEW: domains/clinical/neurology (but domain name still "clinical_neurology")
```

#### Step 6.2: Update Other Scripts

Check and update:
- `validate_tau2_dialogues.py`
- `test_tau2_integration.py`
- Any scripts with domain references

---

### Phase 7: Path Updates in Domain Files
**Duration**: 20 minutes
**Risk**: Medium

#### Files Requiring Path Updates:

1. **Each clinical domain `__init__.py`** (5 files)
   - Update imports from own domain

2. **Each clinical domain `environment.py`** (5 files)
   - Update imports from tools, data_model
   - Update DB_PATH, TASKS_PATH, POLICY_PATH

3. **Each clinical domain `tools.py`** (5 files)
   - Update imports from data_model

4. **Each clinical domain `user_tools.py`** (5 files)
   - Update imports from user_data_model

**Total files to update**: ~20 files

---

### Phase 8: Validation & Testing
**Duration**: 30 minutes
**Risk**: High (validation phase)

#### Step 8.1: Import Validation
```bash
cd "C:\Users\方正\tau2-bench"

# Test Python imports
python -c "from tau2.registry import registry; print('Registry loaded successfully')"
python -c "from tau2.domains.clinical import *; print('Clinical domains loaded')"
python -c "from tau2.domains.clinical.neurology.environment import get_environment; print('Neurology loaded')"
```

#### Step 8.2: Registry Validation
```python
# Test registry function
from tau2.registry import registry

# Check all clinical domains are registered
clinical_domains = [d for d in registry.get_all_domains() if 'clinical' in d]
print(f"Registered clinical domains: {clinical_domains}")

# Expected output:
# ['clinical_cardiology', 'clinical_endocrinology', 'clinical_gastroenterology',
#  'clinical_nephrology', 'clinical_neurology']
```

#### Step 8.3: Environment Creation Test
```python
# Test environment creation for each clinical domain
from tau2.domains.clinical.cardiology.environment import get_environment as cardio_get_env
from tau2.domains.clinical.neurology.environment import get_environment as neuro_get_env

# Create environments
cardio_env = cardio_get_env()
neuro_env = neuro_get_env()

print("Cardiology environment created successfully")
print("Neurology environment created successfully")
```

#### Step 8.4: Data Loading Test
```python
# Test data loading
from tau2.domains.clinical.neurology.environment import get_tasks

tasks = get_tasks()
print(f"Loaded {len(tasks)} neurology tasks")
```

#### Step 8.5: Run Evaluation Test
```bash
# Quick evaluation test
python run_evaluation.py --domain clinical_neurology --max-tasks 1 --max-rounds 1
```

#### Step 8.6: Run Unit Tests
```bash
# Run existing test suite
pytest tests/ -v
```

---

### Phase 9: Cleanup & Finalization
**Duration**: 10 minutes
**Risk**: Low

#### Step 9.1: Remove Empty Directories
```bash
# Remove old docs/clinical_tools if empty
rmdir docs/clinical_tools 2>/dev/null || echo "Directory not empty or doesn't exist"
```

#### Step 9.2: Update Documentation
- Update README.md with new structure
- Update any developer documentation
- Create migration guide for other developers

#### Step 9.3: Git Commit
```bash
git add .
git commit -m "refactor: restructure clinical domains under clinical/ parent directory

- Move clinical domains from src/tau2/domains/clinical_* to src/tau2/domains/clinical/*/
- Move clinical data from data/tau2/domains/clinical_* to data/tau2/domains/clinical/*/
- Move documentation from docs/clinical_tools/ to src/tau2/domains/clinical/docs/
- Update all import paths in registry.py, environment.py, tools.py, user_tools.py
- Update data paths in utils.py files
- Maintain backward compatibility with domain names (clinical_neurology, etc.)

BREAKING CHANGE: Import paths changed for clinical domains
Old: from tau2.domains.clinical_neurology import ...
New: from tau2.domains.clinical.neurology import ...
"
```

---

## 📊 Impact Assessment

### Files Affected

| Category | Count | Files |
|----------|-------|-------|
| **Source Directories Moved** | 5 | clinical_cardiology, clinical_endocrinology, clinical_gastroenterology, clinical_nephrology, clinical_neurology |
| **Data Directories Moved** | 5 | Same as above |
| **Documentation Files Moved** | 11 | 5 tools definitions, 5 policies, 1 summary |
| **Python Files with Updated Imports** | ~25 | registry.py, environment.py, tools.py, user_tools.py, __init__.py for each domain |
| **New Files Created** | 1 | clinical/__init__.py |

### Import Path Changes

| Component | Old Path | New Path |
|-----------|----------|----------|
| **Cardiology environment** | `tau2.domains.clinical_cardiology.environment` | `tau2.domains.clinical.cardiology.environment` |
| **Neurology environment** | `tau2.domains.clinical_neurology.environment` | `tau2.domains.clinical.neurology.environment` |
| **Nephrology environment** | `tau2.domains.clinical_nephrology.environment` | `tau2.domains.clinical.nephrology.environment` |
| **Gastroenterology environment** | `tau2.domains.clinical_gastroenterology.environment` | `tau2.domains.clinical.gastroenterology.environment` |
| **Endocrinology environment** | `tau2.domains.clinical_endocrinology.environment` | `tau2.domains.clinical.endocrinology.environment` |

### Domain Name Strings (UNCHANGED)
- Task configurations using `"clinical_neurology"` remain valid
- Registry names remain `"clinical_neurology"`, etc.
- **Backward compatible** at the configuration level

---

## ⚠️ Risk Mitigation

### High Risk Areas
1. **registry.py** - Central file, errors break all domain loading
   - **Mitigation**: Test each import change immediately
   - **Rollback plan**: Keep backup of original registry.py

2. **Import Path Updates** - 20+ files to update
   - **Mitigation**: Use automated find-replace with verification
   - **Rollback plan**: Git revert if needed

3. **Data Path Updates** - utils.py in each domain
   - **Mitigation**: Verify path calculations
   - **Rollback plan**: Revert from backup

### Rollback Plan
If restructuring fails:
1. Stop all changes
2. Restore from backup: `tar -xzf tau2-bench-backup-YYYYMMDD-HHMMSS.tar.gz`
3. Git revert: `git checkout -- .`
4. Investigate failure
5. Fix issues and retry

---

## ✅ Success Criteria

Restructuring is complete when:
- [ ] All 5 clinical domains moved under `src/tau2/domains/clinical/`
- [ ] All 5 clinical data directories moved under `data/tau2/domains/clinical/`
- [ ] All documentation moved to `src/tau2/domains/clinical/docs/`
- [ ] All import paths updated (25+ files)
- [ ] `registry.py` successfully imports all clinical domains
- [ ] Environment creation works for all clinical domains
- [ ] Task loading works for all clinical domains
- [ ] `run_evaluation.py` executes successfully
- [ ] All unit tests pass
- [ ] No broken imports or path references

---

## 📅 Timeline Estimate

| Phase | Duration | Buffer | Total |
|-------|----------|-------|-------|
| Preparation | 5 min | 5 min | 10 min |
| Source Code Restructuring | 15 min | 10 min | 25 min |
| Data Restructuring | 10 min | 5 min | 15 min |
| Documentation Restructuring | 5 min | 5 min | 10 min |
| Registry Updates | 15 min | 10 min | 25 min |
| Script Updates | 10 min | 5 min | 15 min |
| Path Updates in Domain Files | 20 min | 10 min | 30 min |
| Validation & Testing | 30 min | 15 min | 45 min |
| Cleanup & Finalization | 10 min | 5 min | 15 min |
| **TOTAL** | **120 min** | **70 min** | **190 min (3h 10min)** |

---

## 🚀 Execution Order

Execute phases sequentially:
1. ✅ Phase 1: Preparation
2. ✅ Phase 2: Source Code (do completely before Phase 3)
3. ✅ Phase 3: Data (do completely before Phase 4)
4. ✅ Phase 4: Documentation
5. ✅ Phase 5: Registry (critical - validate immediately)
6. ✅ Phase 6: Scripts
7. ✅ Phase 7: Path Updates (validate each domain)
8. ✅ Phase 8: Validation (comprehensive testing)
9. ✅ Phase 9: Cleanup

After each phase, run validation tests before proceeding.

---

## 📞 Support & Contacts

**Questions or issues?**
- Check backup before any destructive operations
- Test changes in isolation when possible
- Commit after each successful phase
- Keep detailed notes of any deviations from plan

---

**Document Version**: 1.0
**Last Updated**: 2025-03-09
**Status**: Ready for Execution

**End of Plan**
