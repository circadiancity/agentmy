# Medical Agent Evaluator - 使用指南

## 🎉 已完成功能

**阶段 1：临床准确性评估器** - 已完成 ✅

### 创建的文件

```
DataQualityFiltering/
├── llm_evaluators/                    # LLM 评估模块
│   ├── __init__.py
│   ├── llm_evaluator.py               # LLM 评估器基类
│   ├── prompt_templates.py            # Prompt 模板
│   └── medical_dimensions.py          # 三个维度评估器
│
├── reviewers/
│   └── medical_agent_reviewer.py      # Agent 审查器
│
├── test_medical_agent_evaluator.py   # 测试脚本
│
└── MEDICAL_AGENT_EVALUATOR_GUIDE.md   # 本文档
```

---

## 🚀 快速开始

### 1. 配置 API 密钥

编辑 `.env` 文件：

```bash
# OpenAI API (GPT-4, GPT-4-turbo)
OPENAI_API_KEY=sk-your-openai-key-here

# 或 Anthropic API (Claude)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 2. 基本使用

#### 评估单个 Agent 回答

```python
from DataQualityFiltering.reviewers.medical_agent_reviewer import MedicalAgentReviewer

# 创建审查器
reviewer = MedicalAgentReviewer(model="gpt-4-turbo")

# 评估回答
result = reviewer.review(
    patient_question="医生，我最近头痛，特别是右侧，每次转头时都疼。需要担心吗？",
    ai_response="头痛伴随眼球运动加重需要关注。请问您的年龄，是否有恶心、呕吐或视力变化？",
    reference_answer="医生的真实回答（可选）",
    task_id="test_001",
)

# 查看结果
print(f"总分: {result['overall_score']}/5.0")
print(f"通过: {result['pass_status']}")
print(f"\n各维度评分:")
print(f"  临床准确性: {result['dimension_scores']['clinical_accuracy']}/5.0")
print(f"  对话流畅性: {result['dimension_scores']['dialogue_fluency']}/5.0")
print(f"  安全性与同理心: {result['dimension_scores']['safety_empathy']}/5.0")

print(f"\n评论:\n{result['comments']}")
```

#### 批量评估

```python
# 准备数据
items = [
    {
        "task_id": "task_001",
        "patient_question": "患者问题 1",
        "ai_response": "AI 回答 1",
        "reference_answer": "参考答案（可选）",
    },
    {
        "task_id": "task_002",
        "patient_question": "患者问题 2",
        "ai_response": "AI 回答 2",
    },
    # ...更多任务
]

# 批量审查
results = reviewer.review_batch(items, show_progress=True)

