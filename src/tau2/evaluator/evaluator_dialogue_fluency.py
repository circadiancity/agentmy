#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue Fluency Evaluator
对话流畅性评估器

评估 AI 医学助手在对话中的流畅性和沟通能力，包括：
- 问题理解能力 (25%)
- 回答连贯性 (25%)
- 语言表达清晰度 (25%)
- 交互能力 (25%)

从 DataQualityFiltering/agent_evaluation/evaluators/medical_dimensions.py 迁移
"""

import logging
from typing import Dict, List, Any, Optional

# 使用 tau2 的 LLM 工具
from tau2.utils.llm_utils import generate


class DialogueFluencyEvaluator:
    """
    对话流畅性评估器

    评估 AI 医学助手在对话中的流畅性，包括：
    - 问题理解能力 (25%)
    - 回答连贯性 (25%)
    - 语言表达清晰度 (25%)
    - 交互能力 (25%)
    """

    def __init__(
        self,
        model: str = "gpt-4",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        初始化对话流畅性评估器

        Args:
            model: LLM 模型名称
            cache_dir: 缓存目录
            use_cache: 是否使用缓存
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.cache_dir = cache_dir
        self.use_cache = use_cache

        # 评分权重
        self.weights = {
            "question_understanding": 0.25,
            "response_coherence": 0.25,
            "clarity": 0.25,
            "interaction": 0.25,
        }

    def evaluate(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str = "",
        reference_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        评估对话流畅性

        Args:
            patient_question: 患者问题
            ai_response: AI 助手的回答
            context_info: 额外上下文信息
            reference_answer: 参考医生回答（可选）

        Returns:
            评估结果 {
                "overall_score": float (0-5),
                "dimension_scores": {...},
                "strengths": List[str],
                "weaknesses": List[str],
                "errors": List[str],
                "comments": str,
            }
        """
        # 构建评估提示词
        prompt = self._build_evaluation_prompt(
            patient_question,
            ai_response,
            context_info,
            reference_answer
        )

        # 调用 LLM 评估
        try:
            llm_response = self._call_llm(prompt)
            result = self._parse_response(llm_response)
        except Exception as e:
            self.logger.error(f"对话流畅性评估失败: {e}")
            result = self._error_result(str(e))

        return result

    def _build_evaluation_prompt(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str,
        reference_answer: Optional[str],
    ) -> str:
        """构建评估提示词"""
        prompt = f"""请评估以下医学对话的流畅性和沟通质量。

**患者问题**:
{patient_question}

**AI 助手回答**:
{ai_response}

**上下文信息**:
{context_info if context_info else "无"}

请从以下四个维度评估（每个维度 0-5 分）：

1. **问题理解能力** (25%): 是否准确理解患者的问题和需求
2. **回答连贯性** (25%): 回答逻辑清晰，前后一致
3. **语言表达清晰度** (25%): 使用清晰易懂的语言
4. **交互能力** (25%): 恰当的追问、澄清和引导

请以 JSON 格式返回评估结果：
{{
  "question_understanding": {{"score": 4.0, "reasoning": "..."}},
  "response_coherence": {{"score": 3.5, "reasoning": "..."}},
  "clarity": {{"score": 4.5, "reasoning": "..."}},
  "interaction": {{"score": 4.0, "reasoning": "..."}},
  "overall_score": 4.0,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}}
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        response = generate(
            model=self.model,
            prompt=prompt,
            temperature=0.2,
            max_tokens=2000,
        )
        return response

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        import json
        import re

        # 尝试提取 JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))

                # 计算总分
                if "dimension_scores" not in result:
                    dimension_scores = {
                        "question_understanding": result["question_understanding"]["score"],
                        "response_coherence": result["response_coherence"]["score"],
                        "clarity": result["clarity"]["score"],
                        "interaction": result["interaction"]["score"],
                    }
                    result["dimension_scores"] = dimension_scores

                if "overall_score" not in result:
                    # 计算加权总分
                    overall = (
                        result["question_understanding"]["score"] * self.weights["question_understanding"] +
                        result["response_coherence"]["score"] * self.weights["response_coherence"] +
                        result["clarity"]["score"] * self.weights["clarity"] +
                        result["interaction"]["score"] * self.weights["interaction"]
                    )
                    result["overall_score"] = round(overall, 2)

                return result
            except json.JSONDecodeError:
                pass

        # 解析失败，返回错误
        return self._error_result("无法解析 LLM 响应")

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """返回错误结果"""
        return {
            "overall_score": 0.0,
            "dimension_scores": {
                "question_understanding": 0.0,
                "response_coherence": 0.0,
                "clarity": 0.0,
                "interaction": 0.0,
            },
            "strengths": [],
            "weaknesses": [],
            "errors": [error_msg],
            "suggestions": [],
            "comments": f"评估失败: {error_msg}",
        }
