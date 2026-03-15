# DataQualityFiltering 重构方案

## 📋 重构目标

将 DataQualityFiltering 从单一的数据质量过滤工具升级为**统一的医学评估框架**，支持：

1. **数据质量评估** - 验证和过滤医学对话数据
2. **Agent 性能评估** - 评估 Agent 在医学任务上的表现

## 🏗️ 新的目录结构

```
DataQualityFiltering/
├── __init__.py
├── README.md                                # 总体说明文档
│
├── core/                                    # 核心基础设施（新增）
│   ├── __init__.py
│   ├── llm_evaluator.py                    # LLM 评估器基类
│   ├── evaluator_base.py                   # 评估器抽象基类
│   ├── reviewer_base.py                    # 审查器抽象基类
│   └── config.py                           # 配置管理
│
├── data_quality/                           # 数据质量评估子系统
│   ├── __init__.py
│   ├── pipeline.py                         # 数据质量过滤管道
│   ├── filter_engine.py                    # 过滤引擎
│   ├── calibration.py                      # 校准模块
│   ├── cli.py                              # 数据质量 CLI
│   │
│   ├── validators/                         # 数据验证器
│   │   ├── __init__.py
│   │   ├── base.py                         # 验证器基类
│   │   ├── schema_validator.py             # 结构验证器
│   │   ├── quality_validator.py            # 质量验证器
│   │   ├── department_validator.py         # 科室验证器
│   │   └── medical_dialogue_validator.py   # 医学对话验证器
│   │
│   └── reviewers/                          # 数据审查器
│       ├── __init__.py
│       ├── human_review.py                 # 人工审查
│       ├── llm_review.py                   # LLM 自动审查
│       └── medical_dialogue_reviewer.py    # 医学对话审查器
│
├── agent_evaluation/                       # Agent 性能评估子系统（新增）
│   ├── __init__.py
│   ├── README.md                           # Agent 评估说明文档
│   ├── pipeline.py                         # Agent 评估管道
│   ├── cli.py                              # Agent 评估 CLI
│   │
│   ├── evaluators/                         # 评估器
│   │   ├── __init__.py
│   │   ├── clinical_accuracy.py            # 临床准确性评估器
│   │   ├── dialogue_fluency.py             # 对话流畅性评估器
│   │   └── safety_empathy.py               # 安全性与同理心评估器
│   │
│   └── reviewers/                          # 审查器
│       ├── __init__.py
│       └── medical_agent_reviewer.py       # 医学 Agent 综合审查器
│
├── utils/                                  # 工具模块（新增）
│   ├── __init__.py
│   ├── prompt_templates.py                 # Prompt 模板
│   ├── cache.py                            # 缓存管理
│   └── statistics.py                       # 统计工具
│
└── examples/                               # 示例数据（新增）
    ├── sample_medical_dialogue.json        # 医学对话示例
    └── sample_agent_evaluation.json        # Agent 评估示例
```

## 🔧 重构步骤

### Phase 1: 创建核心基础设施 (Phase 1: Create Core Infrastructure)

**目标**: 提取共享的核心组件，为两个子系统提供统一的基础

1. **创建 `core/` 目录**
   - `core/llm_evaluator.py` - 从现有代码提取 LLM 评估器基类
   - `core/evaluator_base.py` - 定义统一的评估器接口
   - `core/reviewer_base.py` - 定义统一的审查器接口
   - `core/config.py` - 统一的配置管理

**优势**:
- 消除代码重复
- 提供一致的接口
- 便于未来扩展

### Phase 2: 重构数据质量评估子系统 (Phase 2: Refactor Data Quality Subsystem)

**目标**: 将现有代码重组到 `data_quality/` 目录，保持功能不变

1. **移动文件到 `data_quality/`**
   - `pipeline.py` → `data_quality/pipeline.py`
   - `filter_engine.py` → `data_quality/filter_engine.py`
   - `validators/` → `data_quality/validators/`
   - `reviewers/` → `data_quality/reviewers/`
   - `cli.py` → `data_quality/cli.py`
   - `check_medical_dialogue.py` → `data_quality/check_medical_dialogue.py`

2. **更新导入路径**
   - 所有导入语句更新为新的路径结构
   - 确保向后兼容（通过 `__init__.py` 重新导出）

**优势**:
- 清晰的职责分离
- 不影响现有功能
- 便于维护

### Phase 3: 集成 Agent 评估子系统 (Phase 3: Integrate Agent Evaluation Subsystem)

**目标**: 将新增的 Agent 评估代码集成到 `agent_evaluation/` 目录

