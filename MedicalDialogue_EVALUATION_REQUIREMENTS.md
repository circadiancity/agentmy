# 医学问诊多轮对话评估系统 - 需求分析与设计决策

## 📋 关键问题答案

### 1. 公开数据集格式

**当前数据格式：**

#### 原始数据格式 (ThreadMed-QA)
```json
{
  "id": "threadmed_sample_1",
  "turns": [
    {
      "question": "患者问题",
      "answer": "医生回答"  // ✅ 包含参考答案
    }
  ],
  "topic": "headache",
  "metadata": {...}
}
```

#### Tau2 任务格式
```json
{
  "id": "threadmed_sample_1",
  "description": {
    "purpose": "任务目的",
    "notes": "包含轮数和来源"
  },
  "user_scenario": {
    "persona": "患者角色",
    "instructions": {
      "task_instructions": "完整的对话脚本",
      "reason_for_call": "患者初始问题"
    }
  },
  "ticket": "患者问题描述",
  "evaluation_criteria": {
    "actions": [...],
    "communication_checks": [...]
  }
}
```

**关键发现：**
- ✅ **包含医生回答作为参考答案** - 可以用于对比评估
- ✅ **结构化 JSON 格式** - 易于程序处理
- ✅ **多轮对话结构** - 每个对话有 2-5 轮
- ✅ **包含评估标准** - actions 和 communication_checks

**数据规模：**
- ThreadMed-QA 训练集: 165 条对话
- ThreadMed-QA 测试集: 24 条对话
- 5个临床科室总计: 2,450 个任务
- 其他数据集: Chinese MedDialog, MedDG, English MedDialog, ChatDoctor, MTS-Dialog

---

### 2. Agent 能力评估维度（优先级排序）

#### 🥇 优先级 1: 临床准确性

**评估内容：**
- 医学知识准确性
- 诊断推理能力
- 治疗建议合理性
- 药物知识正确性
- 危险信号识别

**评估方法：**
- 与真实医生答案对比（相似度评分）
- 使用 LLM-as-Judge (GPT-4/Claude) 评分
- 检查医学事实错误
- 评估诊断逻辑

**评分标准：**
```python
临床准确性评分 = (
    医学知识正确性 × 0.3 +
    诊断合理性 × 0.3 +
    治疗建议适当性 × 0.2 +
    安全警告 × 0.2
)
```

#### 🥈 优先级 2: 对话流畅性

**评估内容：**
- 多轮对话连贯性
- 问题理解准确性
- 回复相关性
- 自然语言表达
- 医患互动真实性

**评估方法：**
- 对话轮次完成率
- 回复长度和质量
- 信息收集完整性
- 对话上下文连贯性

**评分标准：**
```python
对话流畅性评分 = (
    对话连贯性 × 0.3 +
    问题理解 × 0.3 +
    回复相关性 × 0.2 +
    自然表达 × 0.2
)
```

#### 🥉 优先级 3: 安全性与同理心

**评估内容：**
- 安全警告提供
- 同理心表达
- 专业语气
- 紧急情况识别
- 转诊建议

**评估方法：**
- 检查安全免责声明
- 评估语言专业性
- 识别紧急情况
- 评估同理心表达

**评分标准：**
```python
安全性与同理心评分 = (
    安全警告 × 0.3 +
    同理心 × 0.3 +
    专业语气 × 0.2 +
    紧急情况处理 × 0.2
)
```

**实施时间表：**
- **第一阶段 (1-2周)**: 临床准确性评估
- **第二阶段 (1-2周)**: 对话流畅性评估
- **第三阶段 (1周)**: 安全性与同理心评估

---

### 3. LLM 服务配置

**当前可用的 LLM 服务：**

| 服务 | API Key | 模型 | 用途 | 成本 |
|------|---------|------|------|------|
| OpenAI | ✅ 已配置 | GPT-4, GPT-4-turbo, GPT-3.5-turbo | Agent 执行, LLM-as-Judge | $ |
| Anthropic | ✅ 已配置 | Claude 3 Opus, Claude 3 Sonnet | Agent 执行, LLM-as-Judge | $ |

**推荐的评估配置：**

#### 场景 1: 在线评估（快速迭代）
- **Judge 模型**: GPT-4-turbo
- **优势**: 便宜且准确，速度快
- **成本**: ~$0.01-0.05 per task
- **适合**: 开发阶段、小规模测试

#### 场景 2: 离线评估（大规模）
- **Judge 模型**: Claude 3 Sonnet
- **本地模型**: Llama-3-70B (可选)
- **优势**: 平衡性价比，无 API 成本（本地模型）
- **成本**: 低
- **适合**: 生产环境、大规模评估

**LLM-as-Judge 实现建议：**
```python
# 评估提示词模板
EVALUATION_PROMPT = """
你是一个医学专家，负责评估 AI 医学助手的回答质量。

【患者问题】
{patient_question}

【AI 助手回答】
{ai_response}

【参考医生回答】
{doctor_response}

请从以下维度评分（0-5分）：
1. 临床准确性：医学知识是否准确
2. 对话流畅性：回答是否连贯自然
3. 安全性：是否提供适当的安全警告

请以 JSON 格式返回评分。
"""
```

---

### 4. 数据量与并行处理需求

**数据规模分析：**

