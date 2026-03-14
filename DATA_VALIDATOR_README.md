# Medical Dialogue Dataset Validator

## 概述

`data_validator.py` 是一个专门用于检测和验证医疗问诊多轮对话数据集的模块。它可以检查数据集是否符合 tau2-bench 格式标准，并提供详细的验证报告。

## 功能特性

### ✅ 自动检测

- **结构验证**: 检查必需的字段（id, description, user_scenario, ticket, evaluation_criteria）
- **医疗内容验证**: 检测是否包含医疗相关关键词和术语
- **多轮对话验证**: 识别是否包含真正的多轮对话结构
- **评估标准验证**: 确保有明确的评估标准

### 📊 三级验证

| 级别 | 说明 | 示例 |
|------|------|------|
| **ERROR** | 阻止数据集使用的严重问题 | 缺少必需字段 |
| **WARNING** | 应该解决但不影响使用的问题 | 缺少医疗关键词 |
| **INFO** | 信息提示 | 多轮对话较少 |

### 📈 统计信息

- 总任务数
- 多轮对话任务数
- 医疗相关任务数
- 评估动作数量
- 领域分布
- 票据长度统计

## 使用方法

### 1. 命令行使用

```bash
# 基本验证
python data_validator.py data/tau2/domains/clinical/threadmed_qa/tasks.json

# 严格模式（将警告视为错误）
python data_validator.py data/tau2/domains/clinical/threadmed_qa/tasks.json --strict

# 安静模式（只显示错误和警告）
python data_validator.py data/tau2/domains/clinical/threadmed_qa/tasks.json --quiet

# 保存结果为 JSON
python data_validator.py data/tau2/domains/clinical/threadmed_qa/tasks.json --json-output validation_result.json
```

### 2. Python API 使用

```python
from data_validator import MedicalDialogueValidator
from pathlib import Path

# 初始化验证器
validator = MedicalDialogueValidator(strict_mode=False)

# 验证数据集
dataset_path = Path("data/tau2/domains/clinical/threadmed_qa/tasks.json")
result = validator.validate_dataset(dataset_path)

# 检查是否有效
if result.is_valid:
    print("数据集验证通过！")
else:
    print("数据集存在问题：")
    for error in result.errors:
        print(f"  - {error}")

# 打印详细报告
result.print_report()

# 访问统计信息
print(f"总任务数: {result.total_tasks}")
print(f"多轮任务: {result.stats.get('multi_turn_tasks', 0)}")
print(f"领域分布: {result.stats.get('domain_distribution', {})}")
```

### 3. 批量验证

```bash
# 验证所有临床数据集
for domain in data/tau2/domains/clinical/*/tasks.json; do
    echo "Validating $domain"
    python data_validator.py "$domain" --json-output "${domain%.json}_validation.json"
done
```

## 验证规则详解

### 1. 结构验证

检查以下必需字段：

```json
{
  "id": "任务ID",
  "description": { "purpose": "目的描述" },
  "user_scenario": {
    "persona": "患者人设",
    "instructions": { "domain": "医疗领域" }
  },
  "ticket": "患者问题",
  "evaluation_criteria": { "actions": [...] }
}
```

### 2. 医疗内容验证

检测以下医疗关键词：

```
pain, fever, headache, nausea, vomiting, cough
doctor, physician, patient, symptom, diagnosis
treatment, medication, prescription, therapy
blood pressure, heart rate, temperature, examination
medical, clinical, health, disease, condition
```

### 3. 多轮对话验证

识别对话结构标记：

```
Patient: ...
Doctor: ...
Assistant: ...
User: ...
```

统计对话轮次，建议至少 4 轮对话。

### 4. 评估标准验证

检查评估标准是否包含：

- `actions`: 评估动作列表
- `communication_checks`: 沟通检查列表

## 验证报告示例

