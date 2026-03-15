# DataQualityFiltering - 统一的医学评估框架

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/circadiancity/agentmy)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**DataQualityFiltering** 是一个统一的医学评估框架，提供两个互补的子系统：

1. **数据质量评估** (`data_quality`) - 验证和过滤医学对话数据
2. **Agent 性能评估** (`agent_evaluation`) - 评估 Agent 在医学任务上的表现

## 🎯 核心特性

- ✅ **统一的架构** - 两个子系统共享核心基础设施
- ✅ **模块化设计** - 清晰的职责分离，易于扩展
- ✅ **多 LLM 支持** - OpenAI GPT、Anthropic Claude、本地模型
- ✅ **多线程处理** - 高效的批量评估能力
- ✅ **灵活配置** - 支持从文件、环境变量、命令行加载配置
- ✅ **向后兼容** - 保持旧版本的 API 兼容性

## 📁 目录结构

```
DataQualityFiltering/
├── core/                    # 🔧 核心基础设施
│   ├── llm_evaluator.py    # LLM 评估器基类
│   ├── evaluator_base.py   # 评估器抽象接口
│   ├── reviewer_base.py    # 审查器抽象接口
│   └── config.py           # 配置管理
│
├── data_quality/            # 📊 数据质量评估
│   ├── pipeline.py         # 数据质量管道
│   ├── filter_engine.py    # 过滤引擎
│   ├── validators/         # 数据验证器
│   └── reviewers/          # 数据审查器
│
├── agent_evaluation/        # 🤖 Agent 性能评估
│   ├── pipeline.py         # Agent 评估管道
│   ├── evaluators/         # 三维度评估器
│   └── reviewers/          # Agent 综合审查器
│
└── utils/                   # 🛠️ 工具模块
```

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/circadiancity/agentmy.git
cd agentmy/DataQualityFiltering

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
# OpenAI API
export OPENAI_API_KEY="your_openai_api_key"

# Anthropic API（可选）
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# 本地 LLM URL（可选）
export LOCAL_LLM_URL="http://localhost:8000"
```

## 📊 数据质量评估

验证和过滤医学对话数据，确保数据质量。

### 使用示例

```python
from DataQualityFiltering.data_quality import DataQualityPipeline, FilterConfig

# 创建配置
config = FilterConfig(
    review_mode="semi_auto",
    min_quality_score=3.5,
)

# 创建管道
pipeline = DataQualityPipeline(config)

# 运行评估
with open("tasks.json", "r") as f:
    tasks = json.load(f)

results = pipeline.run(tasks)

print(f"通过: {len(results['accepted'])}")
print(f"拒绝: {len(results['rejected'])}")
```

### CLI 使用

```bash
# 检查医学对话
python -m DataQualityFiltering data-quality check --input data.json

# 过滤低质量数据
python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

# 运行完整管道
python -m DataQualityFiltering data-quality pipeline --input data.json --mode semi_auto
```

详见：[数据质量评估文档](data_quality/README.md)

## 🤖 Agent 性能评估

评估 Agent 在医学任务上的表现，包括临床准确性、对话流畅性和安全性。

### 使用示例

```python
from DataQualityFiltering.agent_evaluation import AgentEvaluationPipeline

# 创建管道
pipeline = AgentEvaluationPipeline(
    model="gpt-4-turbo",
    max_workers=4,
    pass_threshold=3.5,
)

# 评估 Agent 回答
results = pipeline.evaluate_from_file(
    input_file="agent_results.json",
    output_file="evaluation_results.json",
)

print(f"通过率: {results['statistics']['pass_rate']}%")
```

### CLI 使用

```bash
# 评估单个任务
python -m DataQualityFiltering agent-eval evaluate --input task.json

# 批量评估
python -m DataQualityFiltering agent-eval batch --input tasks.json --max-workers 8

# 生成报告
python -m DataQualityFiltering agent-eval report --input results.json --output report.md
```

详见：[Agent 性能评估文档](agent_evaluation/README.md)

## 🔧 高级用法

### 自定义评估器

```python
from DataQualityFiltering.core import DimensionEvaluator

class MyCustomEvaluator(DimensionEvaluator):
    def __init__(self):
        super().__init__(
            name="custom_evaluator",
            dimension_name="custom_dimension",
            weight=1.0,
        )

    def evaluate_dimension(self, data):
        # 实现自定义评估逻辑
        score = self._calculate_score(data)
        return {
            "score": score,
            "strengths": ["优点1"],
            "weaknesses": ["不足1"],
        }
```

### 自定义审查器

```python
from DataQualityFiltering.core import EvaluatorBasedReviewer

reviewer = EvaluatorBasedReviewer(
    name="custom_reviewer",
    evaluators=[
        ClinicalAccuracyEvaluator(),
        DialogueFluencyEvaluator(),
        MyCustomEvaluator(),
    ],
    weights={
        "clinical_accuracy": 0.40,
        "dialogue_fluency": 0.35,
        "custom_dimension": 0.25,
    },
    pass_threshold=3.5,
)

result = reviewer.review(patient_question="...", ai_response="...")
```

## 📝 API 参考

### 核心组件

#### LLM 评估器

```python
from DataQualityFiltering.core import create_llm_evaluator

# 创建评估器
evaluator = create_llm_evaluator("gpt-4-turbo")

# 评估
result = evaluator.evaluate("请评估以下内容...")
```

#### 配置管理

```python
from DataQualityFiltering.core import PipelineConfig, ConfigManager

# 从文件加载
config = ConfigManager().load_config("config.json")

# 或手动创建
config = PipelineConfig(
    llm=LLMConfig(model="gpt-4-turbo"),
    evaluation=EvaluationConfig(pass_threshold=3.5),
)
```

## 🔄 从 v1.x 迁移

如果您正在使用 v1.x 版本，迁移到 v2.0 非常简单：

```python
# v1.x（仍然可用）
from DataQualityFiltering import DataQualityPipeline

# v2.0（推荐）
from DataQualityFiltering.data_quality import DataQualityPipeline
```

所有旧的导入路径仍然可用，无需修改现有代码。

## 🤝 贡献

我们欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

- GitHub: [circadiancity/agentmy](https://github.com/circadiancity/agentmy)
- Issues: [GitHub Issues](https://github.com/circadiancity/agentmy/issues)

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

**版本**: 2.0.0
**更新日期**: 2025-03-15