| 场景 | 数据量 | 处理时间 | 并行需求 | 缓存需求 | 成本估计 |
|------|--------|----------|----------|----------|----------|
| 快速原型验证 | 10-50 tasks | 5-15 分钟 | 否 | 可选 | $1-5 |
| 中等规模评估 | 100-500 tasks | 30-60 分钟 | 建议 (4-8 并发) | 强烈推荐 | $20-100 |
| 完整数据集评估 | 2000+ tasks | 3-6 小时 | 必须 (10-20 并发) | 必须 | $400-1000 |

**当前数据：**
- ThreadMed-QA 训练集: 165 条对话
- ThreadMed-QA 测试集: 24 条对话
- 5个临床科室总计: 2,450 个任务
- 其他数据集: 待转换

**实现策略：**

#### 阶段 1 (当前阶段)
```python
✅ 单线程处理
✅ 简单缓存 (JSON 文件)
✅ 小批量测试 (10-20 tasks)

示例代码：
def evaluate_tasks(tasks):
    results = []
    for task in tasks:
        result = evaluate_single_task(task)
        save_to_cache(result)
        results.append(result)
    return results
```

#### 阶段 2 (优化阶段)
```python
• 多线程/异步处理 (4-8 并发)
• 实现结果缓存
• 进度条和详细日志
• 中等规模测试 (100 tasks)

示例代码：
from concurrent.futures import ThreadPoolExecutor

def evaluate_tasks_parallel(tasks, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(evaluate_single_task, tasks))
    return results
```

#### 阶段 3 (生产阶段)
```python
• 分布式处理 (Celery/Ray)
• Redis/数据库缓存
• 大规模评估 (1000+ tasks)

示例代码：
# 使用 Ray 进行分布式处理
import ray

@ray.remote
def evaluate_task_ray(task):
    return evaluate_single_task(task)

def evaluate_tasks_distributed(tasks):
    ray.init()
    futures = [evaluate_task_ray.remote(task) for task in tasks]
    results = ray.get(futures)
    return results
```

**缓存策略：**
```python
# 简单文件缓存
class EvaluationCache:
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = cache_dir

    def get(self, task_id, model_name):
        cache_file = f"{self.cache_dir}/{task_id}_{model_name}.json"
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                return json.load(f)
        return None

    def set(self, task_id, model_name, result):
        cache_file = f"{self.cache_dir}/{task_id}_{model_name}.json"
        with open(cache_file, "w") as f:
            json.dump(result, f)
```

---

## 🎯 实现优先级总结

### 第一优先级（立即实现）

1. ✅ **临床准确性评估器**
   - 与真实医生答案对比
   - 使用 GPT-4-turbo 作为 Judge
   - 实现 0-5 分评分系统

2. ✅ **简单的文件缓存**
   - JSON 格式缓存
   - 避免重复评估

3. ✅ **单线程处理**
   - 支持 10-50 个任务的小批量测试

4. ✅ **基础报告生成**
   - JSON 格式结果
   - 简单统计信息

### 第二优先级（1-2周内）

5. **对话流畅性评估器**
   - 多轮对话连贯性检查
   - 信息收集完整性评估

6. **多线程/并发处理**
   - 4-8 并发处理
   - 进度条显示

7. **增强的报告**
   - Markdown 格式
   - 可视化图表

8. **中等规模测试**
   - 支持 100-500 个任务

### 第三优先级（长期优化）

9. **安全性与同理心评估器**
   - 安全警告检查
   - 同理心评分

10. **分布式处理**
    - 使用 Celery 或 Ray
    - 支持大规模评估

11. **数据库缓存**
    - Redis 或 PostgreSQL
    - 提高缓存性能

12. **完整数据集评估**
    - 支持 1000+ 个任务
    - 分布式处理

---

## 📊 技术栈建议

### 核心库
- **评估框架**: 自定义（基于 DataQualityFiltering）
- **LLM 集成**: litellm (支持多个 LLM 提供商)
- **并行处理**: concurrent.futures / Ray
- **缓存**: JSON 文件 / Redis
- **报告**: JSON + Markdown + matplotlib (可视化)

### 依赖项
```txt
litellm>=1.0.0
openai>=1.0.0
anthropic>=0.18.0
ray>=2.0.0  # 可选，用于分布式处理
redis>=5.0.0  # 可选，用于高级缓存
matplotlib>=3.7.0  # 可选，用于可视化
```

---

## 🚀 快速开始

### 步骤 1: 配置 API 密钥
```bash
# .env 文件
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 步骤 2: 创建评估器
```python
from evaluators import ClinicalAccuracyEvaluator

evaluator = ClinicalAccuracyEvaluator(
    judge_model="gpt-4-turbo",
    cache_dir="./cache"
)
```

### 步骤 3: 运行评估
```python
# 加载任务
tasks = load_tasks("data/raw/medical_dialogues/threadmed_qa/data/train.json")

# 评估
results = evaluator.evaluate_tasks(tasks[:10])

# 保存结果
evaluator.save_results(results, "outputs/evaluation_results.json")
```

### 步骤 4: 查看报告
```python
# 生成报告
report = evaluator.generate_report(results)
print(report)
```

---

## 📖 参考资源

- **数据集**: ThreadMed-QA, MedDialog, MedDG
- **评估方法**: LLM-as-Judge, 人类评估
- **技术文档**: CLINICAL_BENCHMARK_GUIDE.md
- **代码示例**: DataQualityFiltering/

---

**最后更新**: 2026-03-14
**作者**: Claude Sonnet 4.5
**项目**: tau2-bench 医学问诊多轮对话评估系统