1. **创建 `agent_evaluation/` 目录**
   - 将本地新代码移动到对应位置：
     - `llm_evaluators/` → `agent_evaluation/evaluators/`
     - `pipelines/agent_evaluation_pipeline.py` → `agent_evaluation/pipeline.py`
     - `reviewers/medical_agent_reviewer.py` → `agent_evaluation/reviewers/`
     - `evaluate_agent.py` → `agent_evaluation/cli.py`

2. **统一接口设计**
   - 确保 `AgentEvaluationPipeline` 实现统一的评估器接口
   - 使用共享的 `LLMEvaluator` 基类
   - 使用共享的配置管理

**优势**:
- Agent 评估功能独立但集成
- 与数据质量评估共享基础设施
- 清晰的模块边界

### Phase 4: 创建统一的 CLI (Phase 4: Create Unified CLI)

**目标**: 提供统一的命令行入口，支持两个子系统

```bash
# 数据质量评估
python -m DataQualityFiltering data-quality check --input data.json
python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

# Agent 性能评估
python -m DataQualityFiltering agent-eval evaluate --input agent_results.json
python -m DataQualityFiltering agent-eval batch --input results.json --max-workers 8
```

### Phase 5: 文档和测试 (Phase 5: Documentation and Testing)

1. **更新文档**
   - 创建主 `README.md` 说明整体架构
   - 创建 `data_quality/README.md` 说明数据质量评估
   - 创建 `agent_evaluation/README.md` 说明 Agent 评估

2. **添加示例**
   - 在 `examples/` 添加示例数据
   - 添加使用示例脚本

3. **兼容性保证**
   - 保持旧的 CLI 命令可用（向后兼容）
   - 添加弃用警告

## 📊 架构对比

### 重构前

```
DataQualityFiltering/
├── pipeline.py              # 数据质量管道
├── validators/              # 数据验证器
├── reviewers/               # 数据审查器
├── llm_evaluators/          # Agent 评估器（新增，职责不清）
├── pipelines/               # Agent 管道（新增，职责不清）
└── evaluate_agent.py        # Agent CLI（新增，职责不清）
```

**问题**:
- 职责混合：既有数据质量评估，又有 Agent 评估
- 结构混乱：两个系统的代码混在一起
- 扩展困难：添加新的评估类型需要修改核心代码

### 重构后

```
DataQualityFiltering/
├── core/                    # 共享核心
├── data_quality/            # 数据质量评估
├── agent_evaluation/        # Agent 性能评估
├── utils/                   # 工具模块
└── examples/                # 示例数据
```

**优势**:
- ✅ 职责清晰：两个子系统独立但共享基础设施
- ✅ 结构清晰：每个子系统有独立的目录
- ✅ 易于扩展：添加新的评估类型只需新增子目录
- ✅ 代码复用：共享 LLM 调用、配置等核心功能

## 🎯 设计原则

1. **单一职责**: 每个模块只负责一种评估类型
2. **开放封闭**: 对扩展开放（添加新的评估器），对修改封闭（不改动核心代码）
3. **依赖倒置**: 高层模块依赖抽象接口，不依赖具体实现
4. **接口隔离**: 评估器、审查器、管道各自有清晰的接口

## 🔄 迁移路径

### 兼容性保证

为了不影响现有用户，我们保持向后兼容：

1. **保留旧的导入路径**
   ```python
   # 旧的导入仍然可用
   from DataQualityFiltering import DataQualityPipeline
   from DataQualityFiltering.validators import MedicalDialogueValidator

   # 新的导入路径
   from DataQualityFiltering.data_quality import DataQualityPipeline
   from DataQualityFiltering.data_quality.validators import MedicalDialogueValidator
   ```

2. **保留旧的 CLI 命令**
   ```bash
   # 旧的命令仍然可用（显示弃用警告）
   python DataQualityFiltering/cli.py --input data.json

   # 推荐使用新的命令
   python -m DataQualityFiltering data-quality filter --input data.json
   ```

## 📝 实施优先级

1. **高优先级** (立即实施):
   - ✅ Phase 1: 创建核心基础设施
   - ✅ Phase 2: 重构数据质量评估子系统

2. **中优先级** (第二阶段):
   - Phase 3: 集成 Agent 评估子系统
   - Phase 4: 创建统一的 CLI

3. **低优先级** (后续优化):
   - Phase 5: 完善文档和测试
   - 性能优化
   - 添加更多评估器

## 🚀 预期收益

1. **代码质量**
   - 消除职责混淆
   - 减少代码重复
   - 提高可测试性

2. **可维护性**
   - 清晰的模块边界
   - 统一的接口设计
   - 完善的文档

3. **可扩展性**
   - 添加新的评估类型更容易
   - 支持插件式架构
   - 便于社区贡献

4. **用户体验**
   - 统一的命令行界面
   - 清晰的使用文档
   - 更好的错误提示
