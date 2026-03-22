# PrimeKG Random Walk - 快速开始

## 🚀 5 分钟快速开始

### 前提条件

本地已有 PrimeKG 数据（约 1.1 GB）：
```bash
# 检查数据是否存在
ls -lh data/primekg_cache/

# 如果不存在，首次运行会自动下载（需要 30-40 分钟）
```

### 1. 生成 PrimeKG 任务

```bash
# 方式 1: 使用测试脚本（推荐）
python test_primekg_random_walk.py

# 这将生成 6-7 个示例任务，保存在 data/primekg_tasks/
```

### 2. 转换为 tau2 格式

```bash
# 转换 PrimeKG 任务为 tau2 格式
python primekg_to_tau2.py

# 输出：
# - data/tau2/domains/clinical/primekg/tasks.json
# - data/tau2/domains/clinical/primekg/split_tasks.json
# - data/tau2/domains/clinical/primekg/db.json
```

### 3. 在评估框架中使用

```python
# 使用生成的 tau2 任务
import json

# 加载任务
with open('data/tau2/domains/clinical/primekg/tasks.json', 'r') as f:
    tasks = json.load(f)

# 查看第一个任务
task = tasks[0]
print(f"任务 ID: {task['id']}")
print(f"主诉: {task['ticket']}")
print(f"对话轮次: {len(task['reference_dialogue'])}")

# 可以直接用于评估
# from evaluation import evaluate_task
# evaluate_task(task)
```

---

## 📊 生成的数据

### 任务统计

- **总任务数**: 6 个（可扩展到数百个）
- **症状类型**: pain, fever, hypertension
- **平均路径长度**: 2.5 节点
- **平均对话轮次**: 5.5 轮

### 数据结构

```json
{
  "id": "primekg_fever_medium",
  "user_scenario": {
    "persona": "60-year-old female patient",
    "instructions": {
      "domain": "primekg_internal_medicine",
      "reason_for_call": "Periodic fever",
      "known_info": "Patient has fever for 22 days",
      "unknown_info": "cyclic hematopoiesis"
    }
  },
  "reference_dialogue": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

---

## 🔧 自定义生成

### 生成更多任务

```python
from primekg_random_walk import PrimeKGRandomWalkPipeline

# 初始化（使用缓存，20秒加载）
pipeline = PrimeKGRandomWalkPipeline(use_cache=True)

# 搜索症状
symptoms = pipeline.real_kg.search_nodes("pain", limit=10)
print(f"找到 {len(symptoms)} 个症状")

# 批量生成
for i, symptom in enumerate(symptoms[:5]):
    task = pipeline.generate_consultation_task(
        symptom_keyword=symptom['name'],
        walk_type="medium"
    )
    print(f"{i+1}. {symptom['name']} → {task.patient_profile.get('underlying_condition')}")

    # 保存任务
    pipeline.export_to_tau2(
        task,
        f"data/primekg_tasks/task_{i}.json"
    )
```

### 使用不同症状

```python
# 可用的症状关键词
symptom_keywords = [
    "pain",           # 疼痛
    "fever",          # 发热
    "nausea",         # 恶心
    "hypertension",   # 高血压
    "diabetes",       # 糖尿病
    "infection",      # 感染
    "inflammation",   # 炎症
    "edema",          # 水肿
]

for keyword in symptom_keywords:
    try:
        task = pipeline.generate_consultation_task(keyword)
        print(f"✓ {keyword}: {task.patient_profile['chief_complaint']}")
    except Exception as e:
        print(f"✗ {keyword}: {e}")
```

---

## 📈 扩展数据集

### 批量生成（100+ 任务）

```python
import random
from pathlib import Path

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)

# 定义症状关键词列表
symptom_keywords = [
    "pain", "fever", "nausea", "hypertension", "diabetes",
    "headache", "cough", "fatigue", "weakness", "dizziness"
]

output_dir = Path("data/primekg_tasks/batch")
output_dir.mkdir(parents=True, exist_ok=True)

