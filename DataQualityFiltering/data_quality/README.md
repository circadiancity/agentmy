# 数据质量评估子系统

验证和过滤医学对话数据，确保数据质量符合要求。

## 功能概述

- ✅ **数据验证** - 检查数据结构和格式
- ✅ **质量评分** - 多维度评估数据质量
- ✅ **智能过滤** - 根据阈值过滤低质量数据
- ✅ **人工审查** - 支持人工审核机制
- ✅ **LLM 审查** - 自动化质量审查
- ✅ **校准机制** - 人工和自动审查结果校准

## 使用方法

### Python API

```python
from DataQualityFiltering.data_quality import (
    DataQualityPipeline,
    FilterConfig,
    MedicalDialogueValidator,
)
import json

# 方式1: 使用完整管道
config = FilterConfig(
    review_mode="semi_auto",  # human, semi_auto, both
    min_quality_score=3.5,
    llm_model="gpt-4o-mini",
)

pipeline = DataQualityPipeline(config)

with open("tasks.json", "r") as f:
    tasks = json.load(f)

results = pipeline.run(tasks)

# 方式2: 使用验证器
validator = MedicalDialogueValidator()
is_valid, errors = validator.validate(task)

# 方式3: 使用过滤器
from DataQualityFiltering.data_quality import QualityFilter

filter_engine = QualityFilter(config)
score = filter_engine.calculate_quality_score(task)
```

### CLI 工具

#### 检查医学对话

```bash
python -m DataQualityFiltering data-quality check \
    --input data.json \
    --output report.md
```

#### 过滤低质量数据

```bash
python -m DataQualityFiltering data-quality filter \
    --input data.json \
    --threshold 3.5 \
    --output filtered.json
```

#### 运行完整管道

```bash
python -m DataQualityFiltering data-quality pipeline \
    --input tasks.json \
    --mode semi_auto \
    --threshold 3.5 \
    --output-dir ./outputs
```

## 评估维度

### 1. 工具使用 (60% 权重)

评估任务中工具使用的数量和合理性

- **优秀**: 5-6 个工具，使用合理
- **良好**: 4-5 个工具，使用较合理
- **及格**: 2-3 个工具，基本合理
- **不及格**: 0-1 个工具，或使用不当

### 2. 内容质量 (40% 权重)

评估任务内容的完整性和质量

- **优秀**: 内容丰富，结构完整 (>400 字符)
- **良好**: 内容充实，结构较好 (>300 字符)
- **及格**: 内容基本完整 (>200 字符)
- **不及格**: 内容简短或缺失

## 验证器

### MedicalDialogueValidator

验证医学对话数据是否符合要求：

```python
from DataQualityFiltering.data_quality import MedicalDialogueValidator

validator = MedicalDialogueValidator()
result = validator.validate(task)

if result.is_valid:
    print("✅ 数据有效")
else:
    print(f"❌ 数据无效: {result.errors}")
```

验证项包括：
- ✅ 必填字段检查
- ✅ 对话结构验证
- ✅ 医学关键词检测
- ✅ 咨询模式识别
- ✅ 对话标记验证

### SchemaValidator

验证数据结构是否符合 JSON Schema：

```python
from DataQualityFiltering.data_quality import SchemaValidator

validator = SchemaValidator(schema_path="schema.json")
result = validator.validate(task)
```

## 审查模式

### Human 模式

纯人工审查，适合小规模高质量数据集：

```python
config = FilterConfig(
    review_mode="human",
    min_quality_score=4.0,
)
```

### Semi-Auto 模式

LLM 自动审查，适合大规模数据处理：

```python
config = FilterConfig(
    review_mode="semi_auto",
    llm_model="gpt-4o-mini",
    min_quality_score=3.5,
)
```

### Both 模式

人工 + LLM 联合审查，包含校准机制：

```python
config = FilterConfig(
    review_mode="both",
    min_calibration_tasks=3,
    min_calibration_r=0.5,
)
```

## 配置选项

### FilterConfig

```python
from DataQualityFiltering.data_quality import FilterConfig

config = FilterConfig(
    # 质量阈值
    min_quality_score=3.5,

    # 工具数量范围
    min_tool_count=1,
    max_tool_count=8,

    # 内容长度
    min_content_length=50,

    # 权重配置
    tool_count_weight=0.6,
    content_length_weight=0.02,

    # 审查模式
    review_mode="semi_auto",
    llm_model="gpt-4o-mini",
)
```

## 输出格式

### 管道输出

```json
{
  "accepted": [
    {
      "task_id": "task_001",
      "quality_score": 4.2,
      "tool_count": 5,
      "content_length": 450,
      ...
    }
  ],
  "rejected": [
    {
      "task_id": "task_002",
      "quality_score": 2.8,
      "reason": "质量分数低于阈值"
    }
  ],
  "statistics": {
    "total": 100,
    "accepted": 85,
    "rejected": 15,
    "pass_rate": 85.0
  }
}
```

## 最佳实践

1. **数据准备**
   - 确保 JSON 格式正确
   - 包含所有必填字段
   - 使用 UTF-8 编码

2. **阈值设置**
   - 测试集: 3.5-4.0（严格）
   - 训练集: 3.0-3.5（中等）
   - 生产数据: 2.5-3.0（宽松）

3. **审查模式选择**
   - 小数据集 (<100): 使用 `human`
   - 中等数据集 (100-1000): 使用 `both`
   - 大数据集 (>1000): 使用 `semi_auto`

4. **性能优化**
   - 启用缓存减少 LLM 调用
   - 使用批处理提高吞吐量
   - 选择合适的 LLM 模型

## 故障排除

### 问题: 导入错误

```python
# 错误
from DataQualityFiltering import DataQualityPipeline

# 正确
from DataQualityFiltering.data_quality import DataQualityPipeline
```

### 问题: LLM API 调用失败

```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 或在代码中设置
import os
os.environ["OPENAI_API_KEY"] = "your_key"
```

### 问题: 验证失败

```python
# 查看详细错误信息
result = validator.validate(task)
print(result.errors)
print(result.warnings)
```

## 相关文档

- [主 README](../README.md)
- [Agent 评估文档](../agent_evaluation/README.md)
- [API 参考](../docs/api.md)

---

**版本**: 2.0.0
**更新日期**: 2025-03-15