```
================================================================================
  MEDICAL CONSULTATION DIALOGUE DATASET VALIDATION REPORT
================================================================================

Overall Status: [VALID]
Total Tasks: 500
Issues Found: 1999
  - Errors: 0
  - Warnings: 500
  - Info: 1499

--------------------------------------------------------------------------------
  DATASET STATISTICS
--------------------------------------------------------------------------------
  multi_turn_tasks: 28
  safety_related_tasks: 12
  total_evaluation_actions: 531
  tasks_with_errors: 0
  tasks_with_warnings: 500
  avg_ticket_length: 73.416
  min_ticket_length: 13
  max_ticket_length: 155
  domain_distribution: {'internal_medicine': 500}

WARNINGs (500):
  [WARNING] medical: Ticket may not be medical-related (no medical keywords found) (Task: clinical_internal_medicine_0)
  Suggestion: Ensure content describes a health-related concern
  ...

================================================================================
```

## 测试验证器

运行测试套件：

```bash
python test_validator.py
```

测试包括：
1. ✅ 有效多轮医疗对话数据集
2. ❌ 缺少必需字段的数据集
3. ⚠️ 非医疗数据集
4. 🔀 混合质量数据集
5. 📊 真实 ThReadMed-QA 数据集
6. 📊 真实 Chinese MedDialog 数据集

## 验证结果解读

### ✅ 数据集有效

- 无 ERROR 级别问题
- 可以安全使用
- WARNING 和 INFO 可以根据需要处理

### ❌ 数据集无效

- 存在 ERROR 级别问题
- 需要修复后才能使用
- 查看具体错误信息和修复建议

### ⚠️ 有警告的数据集

- 结构基本正确
- 存在可以改进的地方
- 建议根据警告优化数据集

## 常见问题

### Q1: 为什么医疗关键词检测失败？

**A**: 可能原因：
- 使用了中文医学术语（需要添加到关键词列表）
- 术语过于专业或缩写
- 建议添加相关关键词到 `MEDICAL_KEYWORDS`

### Q2: 如何处理中文医疗对话？

**A**:
1. 添加中文医疗关键词到验证器
2. 调整 `CONSULTATION_PATTERNS` 以支持中文
3. 考虑创建专门的语言特定验证规则

### Q3: 多轮对话检测不准确？

**A**: 确保 `task_instructions` 中使用明确的对话标记：
```
Patient: ...
Physician: ...
```

### Q4: 如何自定义验证规则？

**A**: 继承 `MedicalDialogueValidator` 类并重写验证方法：

```python
class CustomValidator(MedicalDialogueValidator):
    def validate_task(self, task, idx):
        issues = super().validate_task(task, idx)
        # 添加自定义验证逻辑
        return issues
```

## 集成到数据流程

### 在数据转换后验证

```python
from data_validator import MedicalDialogueValidator

# 转换数据集
converter = ThReadMedQAConverter()
tasks = converter.convert_to_tau2(conversations)

# 保存前验证
validator = MedicalDialogueValidator()
result = validator.validate_dataset_from_tasks(tasks)

if result.is_valid:
    converter.save_tasks(tasks, output_dir)
else:
    print("数据集验证失败，请修复错误")
    for error in result.errors:
        print(f"  {error}")
```

### 在 CI/CD 中使用

```bash
# .github/workflows/validate_datasets.yml
name: Validate Datasets

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Clinical Datasets
        run: |
          for dataset in data/tau2/domains/clinical/*/tasks.json; do
            python data_validator.py "$dataset" --strict
          done
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `data_validator.py` | 主验证器模块 |
| `test_validator.py` | 测试套件 |
| `DATA_VALIDATOR_README.md` | 本文档 |

## 扩展和贡献

欢迎扩展验证器功能：

1. 添加新的验证规则
2. 支持更多语言
3. 改进错误消息和建议
4. 添加更多统计指标

## 许可证

与 tau2-bench 项目保持一致
