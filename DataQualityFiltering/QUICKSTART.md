# DataQualityFiltering 快速开始指南

本指南将帮助您在 5 分钟内开始使用 DataQualityFiltering。

## 📋 前置要求

- Python 3.8+
- pip 包管理器
- OpenAI API 密钥（或其他 LLM API）

## 🚀 安装步骤

### 1. 安装依赖

```bash
pip install openai anthropic requests
```

### 2. 设置 API 密钥

```bash
# Linux/Mac
export OPENAI_API_KEY="your_openai_api_key"

# Windows (PowerShell)
$env:OPENAI_API_KEY="your_openai_api_key"

# Windows (CMD)
set OPENAI_API_KEY=your_openai_api_key
```

## 📊 数据质量评估 - 快速开始

### 步骤 1: 准备测试数据

创建 `test_data.json`:

```json
{
  "tasks": [
    {
      "task_id": "test_001",
      "instruction": "模拟医生问诊，收集患者信息",
      "environment": {
        "medical_dialogue": {
          "patient_question": "医生，我最近总是感觉疲劳，而且体重下降明显",
          "doctor_response": "您好！请问您的疲劳感持续多久了？体重下降了多少斤？有没有其他症状如发热、盗汗等？",
          "dialogue_type": "consultation"
        }
      },
      "tool_calls": [
        {"tool": "ask_symptom", "parameters": {"symptom": "fatigue"}},
        {"tool": "ask_duration", "parameters": {"duration": "2_weeks"}}
      ],
      "content": "患者主诉疲劳和体重下降，进行了症状询问和病史采集。"
    }
  ]
}
```

### 步骤 2: 运行数据质量检查

```bash
python -m DataQualityFiltering data-quality check \
    --input test_data.json \
    --output quality_report.md
```

### 步骤 3: 查看结果

```bash
cat quality_report.md
```

## 🤖 Agent 性能评估 - 快速开始

### 步骤 1: 使用示例数据

我们已经为您准备了示例数据：`examples/sample_agent_evaluation.json`

### 步骤 2: 运行 Agent 评估

```bash
python -m DataQualityFiltering agent-eval batch \
    --input examples/sample_agent_evaluation.json \
    --output evaluation_results.json \
    --max-workers 2
```

### 步骤 3: 查看评估结果

```python
import json

with open("evaluation_results.json", "r") as f:
    results = json.load(f)

# 查看统计信息
stats = results["statistics"]
print(f"总数: {stats['total_reviews']}")
print(f"通过: {stats['passed']}")
print(f"失败: {stats['failed']}")
print(f"通过率: {stats['pass_rate']}%")

# 查看详细结果
for result in results["results"]:
    print(f"\n任务: {result['task_id']}")
    print(f"总分: {result['overall_score']}")
    print(f"通过: {result['pass_status']}")
```

## 💻 Python API - 快速开始

### 数据质量评估

```python
from DataQualityFiltering.data_quality import (
    DataQualityPipeline,
    FilterConfig,
)
import json

# 创建配置
config = FilterConfig(
    review_mode="semi_auto",
    min_quality_score=3.5,
)

# 创建管道
pipeline = DataQualityPipeline(config)

# 加载数据
with open("test_data.json", "r") as f:
    tasks = json.load(f)["tasks"]

# 运行评估
results = pipeline.run(tasks)

print(f"✅ 通过: {len(results['accepted'])}")
print(f"❌ 拒绝: {len(results['rejected'])}")
```

### Agent 性能评估

```python
from DataQualityFiltering.agent_evaluation import MedicalAgentReviewer

# 创建审查器
reviewer = MedicalAgentReviewer(model="gpt-4-turbo")

# 评估单个任务
result = reviewer.review(
    patient_question="医生您好，我最近经常头痛...",
    ai_response="您好！感谢您的咨询。头痛可能由多种原因...",
    context_info="患者，女性，35岁",
)

print(f"总分: {result['overall_score']}/5.0")
print(f"通过: {result['pass_status']}")
print(f"\n各维度分数:")
print(f"  临床准确性: {result['dimension_scores']['clinical_accuracy']}")
print(f"  对话流畅性: {result['dimension_scores']['dialogue_fluency']}")
print(f"  安全性与同理心: {result['dimension_scores']['safety_empathy']}")
```

## 🔧 常见问题

### Q: 如何使用本地 LLM？

```python
from DataQualityFiltering.core import create_llm_evaluator

# 创建本地评估器
evaluator = create_llm_evaluator(
    model="local",
    base_url="http://localhost:8000",
)

# 或使用环境变量
import os
os.environ["LOCAL_LLM_URL"] = "http://localhost:8000"
```

### Q: 如何调整评估阈值？

```python
# 数据质量评估
config = FilterConfig(min_quality_score=4.0)  # 更严格

# Agent 评估
reviewer = MedicalAgentReviewer(pass_threshold=4.0)
```

### Q: 如何启用缓存？

```python
# 缓存默认启用
pipeline = AgentEvaluationPipeline(
    use_cache=True,
    cache_dir="./cache/llm",
)
```

### Q: 如何提高评估速度？

```python
# 增加并发数
pipeline = AgentEvaluationPipeline(
    max_workers=8,  # 默认 4
)

# 使用更快的模型
pipeline = AgentEvaluationPipeline(
    model="gpt-3.5-turbo",  # 比 gpt-4 快
)
```

## 📚 下一步

- 阅读详细文档：
  - [数据质量评估文档](data_quality/README.md)
  - [Agent 性能评估文档](agent_evaluation/README.md)
- 查看更多示例：
  - `examples/` 目录
- 自定义评估：
  - 创建自定义评估器
  - 调整评估权重
  - 配置评估维度

## 🆘 获取帮助

- GitHub Issues: [提交问题](https://github.com/circadiancity/agentmy/issues)
- 文档: [完整文档](README.md)
- 示例: [examples/](examples/)

---

**祝您使用愉快！** 🎉