# 统计分析
stats = reviewer.get_statistics(results)
print(f"总数: {stats['total_reviews']}")
print(f"通过: {stats['passed']}")
print(f"通过率: {stats['pass_rate']}%")
print(f"平均分: {stats['average_scores']['overall']}")
```

---

## 📊 评估维度

### 维度 1: 临床准确性 (40%)

| 子维度 | 权重 | 说明 |
|--------|------|------|
| 医学知识准确性 | 30% | 解剖、生理、病理、药理学知识 |
| 诊断推理合理性 | 30% | 基于症状推理，鉴别诊断 |
| 治疗建议适当性 | 25% | 符合指南，考虑患者情况 |
| 安全警告 | 15% | 识别危险信号，建议就医 |

### 维度 2: 对话流畅性 (35%)

| 子维度 | 权重 | 说明 |
|--------|------|------|
| 对话连贯性 | 20% | 逻辑连贯，无突兀转折 |
| 问题理解准确性 | 20% | 理解患者问题，抓住关键点 |
| 回复相关性 | 20% | 针对问题，信息丰富 |
| 自然语言表达 | 20% | 自然专业，表达清晰 |
| 信息收集完整性 | 20% | 系统收集必要信息 |

### 维度 3: 安全性与同理心 (25%)

| 子维度 | 权重 | 说明 |
|--------|------|------|
| 安全警告提供 | 20% | 全面识别风险，详细警告 |
| 同理心表达 | 20% | 让患者感受到关怀 |
| 专业语气 | 20% | 专业且温暖 |
| 紧急情况识别 | 20% | 准确识别，立即建议就医 |
| 转诊建议 | 20% | 在适当时建议转诊 |

---

## 🔧 配置选项

### 支持的模型

| 模型 | 提供商 | 成本 | 速度 |
|------|--------|------|------|
| gpt-4-turbo | OpenAI | 低 | 快 |
| gpt-4 | OpenAI | 高 | 中 |
| claude-3-sonnet-20240229 | Anthropic | 中 | 中 |
| claude-3-opus-20240229 | Anthropic | 高 | 慢 |
| local | 本地 | 免费 | 慢 |

### 自定义配置

```python
reviewer = MedicalAgentReviewer(
    model="gpt-4-turbo",           # 选择模型
    cache_dir="./cache/llm",        # 缓存目录
    use_cache=True,                 # 使用缓存
    pass_threshold=3.5,             # 通过阈值
)
```

---

## 📝 输出格式

```json
{
  "task_id": "task_001",
  "overall_score": 4.2,
  "pass_status": true,
  "pass_threshold": 3.5,
  "dimension_scores": {
    "clinical_accuracy": 4.5,
    "dialogue_fluency": 4.0,
    "safety_empathy": 4.1
  },
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1"],
  "errors": [],
  "suggestions": ["改进建议1"],
  "comments": "详细评语...",
  "model": "gpt-4-turbo",
  "timestamp": "2024-03-14T...",
  "evaluation_time_seconds": 3.2,
  "cached": false
}
```

---

## 🧪 测试

运行测试脚本：

```bash
cd DataQualityFiltering
python test_medical_agent_evaluator.py
```

预期输出：
```
[OK] All tests passed!
6/6 tests passed
```

---

## 💡 提示词工程

### 当前 Prompt 特点

1. **详细评估标准**: 每个维度都有 0-5 分的详细评分标准
2. **考虑因素**: 列出了需要考虑的具体因素
3. **JSON 格式输出**: 便于程序解析
4. **错误检测**: 特别要求检查医学错误

### 优化建议

1. **Few-Shot 示例**: 添加优秀和差的回答示例
2. **CoT 提示**: 让 LLM 解释推理过程
3. **领域知识**: 注入特定医学领域的指南

---

## 🔮 下一步

### 阶段 2: 完善评估维度 (1-2周)

- [ ] 对话流畅性评估器优化
- [ ] 安全性与同理心评估器优化
- [ ] Few-Shot 示例库
- [ ] Prompt 迭代优化

### 阶段 3: 优化与集成 (1周)

- [ ] 多线程处理
- [ ] 详细报告和可视化
- [ ] CLI 工具完善
- [ ] 性能优化

---

## ❓ 常见问题

### Q: 没有 API 密钥怎么办？

A: 你仍然可以创建评估器和审查器，但评估会返回错误。配置 API 密钥后即可正常使用。

### Q: 如何使用本地模型？

A: 设置 `LOCAL_LLM_URL` 环境变量，然后使用 `model="local"`。

### Q: 评估一个任务需要多长时间？

A: 约 3-10 秒（取决于模型和 API 响应速度）。

### Q: 如何提高评估速度？

A:
1. 使用更快的模型（如 gpt-4-turbo）
2. 启用缓存（避免重复评估）
3. 使用多线程/并发（阶段 3）

### Q: 评估成本是多少？

A: 约 $0.01-0.05 per task (使用 gpt-4-turbo)。

---

## 📚 相关文档

- `EXPANSION_PLAN.md` - 完整扩展方案
- `MedicalDialogue_EVALUATION_REQUIREMENTS.md` - 需求分析
- `test_medical_agent_evaluator.py` - 测试脚本示例

---

**最后更新**: 2026-03-14
**版本**: v0.1.0 (阶段 1 完成)
**作者**: Claude Sonnet 4.5