# 生成任务
task_count = 0
for keyword in symptom_keywords:
    for _ in range(10):  # 每个症状生成 10 个任务
        try:
            task = pipeline.generate_consultation_task(
                symptom_keyword=keyword,
                walk_type=random.choice(["short", "medium", "long"])
            )

            # 保存
            output_file = output_dir / f"{task.task_id}.json"
            pipeline.export_to_tau2(task, str(output_file))

            task_count += 1
            print(f"✓ [{task_count}] {task.task_id}")

        except Exception as e:
            continue

print(f"\n✓ 总共生成了 {task_count} 个任务")
```

---

## 🎯 集成到现有系统

### 与现有中文任务混合使用

```python
# 加载 PrimeKG 任务
with open('data/tau2/domains/clinical/primekg/tasks.json') as f:
    primekg_tasks = json.load(f)

# 加载现有中文任务
with open('data/tau2/domains/clinical/chinese_internal_medicine/tasks.json') as f:
    chinese_tasks = json.load(f)

# 合并
all_tasks = primekg_tasks + chinese_tasks

# 保存合并后的任务集
with open('data/tau2/domains/clinical/combined/tasks.json') as f:
    json.dump(all_tasks, f, ensure_ascii=False, indent=2)

print(f"总任务数: {len(all_tasks)}")
print(f"  - PrimeKG: {len(primekg_tasks)}")
print(f"  - 中文: {len(chinese_tasks)}")
```

---

## 🔍 验证数据质量

### 检查医学准确性

```python
from primekg_random_walk import PrimeKGRandomWalkPipeline

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)

# 验证诊断准确性
task_id = "primekg_fever_medium"
task_file = f"data/primekg_tasks/{task_id}.json"

# 读取任务
import json
with open(task_file) as f:
    data = json.load(f)

# 验证疾病
disease_name = data['patient_profile']['underlying_condition']
results = pipeline.real_kg.search_nodes(disease_name.split()[0], limit=5)

print(f"验证疾病: {disease_name}")
print(f"PrimeKG 中的匹配:")
for r in results:
    print(f"  - {r['name']}")

# 验证药物
if len(data['path']['nodes']) > 2:
    drug_id = data['path']['nodes'][2]
    drug_info = pipeline.real_kg.get_node_info(drug_id)

    if drug_info:
        print(f"\n验证药物: {drug_info['name']}")
        print(f"  类型: {drug_info['type']}")

        # 查询药物的适应症
        neighbors = pipeline.real_kg.get_neighbors(
            drug_id,
            edge_type="indication",
            direction="out"
        )

        print(f"  适应症数量: {len(neighbors)}")
```

---

## ❓ 常见问题

### Q1: 首次运行需要多长时间？

**A**:
- 下载 PrimeKG: ~10-20 分钟（936 MB）
- 解析和过滤: ~10-20 分钟
- 总计: ~20-40 分钟（首次）
- 后续使用: ~20 秒（使用缓存）

### Q2: 能否使用更小的数据集？

**A**: 可以，调整过滤参数：

```python
pipeline = PrimeKGRandomWalkPipeline(
    focus_types=["disease", "drug"],  # 只保留疾病和药物
    use_cache=True
)
```

### Q3: 如何生成中文任务？

**A**: 当前生成的是英文任务，中文适配需要额外开发。参见 `PRIMEKG_USAGE_GUIDE.md` 中的"方案 B: 中文适配"。

### Q4: 生成的任务可以直接用于评估吗？

**A**: 可以！任务已经是 tau2 格式，可以直接用于：

```bash
# 在评估框架中使用
python evaluation.py \
    --domain clinical \
    --subdomain primekg \
    --tasks data/tau2/domains/clinical/primekg/tasks.json
```

---

## 📚 更多资源

- **完整指南**: `PRIMEKG_USAGE_GUIDE.md`
- **技术文档**: `PRIMEKG_RANDOM_WALK_INTEGRATION.md`
- **API 文档**: `primekg_random_walk.py` (代码注释)
- **示例**: `test_primekg_random_walk.py`

---

**最后更新**: 2025-03-22
**状态**: ✅ 可直接使用
