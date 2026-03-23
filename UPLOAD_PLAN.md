# 上传和转换计划
# Upload and Conversion Plan

## 第一步：上传生成器到GitHub

```bash
# 1. 添加生成器到git
git add MedicalDialogueTaskGenerator/
git add convert_dataset.py

# 2. 提交
git commit -m "feat: add Medical Dialogue Task Generator and dataset converter"

# 3. 推送到GitHub
git push my_github sync-quality-threshold-modules
```

## 第二步：批量转换所有数据集

### 1. chinese_internal_medicine (500个任务)
```bash
python convert_dataset.py \
  --input "data/tau2/domains/clinical/chinese_internal_medicine/tasks.json" \
  --output "data/tau2/domains/clinical/chinese_internal_medicine/tasks_advanced.json"
```

### 2. 其他数据集 (按优先级)
- chinese_pediatrics (儿科)
- chinese_surgery (外科)
- chinese_obstetrics_gynecology (妇产科)
- chinese_oncology (肿瘤科)
- cardiology (心脏病学)
- endocrinology (内分泌学)

## 第三步：创建对比报告

生成转换前后的对比报告，展示增强功能。

## 第四步：更新文档

在GitHub README中添加新功能的说明。

## 文件清单

### 需要上传的文件：
1. MedicalDialogueTaskGenerator/ (完整目录)
2. convert_dataset.py (转换脚本)
3. UPLOAD_PLAN.md (本文件)

### 转换后的文件：
1. chinese_internal_medicine/tasks_advanced.json
2. 其他科室的tasks_advanced.json
