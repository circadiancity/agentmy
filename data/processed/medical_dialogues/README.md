# Medical Dialogue Datasets - Processed (tau2-bench Format)

This directory contains medical dialogue datasets that have been converted to tau2-bench format.

## 📁 Directory Structure

Each subdirectory contains tau2-bench compatible task sets:

```
<dataset_name>/
├── tasks.json          # Tau2 task objects
├── db.json             # Clinical database
├── tools.json          # Tool definitions
├── policy.md           # Clinical policy
└── split_tasks.json    # Train/val/test splits
```

## 📊 Dataset Status

| Dataset | Status | Tasks | Departments |
|---------|--------|-------|-------------|
| `chinese_meddialog/` | ⏳ Pending | - | - |
| `meddg/` | ⏳ Pending | - | Gastroenterology |
| `english_meddialog/` | ⏳ Pending | - | - |
| `chatdoctor/` | ⏳ Pending | - | - |
| `mts_dialog/` | ⏳ Pending | - | - |

## 🔄 Conversion Scripts

See conversion scripts in the project root:
- `convert_chinese_meddialog.py` - Convert Chinese MedDialog
- `convert_meddg.py` - Convert MedDG dataset
- `convert_english_meddialog.py` - Convert English MedDialog
- `convert_chatdoctor.py` - Convert ChatDoctor dataset
- `convert_mts_dialog.py` - Convert MTS-Dialog

## 📝 Usage

```bash
# After conversion, run evaluations:
python run_clinical_benchmark.py --domain chinese_meddialog --max-tasks 10
```

## 🆚 Comparison: Real vs Synthetic

| Dataset | Type | Authenticity |
|---------|------|--------------|
| Chinese MedDialog | Real dialogue | ✅ Authentic |
| MedDG | Real dialogue | ✅ Authentic |
| English MedDialog | Real dialogue | ✅ Authentic |
| ChatDoctor | Real dialogue | ✅ Authentic |
| MTS-Dialog | Real dialogue | ✅ Authentic |
| MedXpertQA (existing) | Synthetic from MCQ | ⚠️ Simulated |

## 📊 Quality Metrics

After conversion, each dataset will be evaluated on:
- Clinical accuracy
- Dialogue naturalness
- Evaluation completeness
- Difficulty appropriateness

See `CLINICAL_BENCHMARK_GUIDE.md` for evaluation details.
