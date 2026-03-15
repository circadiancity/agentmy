#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataQualityFiltering - 统一的医学评估框架

提供两个子系统的评估功能：
1. 数据质量评估 (data_quality) - 验证和过滤医学对话数据
2. Agent 性能评估 (agent_evaluation) - 评估 Agent 在医学任务上的表现

使用示例:
    # 数据质量评估
    from DataQualityFiltering.data_quality import DataQualityPipeline
    from DataQualityFiltering.data_quality import FilterConfig

    # Agent 性能评估
    from DataQualityFiltering.agent_evaluation import AgentEvaluationPipeline
    from DataQualityFiltering.agent_evaluation import MedicalAgentReviewer
"""

# 版本信息
__version__ = "2.0.0"
__author__ = "DataQualityFiltering Team"

# ============================================================================
# 核心基础设施
# ============================================================================
from .core import (
    # LLM 评估器
    LLMEvaluator,
    OpenAIEvaluator,
    AnthropicEvaluator,
    LocalLLMEvaluator,
    create_llm_evaluator,
    # 基类
    BaseEvaluator,
    BaseReviewer,
    BaseConfig,
    # 配置
    LLMConfig,
    EvaluationConfig,
    PipelineConfig,
    ConfigManager,
)

# ============================================================================
# 数据质量评估子系统
# ============================================================================
from .data_quality import (
    # 管道和过滤
    DataQualityPipeline,
    QualityFilter,
    FilterConfig as DataQualityFilterConfig,
    # 验证器
    MedicalDialogueValidator,
    # 审查器
    MedicalDialogueReviewer,
    # 工具
    HumanReviewProcess,
    LLMReviewer as DataQualityLLMReviewer,
    Calibrator,
)

# ============================================================================
# 向后兼容性：旧的导入路径仍然可用
# ============================================================================
# 从前的导入：from DataQualityFiltering import DataQualityPipeline
# 现在会自动重定向到 data_quality 子系统

# ============================================================================
# Agent 性能评估子系统
# ============================================================================
from .agent_evaluation import (
    AgentEvaluationPipeline,
    MedicalAgentReviewer,
)

# ============================================================================
# 公共 API
# ============================================================================

__all__ = [
    # 版本信息
    "__version__",
    "__author__",

    # ========== 核心基础设施 ==========
    # LLM 评估器
    "LLMEvaluator",
    "OpenAIEvaluator",
    "AnthropicEvaluator",
    "LocalLLMEvaluator",
    "create_llm_evaluator",
    # 基类
    "BaseEvaluator",
    "BaseReviewer",
    "BaseConfig",
    # 配置
    "LLMConfig",
    "EvaluationConfig",
    "PipelineConfig",
    "ConfigManager",

    # ========== 数据质量评估 ==========
    # 管道和过滤
    "DataQualityPipeline",
    "QualityFilter",
    "DataQualityFilterConfig",  # 使用别名避免冲突
    # 验证器
    "MedicalDialogueValidator",
    # 审查器
    "MedicalDialogueReviewer",
    # 工具
    "HumanReviewProcess",
    "DataQualityLLMReviewer",  # 使用别名避免冲突
    "Calibrator",

    # ========== Agent 性能评估 ==========
    "AgentEvaluationPipeline",
    "MedicalAgentReviewer",
]
