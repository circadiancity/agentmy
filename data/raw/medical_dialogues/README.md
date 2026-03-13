# Medical Dialogue Datasets - Raw Data

This directory contains raw medical dialogue datasets for conversion to tau2-bench format.

## 📁 Directory Structure

| Dataset | Description | Source | Size |
|---------|-------------|--------|------|
| `chinese_meddialog/` | Chinese medical dialogues (110万对话 / 400万轮次) | [阿里云天池](https://tianchi.aliyun.com/dataset/92110) | 110万+ |
| `meddg/` | Gastrointestinal disease consultations (12种常见胃肠病) | [arXiv](https://arxiv.org/abs/2010.07497) | 17,000+ |
| `english_meddialog/` | English medical dialogues | [Hugging Face](https://huggingface.co/datasets/UCSD26/medical_dialog) | 260,000 |
| `chatdoctor/` | Real doctor-patient interactions | [Kaggle](https://www.kaggle.com/datasets/punyaslokaprusty/chatdoctor) | 100,000 |
| `mts_dialog/` | Dialogues with summaries | [GitHub](https://github.com/abachaa/MTS-Dialog) | 1,700 |

## 📥 Download Instructions

### Chinese MedDialog
```bash
# Visit: https://tianchi.aliyun.com/dataset/92110
# Download and extract to data/raw/medical_dialogues/chinese_meddialog/
```

### MedDG
```bash
# Visit: https://arxiv.org/abs/2010.07497
# Follow paper instructions to obtain dataset
# Extract to data/raw/medical_dialogues/meddg/
```

### English MedDialog
```bash
# Using Hugging Face datasets library:
pip install datasets
python -c "from datasets import load_dataset; ds = load_dataset('UCSD26/medical_dialog'); ds.save_to_disk('data/raw/medical_dialogues/english_meddialog/')"
```

### ChatDoctor
```bash
# Visit: https://www.kaggle.com/datasets/punyaslokaprusty/chatdoctor
# Download and extract to data/raw/medical_dialogues/chatdoctor/
```

### MTS-Dialog
```bash
git clone https://github.com/abachaa/MTS-Dialog.git data/raw/medical_dialogues/mts_dialog/
```

## ⚠️ Important Notes

- **Do NOT commit large data files to Git** - These directories are gitignored
- Raw data files should be kept in `.gitignore`
- Only processed and converted data should be committed to the repository

## 🔄 Conversion Process

After downloading raw data, use the conversion scripts in `UniClinicalDataEngine/` to convert to tau2-bench format. Results will be stored in `data/processed/medical_dialogues/`.
