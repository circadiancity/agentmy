# ThReadMed-QA Conversion Summary

## 🎯 Objective

Convert **ThReadMed-QA** - the first large-scale benchmark of authentic, multi-turn patient-physician dialogue - to tau2-bench format for medical consultation evaluation.

## 📊 Dataset Information

| Property | Value |
|---|---|
| **Dataset Name** | ThReadMed-QA |
| **Source** | Reddit r/AskDocs |
| **Paper** | arXiv:2603.11281 |
| **GitHub** | github.com/monicamunnangi/ThReadMed-QA |
| **Total Conversations** | 2,437 |
| **Total QA Pairs** | 8,204 |
| **Max Turns** | 9 |
| **Median Follow-ups** | 2 |
| **Language** | English |

## ✨ Key Advantages

### 1. **True Multi-Turn Dialogues** ✅
- Patient questions with follow-ups
- Physician responses to each question
- Realistic clarification and refinement patterns
- Reflects actual online consultation behavior

### 2. **High-Quality Ground Truth** ✅
- Verified physician responses
- 100% response coverage
- LLM-as-judge evaluation rubric
- Clinically validated scoring criteria

### 3. **Comprehensive Evaluation** ✅
- Turn-Level Degradation metrics
- Conversational Consistency Score (CCS)
- Error Propagation Rate (EPR)
- Tested on 5 frontier LLMs

## 🆚 Comparison with Other Datasets

| Dataset | Type | Authenticity | Multi-turn | Size |
|---------|------|--------------|------------|------|
| **ThReadMed-QA** | Real dialogue | ✅ Authentic | ✅ Yes | 2,437 conv |
| MedXpertQA | Simulated from MCQ | ⚠️ Simulated | ✅ Yes | 2,450 tasks |
| Chinese MedDialog | Real QA | ✅ Authentic | ❌ Single-turn | 792,099 QA |
| LCMDC | Real QA | ✅ Authentic | ❌ Single-turn | 472,418 QA |

## 📋 Conversion Steps

### Step 1: Download Dataset
```bash
# Option A: Git clone
cd data/raw/medical_dialogues/threadmed_qa
git clone https://github.com/monicamunnangi/ThReadMed-QA.git .

# Option B: Download ZIP manually
# 1. Visit https://github.com/monicamunnangi/ThReadMed-QA
# 2. Click "Code" → "Download ZIP"
# 3. Extract to data/raw/medical_dialogues/threadmed_qa/
```

### Step 2: Run Conversion Script
```bash
python convert_threadmed_qa.py
```

### Step 3: Verify Output
```bash
# Check converted files
ls -la data/processed/medical_dialogues/threadmed_qa/

# Expected output:
# - tasks.json (all tasks)
# - tasks_train.json (training set)
# - tasks_val.json (validation set)
# - tasks_test.json (test set)
# - db.json (patient database)
# - split_tasks.json (data splits)
```

### Step 4: Run Evaluation
```bash
# Run tau2-bench evaluation
python run_clinical_benchmark.py --domain threadmed_qa --max-tasks 10
```

## 📁 Expected File Structure

After conversion:
```
data/processed/medical_dialogues/threadmed_qa/
├── tasks.json              # All 2,437 tasks
├── tasks_train.json        # Training set (~1,950 tasks)
├── tasks_val.json          # Validation set (~244 tasks)
├── tasks_test.json         # Test set (~243 tasks)
├── db.json                 # Patient database
└── split_tasks.json        # Train/val/test IDs
```

## 🎭 Task Format Example

Each converted task will include:
- **Multi-turn dialogue**: Patient questions and physician responses
- **Evaluation criteria**: Clinical accuracy, safety, empathy
- **Metadata**: Thread ID, number of turns, platform info

```json
{
  "id": "threadmed_001",
  "description": {
    "purpose": "Multi-turn medical consultation from Reddit r/AskDocs",
    "notes": "Real patient-physician dialogue with 3 turns"
  },
  "user_scenario": {
    "instructions": {
      "task_instructions": "Full dialogue transcript..."
    }
  },
  "evaluation_criteria": {
    "actions": [...],
    "communication_checks": [...]
  },
  "metadata": {
    "source": "ThReadMed-QA",
    "num_turns": 3
  }
}
```

## 📈 Expected Results

Based on the paper's evaluation of 5 frontier LLMs:
- **GPT-5**: 41.2% fully correct responses
- **GPT-4o**: ~35% fully correct
- **Claude Haiku**: ~30% fully correct
- All models degrade significantly from turn 0 to turn 2
- Wrong-answer rate triples by the third turn

## 🚦 Current Status

- [x] Dataset research completed
- [x] Conversion script created
- [ ] Dataset downloaded (pending - network issue)
- [ ] Conversion executed
- [ ] Results validated
- [ ] Committed to Git

## 💡 Next Steps

1. **Download dataset** when network is stable
2. **Run conversion** script
3. **Validate output** format
4. **Run benchmark** evaluation
5. **Compare results** with MedXpertQA
6. **Document findings**

## 📚 Resources

- **Paper**: [arXiv:2603.11281](https://arxiv.org/html/2603.11281v1)
- **GitHub**: [ThReadMed-QA Repository](https://github.com/monicamunnangi/ThReadMed-QA)
- **Conversion Script**: `convert_threadmed_qa.py`
- **Original README**: `data/raw/medical_dialogues/threadmed_qa/README.md`

## 🔬 Research Value

ThReadMed-QA provides:
1. **Ecologically valid** evaluation - real patient questions
2. **Multi-turn robustness** testing - measures degradation
3. **Clinical safety** assessment - error propagation tracking
4. **Comparable baseline** - 5 frontier LLMs evaluated

This makes it superior to:
- Exam-style datasets (unrealistic)
- Single-turn datasets (incomplete)
- Synthetic/adversarial datasets (not grounded)

---

**Created**: 2025-03-13
**Branch**: feature/medical-dialogue-datasets
**Status**: Ready for download and conversion
