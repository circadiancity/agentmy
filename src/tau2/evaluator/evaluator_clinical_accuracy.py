#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Accuracy Evaluator
临床准确性评估器

评估 AI 医学助手在临床场景中的准确性，包括：
- 医学知识准确性 (30%)
- 诊断推理合理性 (30%)
- 治疗建议适当性 (25%)
- 安全警告 (15%)

从 DataQualityFiltering/agent_evaluation/evaluators/medical_dimensions.py 迁移
"""

import logging
from typing import Dict, List, Any, Optional

# 使用 tau2 的 LLM 工具
from tau2.utils.llm_utils import generate


class ClinicalAccuracyEvaluator:
    """
    临床准确性评估器

    评估 AI 医学助手的临床准确性，包括：
    - 医学知识准确性 (30%)
    - 诊断推理合理性 (30%)
    - 治疗建议适当性 (25%)
    - 安全警告 (15%)
    """

    def __init__(
        self,
        model: str = "gpt-4",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        初始化临床准确性评估器

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
            "medical_knowledge": 0.30,
            "diagnostic_reasoning": 0.30,
            "treatment_appropriateness": 0.25,
            "safety_warnings": 0.15,
        }

    def evaluate(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str = "",
        reference_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        评估临床准确性

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
            self.logger.error(f"临床准确性评估失败: {e}")
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
        prompt = f"""请评估以下医学对话中 AI 助手的临床准确性。

**患者问题**:
{patient_question}

**AI 助手回答**:
{ai_response}

**上下文信息**:
{context_info if context_info else "无"}

**参考答案**（如果有）:
{reference_answer if reference_answer else "无"}

请从以下四个维度评估（每个维度 0-5 分）：

1. **医学知识准确性** (30%): 医学术语、疾病诊断、治疗方案是否准确
2. **诊断推理合理性** (30%): 症状分析、鉴别诊断的逻辑性
3. **治疗建议适当性** (25%): 治疗方案是否合理、安全
4. **安全警告** (15%): 是否及时提醒危险症状和就医建议

请以 JSON 格式返回评估结果：
{{
  "medical_knowledge": {{"score": 4.0, "reasoning": "..."}},
  "diagnostic_reasoning": {{"score": 3.5, "reasoning": "..."}},
  "treatment_appropriateness": {{"score": 4.5, "reasoning": "..."}},
  "safety_warnings": {{"score": 5.0, "reasoning": "..."}},
  "overall_score": 4.2,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}}
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        # 使用 tau2 的 LLM 工具
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
                        "medical_knowledge": result["medical_knowledge"]["score"],
                        "diagnostic_reasoning": result["diagnostic_reasoning"]["score"],
                        "treatment_appropriateness": result["treatment_appropriateness"]["score"],
                        "safety_warnings": result["safety_warnings"]["score"],
                    }
                    result["dimension_scores"] = dimension_scores

                if "overall_score" not in result:
                    # 计算加权总分
                    overall = (
                        result["medical_knowledge"]["score"] * self.weights["medical_knowledge"] +
                        result["diagnostic_reasoning"]["score"] * self.weights["diagnostic_reasoning"] +
                        result["treatment_appropriateness"]["score"] * self.weights["treatment_appropriateness"] +
                        result["safety_warnings"]["score"] * self.weights["safety_warnings"]
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
                "medical_knowledge": 0.0,
                "diagnostic_reasoning": 0.0,
                "treatment_appropriateness": 0.0,
                "safety_warnings": 0.0,
            },
            "strengths": [],
            "weaknesses": [],
            "errors": [error_msg],
            "suggestions": [],
            "comments": f"评估失败: {error_msg}",
        }
