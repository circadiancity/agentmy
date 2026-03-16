#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Evaluator
综合医疗评估器

整合三个医疗评估维度，为 tau2 框架提供统一的医疗评估接口：
- ClinicalAccuracyEvaluator: 临床准确性
- DialogueFluencyEvaluator: 对话流畅性
- SafetyEmpathyEvaluator: 安全性与同理心

继承自 tau2.evaluator.EvaluatorBase，实现 calculate_reward 方法。
"""

import logging
from typing import Optional
from tau2.data_model.message import Message
from tau2.data_model.simulation import ClinicalCheck, RewardInfo
from tau2.data_model.tasks import RewardType, Task
from tau2.evaluator.evaluator_base import EvaluatorBase
from tau2.evaluator.evaluator_clinical_accuracy import ClinicalAccuracyEvaluator
from tau2.evaluator.evaluator_dialogue_fluency import DialogueFluencyEvaluator
from tau2.evaluator.evaluator_safety_empathy import SafetyEmpathyEvaluator


class ClinicalEvaluator(EvaluatorBase):
    """
    综合医疗评估器

    整合三个医疗维度评估器，为医疗领域的 Agent 评估提供统一的接口。

    评估维度：
    - 临床准确性 (40%): 医学知识、诊断推理、治疗建议、安全警告
    - 对话流畅性 (30%): 问题理解、回答连贯性、表达清晰度、交互能力
    - 安全性与同理心 (30%): 安全意识、同理心表达、沟通技巧
    """

    # 默认权重配置
    DEFAULT_WEIGHTS = {
        "clinical_accuracy": 0.40,
        "dialogue_fluency": 0.30,
        "safety_empathy": 0.30,
    }

    # 评分阈值：高于此分数认为通过评估
    DEFAULT_PASS_THRESHOLD = 3.0  # 0-5 分制

    def __init__(
        self,
        model: str = "gpt-4",
        weights: Optional[dict] = None,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        初始化综合医疗评估器

        Args:
            model: LLM 模型名称
            weights: 自定义权重配置，默认为 DEFAULT_WEIGHTS
            pass_threshold: 通过评估的分数阈值 (0-5)
            cache_dir: 缓存目录
            use_cache: 是否使用缓存
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.pass_threshold = pass_threshold

        # 初始化三个医疗评估器
        self.clinical_accuracy_eval = ClinicalAccuracyEvaluator(
            model=model, cache_dir=cache_dir, use_cache=use_cache
        )
        self.dialogue_fluency_eval = DialogueFluencyEvaluator(
            model=model, cache_dir=cache_dir, use_cache=use_cache
        )
        self.safety_empathy_eval = SafetyEmpathyEvaluator(
            model=model, cache_dir=cache_dir, use_cache=use_cache
        )

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Message],
        model: str = "gpt-4",
        weights: Optional[dict] = None,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        **kwargs,
    ) -> RewardInfo:
        """
        计算医疗任务的奖励分数

        Args:
            task: 任务对象，包含用户场景和评估标准
            full_trajectory: 完整的对话轨迹（用户、Agent、环境的消息列表）
            model: LLM 模型名称
            weights: 自定义权重配置
            pass_threshold: 通过阈值
            **kwargs: 额外参数

        Returns:
            RewardInfo: 包含 clinical_checks 的奖励信息
        """
        # 创建实例（因为 __init__ 不是类方法）
        evaluator = cls(
            model=model,
            weights=weights,
            pass_threshold=pass_threshold,
        )

        # 从轨迹中提取患者问题和 AI 回答
        patient_question, ai_response = evaluator._extract_dialogue(full_trajectory)

        # 获取上下文信息（从 task 中提取）
        context_info = evaluator._extract_context(task)

        # 可选：获取参考答案
        reference_answer = kwargs.get("reference_answer", None)

        # 执行三个维度的评估
        accuracy_result = evaluator.clinical_accuracy_eval.evaluate(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        fluency_result = evaluator.dialogue_fluency_eval.evaluate(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        safety_result = evaluator.safety_empathy_eval.evaluate(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 整合三个维度的评估结果
        clinical_check = evaluator._combine_results(
            accuracy_result,
            fluency_result,
            safety_result,
        )

        # 计算总奖励分数
        overall_reward = evaluator._calculate_overall_reward(clinical_check)

        # 构建 RewardInfo
        reward_info = RewardInfo(
            reward=overall_reward,
            clinical_checks=[clinical_check],
            reward_basis=[RewardType.CLINICAL],
            reward_breakdown={RewardType.CLINICAL: overall_reward},
            info={
                "model": model,
                "weights": evaluator.weights,
                "pass_threshold": evaluator.pass_threshold,
            },
        )

        return reward_info

    def _extract_dialogue(
        self, full_trajectory: list[Message]
    ) -> tuple[str, str]:
        """
        从对话轨迹中提取患者问题和 AI 回答

        Args:
            full_trajectory: 完整的对话轨迹

        Returns:
            (patient_question, ai_response) 元组
        """
        patient_question = ""
        ai_response = ""

        # 找到最后一条用户消息作为患者问题
        for msg in reversed(full_trajectory):
            if msg.role == "user":
                patient_question = msg.content or ""
                break

        # 找到最后一条助手消息作为 AI 回答
        for msg in reversed(full_trajectory):
            if msg.role == "assistant":
                # 如果有工具调用，也包含在回答中
                if msg.tool_calls:
                    tool_info = "\n".join([
                        f"工具调用: {call.function.name}({call.function.arguments})"
                        for call in msg.tool_calls
                    ])
                    ai_response = (msg.content or "") + "\n" + tool_info
                else:
                    ai_response = msg.content or ""
                break

        return patient_question, ai_response

    def _extract_context(self, task: Task) -> str:
        """
        从任务中提取上下文信息

        Args:
            task: 任务对象

        Returns:
            上下文字符串
        """
        context_parts = []

        # 添加领域信息
        if hasattr(task.user_scenario.instructions, 'domain'):
            context_parts.append(f"医疗领域: {task.user_scenario.instructions.domain}")

        # 添加任务描述
        if task.description and task.description.purpose:
            context_parts.append(f"任务目的: {task.description.purpose}")

        # 添加用户已知信息
        if hasattr(task.user_scenario.instructions, 'known_info') and \
           task.user_scenario.instructions.known_info:
            context_parts.append(f"患者已知信息: {task.user_scenario.instructions.known_info}")

        return "\n".join(context_parts)

    def _combine_results(
        self,
        accuracy_result: dict,
        fluency_result: dict,
        safety_result: dict,
    ) -> ClinicalCheck:
        """
        整合三个维度的评估结果

        Args:
            accuracy_result: 临床准确性评估结果
            fluency_result: 对话流畅性评估结果
            safety_result: 安全性与同理心评估结果

        Returns:
            ClinicalCheck 对象
        """
        # 计算加权总分
        overall_score = (
            accuracy_result["overall_score"] * self.weights["clinical_accuracy"] +
            fluency_result["overall_score"] * self.weights["dialogue_fluency"] +
            safety_result["overall_score"] * self.weights["safety_empathy"]
        )

        # 整合维度分数
        dimension_scores = {
            "clinical_accuracy": accuracy_result["dimension_scores"],
            "dialogue_fluency": fluency_result["dimension_scores"],
            "safety_empathy": safety_result["dimension_scores"],
        }

        # 整合优点
        strengths = []
        strengths.extend(accuracy_result.get("strengths", []))
        strengths.extend(fluency_result.get("strengths", []))
        strengths.extend(safety_result.get("strengths", []))

        # 整合不足
        weaknesses = []
        weaknesses.extend(accuracy_result.get("weaknesses", []))
        weaknesses.extend(fluency_result.get("weaknesses", []))
        weaknesses.extend(safety_result.get("weaknesses", []))

        # 整合建议
        suggestions = []
        suggestions.extend(accuracy_result.get("suggestions", []))
        suggestions.extend(fluency_result.get("suggestions", []))
        suggestions.extend(safety_result.get("suggestions", []))

        # 整合错误
        errors = []
        errors.extend(accuracy_result.get("errors", []))
        errors.extend(fluency_result.get("errors", []))
        errors.extend(safety_result.get("errors", []))

        # 判断是否通过阈值
        met = overall_score >= self.pass_threshold

        # 计算奖励分数（归一化到 0-1）
        reward = overall_score / 5.0

        # 构建评语
        comments = f"""
综合医疗评估结果：
- 总分: {overall_score:.2f}/5.0 ({'通过' if met else '未通过'})
- 临床准确性: {accuracy_result['overall_score']:.2f}/5.0
- 对话流畅性: {fluency_result['overall_score']:.2f}/5.0
- 安全性与同理心: {safety_result['overall_score']:.2f}/5.0
        """.strip()

        if errors:
            comments += f"\n评估错误: {', '.join(errors)}"

        return ClinicalCheck(
            overall_score=round(overall_score, 2),
            dimension_scores=dimension_scores,
            met=met,
            reward=round(reward, 3),
            strengths=strengths if strengths else None,
            weaknesses=weaknesses if weaknesses else None,
            suggestions=suggestions if suggestions else None,
            comments=comments,
        )

    def _calculate_overall_reward(self, clinical_check: ClinicalCheck) -> float:
        """
        根据临床检查结果计算总体奖励分数

        Args:
            clinical_check: 临床检查结果

        Returns:
            奖励分数 (0-1)
        """
        # 直接使用 clinical_check 中的 reward
        return clinical_check.reward
