#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Evaluator Interface
评估器抽象基类

定义统一的评估器接口，所有评估器都应继承此类。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import logging


class BaseEvaluator(ABC):
    """
    评估器抽象基类

    所有评估器（数据质量评估器、Agent 性能评估器等）都应继承此类。

    设计原则：
    1. 单一职责：每个评估器专注于一个特定的评估维度
    2. 接口统一：所有评估器都实现相同的接口
    3. 可扩展性：子类可以灵活扩展评估逻辑
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        weight: float = 1.0,
    ):
        """
        初始化评估器

        Args:
            name: 评估器名称
            description: 评估器描述
            weight: 权重（用于计算总分）
        """
        self.name = name
        self.description = description or f"{name} evaluator"
        self.weight = weight
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @abstractmethod
    def evaluate(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        评估单个项目

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            评估结果字典 {
                "overall_score": float,  # 总分（0-5 或 0-100）
                "dimension_scores": Dict[str, float],  # 各维度分数
                "pass_status": bool,  # 是否通过
                "strengths": List[str],  # 优点列表
                "weaknesses": List[str],  # 不足列表
                "errors": List[str],  # 错误列表
                "suggestions": List[str],  # 改进建议
                "comments": str,  # 评语
                "metadata": Dict,  # 额外元数据
            }
        """
        pass

    def evaluate_batch(
        self,
        items: List[Any],
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        批量评估（默认实现，子类可以覆盖以优化性能）

        Args:
            items: 待评估项目列表
            show_progress: 是否显示进度

        Returns:
            评估结果列表
        """
        results = []

        for idx, item in enumerate(items, 1):
            if show_progress and idx % 10 == 0:
                self.logger.info(f"评估进度: {idx}/{len(items)}")

            # 假设 item 是字典，如果不是，子类应该覆盖此方法
            if isinstance(item, dict):
                result = self.evaluate(**item)
            else:
                result = self.evaluate(item)

            results.append(result)

        return results

    def calculate_weighted_score(
        self,
        score: float,
        max_score: float = 5.0,
    ) -> float:
        """
        计算加权分数

        Args:
            score: 原始分数
            max_score: 最大分数

        Returns:
            加权后的分数
        """
        normalized = score / max_score
        return normalized * self.weight

    def get_pass_status(
        self,
        score: float,
        threshold: float = 3.5,
    ) -> bool:
        """
        判断是否通过

        Args:
            score: 分数
            threshold: 通过阈值

        Returns:
            是否通过
        """
        return score >= threshold

    def get_info(self) -> Dict[str, Any]:
        """
        获取评估器信息

        Returns:
            评估器信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', weight={self.weight})"


class DimensionEvaluator(BaseEvaluator):
    """
    维度评估器

    用于评估某个特定维度的质量或性能。
    例如：临床准确性、对话流畅性、安全性等。
    """

    def __init__(
        self,
        name: str,
        dimension_name: str,
        description: Optional[str] = None,
        weight: float = 1.0,
        score_range: Tuple[float, float] = (0.0, 5.0),
    ):
        """
        初始化维度评估器

        Args:
            name: 评估器名称
            dimension_name: 维度名称
            description: 评估器描述
            weight: 权重
            score_range: 分数范围 (min, max)
        """
        super().__init__(name, description, weight)
        self.dimension_name = dimension_name
        self.score_range = score_range

    @abstractmethod
    def evaluate_dimension(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        评估特定维度

        Returns:
            维度评估结果 {
                "score": float,  # 维度分数
                "details": Dict,  # 详细信息
                "strengths": List[str],
                "weaknesses": List[str],
                "suggestions": List[str],
            }
        """
        pass

    def evaluate(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        评估（实现 BaseEvaluator 接口）

        Returns:
            评估结果字典
        """
        # 调用子类的维度评估方法
        dimension_result = self.evaluate_dimension(*args, **kwargs)

        # 规范化结果
        score = dimension_result.get("score", 0.0)

        # 确保分数在有效范围内
        min_score, max_score = self.score_range
        score = max(min_score, min(max_score, score))

        return {
            "overall_score": score,
            "dimension_scores": {
                self.dimension_name: score,
            },
            "pass_status": self.get_pass_status(score),
            "strengths": dimension_result.get("strengths", []),
            "weaknesses": dimension_result.get("weaknesses", []),
            "errors": dimension_result.get("errors", []),
            "suggestions": dimension_result.get("suggestions", []),
            "comments": dimension_result.get("comments", ""),
            "metadata": {
                "dimension": self.dimension_name,
                "details": dimension_result.get("details", {}),
                "evaluator": self.get_info(),
            },
        }


class CompositeEvaluator(BaseEvaluator):
    """
    组合评估器

    将多个评估器组合在一起，计算综合评分。
    """

    def __init__(
        self,
        name: str,
        evaluators: List[BaseEvaluator],
        weights: Optional[Dict[str, float]] = None,
        description: Optional[str] = None,
    ):
        """
        初始化组合评估器

        Args:
            name: 评估器名称
            evaluators: 子评估器列表
            weights: 各评估器的权重（评估器名称 -> 权重）
            description: 评估器描述
        """
        super().__init__(name, description, weight=1.0)
        self.evaluators = evaluators
        self.weights = weights or {}

        # 验证权重
        for evaluator_name in self.weights.keys():
            if not any(e.name == evaluator_name for e in evaluators):
                raise ValueError(f"评估器 '{evaluator_name}' 不在评估器列表中")

    def evaluate(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        综合评估

        Returns:
            综合评估结果
        """
        all_results = {}
        dimension_scores = {}
        all_strengths = []
        all_weaknesses = []
        all_errors = []
        all_suggestions = []

        # 运行所有评估器
        for evaluator in self.evaluators:
            self.logger.debug(f"运行评估器: {evaluator.name}")
            result = evaluator.evaluate(*args, **kwargs)

            all_results[evaluator.name] = result

            # 收集维度分数
            if "dimension_scores" in result:
                dimension_scores.update(result["dimension_scores"])

            # 收集反馈
            all_strengths.extend(result.get("strengths", []))
            all_weaknesses.extend(result.get("weaknesses", []))
            all_errors.extend(result.get("errors", []))
            all_suggestions.extend(result.get("suggestions", []))

        # 计算加权总分
        overall_score = self._calculate_overall_score(dimension_scores)

        return {
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "pass_status": self.get_pass_status(overall_score),
            "strengths": all_strengths,
            "weaknesses": all_weaknesses,
            "errors": all_errors,
            "suggestions": all_suggestions,
            "comments": self._generate_comments(dimension_scores, overall_score),
            "metadata": {
                "evaluator_results": all_results,
                "weights": self.weights,
                "evaluator": self.get_info(),
            },
        }

    def _calculate_overall_score(
        self,
        dimension_scores: Dict[str, float],
    ) -> float:
        """
        计算总分

        Args:
            dimension_scores: 各维度分数

        Returns:
            总分
        """
        if not dimension_scores:
            return 0.0

        if not self.weights:
            # 没有权重，计算简单平均
            return round(sum(dimension_scores.values()) / len(dimension_scores), 2)

        # 使用权重计算
        weighted_sum = 0.0
        total_weight = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.weights.get(dimension, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

    def _generate_comments(
        self,
        dimension_scores: Dict[str, float],
        overall_score: float,
    ) -> str:
        """
        生成综合评语

        Args:
            dimension_scores: 各维度分数
            overall_score: 总分

        Returns:
            评语文本
        """
        comments = []

        # 总体评价
        if overall_score >= 4.5:
            comments.append("✅ 优秀的表现，各方面都非常出色。")
        elif overall_score >= 4.0:
            comments.append("✅ 良好的表现，达到高质量标准。")
        elif overall_score >= 3.5:
            comments.append("✓ 达到基本要求，有改进空间。")
        elif overall_score >= 3.0:
            comments.append("⚠️  低于理想标准，需要明显改进。")
        elif overall_score >= 2.0:
            comments.append("❌ 存在明显问题，不建议使用。")
        else:
            comments.append("❌ 严重不达标，存在重大缺陷。")

        # 各维度评价
        for dimension, score in dimension_scores.items():
            comments.append(f"\n**{dimension}**: {score:.1f}/5.0")
            if score < 3.0:
                comments.append(f"  - 需要提升 {dimension} 的表现")

        return "\n".join(comments)


# 导出
__all__ = [
    "BaseEvaluator",
    "DimensionEvaluator",
    "CompositeEvaluator",
]
