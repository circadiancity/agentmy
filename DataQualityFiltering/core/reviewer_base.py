#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Reviewer Interface
审查器抽象基类

定义统一的审查器接口，所有审查器都应继承此类。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging


class BaseReviewer(ABC):
    """
    审查器抽象基类

    审查器与评估器的区别：
    - 评估器 (Evaluator): 专注于某个维度的量化评分
    - 审查器 (Reviewer): 整合多个评估器，提供综合审查结果

    设计原则：
    1. 组合优于继承：审查器可以组合多个评估器
    2. 接口统一：所有审查器都实现相同的接口
    3. 灵活配置：支持自定义评估器组合和权重
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        pass_threshold: float = 3.5,
    ):
        """
        初始化审查器

        Args:
            name: 审查器名称
            description: 审查器描述
            pass_threshold: 通过阈值
        """
        self.name = name
        self.description = description or f"{name} reviewer"
        self.pass_threshold = pass_threshold
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @abstractmethod
    def review(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        审查单个项目

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            审查结果字典 {
                "task_id": str,  # 任务 ID
                "overall_score": float,  # 总分
                "pass_status": bool,  # 是否通过
                "pass_threshold": float,  # 通过阈值
                "dimension_scores": Dict[str, float],  # 各维度分数
                "dimension_details": Dict,  # 各维度详细信息
                "strengths": List[str],  # 优点列表
                "weaknesses": List[str],  # 不足列表
                "errors": List[str],  # 错误列表
                "suggestions": List[str],  # 改进建议
                "comments": str,  # 评语
                "metadata": Dict,  # 额外元数据
                "timestamp": str,  # 审查时间
            }
        """
        pass

    def review_batch(
        self,
        items: List[Any],
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        批量审查（默认实现，子类可以覆盖以优化性能）

        Args:
            items: 待审查项目列表
            show_progress: 是否显示进度

        Returns:
            审查结果列表
        """
        results = []

        for idx, item in enumerate(items, 1):
            if show_progress and idx % 10 == 0:
                self.logger.info(f"审查进度: {idx}/{len(items)}")

            # 假设 item 是字典，如果不是，子类应该覆盖此方法
            if isinstance(item, dict):
                result = self.review(**item)
            else:
                result = self.review(item)

            results.append(result)

        return results

    def get_statistics(
        self,
        reviews: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        统计批量审查结果

        Args:
            reviews: 审查结果列表

        Returns:
            统计信息 {
                "total_reviews": int,  # 总数
                "passed": int,  # 通过数
                "failed": int,  # 失败数
                "pass_rate": float,  # 通过率
                "average_scores": Dict,  # 平均分数
                "score_distribution": Dict,  # 分数分布
                "min_score": float,  # 最低分
                "max_score": float,  # 最高分
            }
        """
        if not reviews:
            return {}

        total = len(reviews)
        passed = sum(1 for r in reviews if r.get("pass_status", False))
        failed = total - passed

        # 收集所有分数
        overall_scores = [r.get("overall_score", 0) for r in reviews]

        # 收集维度分数
        dimension_scores = {}
        for review in reviews:
            for dim, score in review.get("dimension_scores", {}).items():
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(score)

        # 计算平均分
        average_scores = {
            "overall": round(sum(overall_scores) / total, 2) if total > 0 else 0,
        }

        for dim, scores in dimension_scores.items():
            average_scores[dim] = round(sum(scores) / len(scores), 2) if scores else 0

        # 分数分布
        score_ranges = {
            "excellent": sum(1 for s in overall_scores if s >= 4.5),
            "good": sum(1 for s in overall_scores if 4.0 <= s < 4.5),
            "satisfactory": sum(1 for s in overall_scores if 3.5 <= s < 4.0),
            "needs_improvement": sum(1 for s in overall_scores if 3.0 <= s < 3.5),
            "poor": sum(1 for s in overall_scores if s < 3.0),
        }

        return {
            "total_reviews": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
            "average_scores": average_scores,
            "score_distribution": score_ranges,
            "min_score": round(min(overall_scores), 2) if overall_scores else 0,
            "max_score": round(max(overall_scores), 2) if overall_scores else 0,
        }

    def get_pass_status(
        self,
        score: float,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        判断是否通过

        Args:
            score: 分数
            threshold: 通过阈值（默认使用实例阈值）

        Returns:
            是否通过
        """
        threshold = threshold or self.pass_threshold
        return score >= threshold

    def get_info(self) -> Dict[str, Any]:
        """
        获取审查器信息

        Returns:
            审查器信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "pass_threshold": self.pass_threshold,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', threshold={self.pass_threshold})"


class EvaluatorBasedReviewer(BaseReviewer):
    """
    基于评估器的审查器

    这是一个通用基类，可以轻松组合多个评估器来创建审查器。

    使用示例:
        reviewer = EvaluatorBasedReviewer(
            name="medical_agent_reviewer",
            evaluators=[
                ClinicalAccuracyEvaluator(),
                DialogueFluencyEvaluator(),
                SafetyEmpathyEvaluator(),
            ],
            weights={
                "clinical_accuracy": 0.40,
                "dialogue_fluency": 0.35,
                "safety_empathy": 0.25,
            },
        )
    """

    def __init__(
        self,
        name: str,
        evaluators: List[Any],
        weights: Optional[Dict[str, float]] = None,
        description: Optional[str] = None,
        pass_threshold: float = 3.5,
    ):
        """
        初始化基于评估器的审查器

        Args:
            name: 审查器名称
            evaluators: 评估器列表
            weights: 各维度权重（维度名称 -> 权重）
            description: 审查器描述
            pass_threshold: 通过阈值
        """
        super().__init__(name, description, pass_threshold)

        self.evaluators = evaluators
        self.weights = weights or {}

        # 验证权重
        if self.weights:
            for dim_name in self.weights.keys():
                # 检查是否有评估器提供这个维度
                found = False
                for evaluator in evaluators:
                    if hasattr(evaluator, 'dimension_name') and evaluator.dimension_name == dim_name:
                        found = True
                        break
                if not found:
                    self.logger.warning(f"权重中的维度 '{dim_name}' 没有对应的评估器")

    def review(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        综合审查（基于所有评估器的结果）

        Returns:
            审查结果字典
        """
        from datetime import datetime

        start_time = datetime.now()
        task_id = kwargs.get("task_id", "unknown")

        # 运行所有评估器
        all_results = {}
        dimension_scores = {}
        dimension_details = {}
        all_strengths = []
        all_weaknesses = []
        all_errors = []
        all_suggestions = []

        for evaluator in self.evaluators:
            self.logger.debug(f"运行评估器: {evaluator.name}")

            try:
                result = evaluator.evaluate(*args, **kwargs)

                all_results[evaluator.name] = result

                # 收集维度分数
                if "dimension_scores" in result:
                    dimension_scores.update(result["dimension_scores"])

                # 收集详细信息
                if "metadata" in result and "details" in result["metadata"]:
                    dimension_details[evaluator.name] = result["metadata"]["details"]

                # 收集反馈
                all_strengths.extend(result.get("strengths", []))
                all_weaknesses.extend(result.get("weaknesses", []))
                all_errors.extend(result.get("errors", []))
                all_suggestions.extend(result.get("suggestions", []))

            except Exception as e:
                self.logger.error(f"评估器 {evaluator.name} 执行失败: {e}")
                all_errors.append(f"{evaluator.name}: {str(e)}")

        # 计算加权总分
        overall_score = self._calculate_overall_score(dimension_scores)

        # 判断是否通过
        pass_status = self.get_pass_status(overall_score)

        # 生成综合评语
        comments = self._generate_comments(dimension_scores, overall_score, pass_status)

        # 计算耗时
        elapsed_time = (datetime.now() - start_time).total_seconds()

        return {
            "task_id": task_id,
            "overall_score": round(overall_score, 2),
            "pass_status": pass_status,
            "pass_threshold": self.pass_threshold,
            "dimension_scores": dimension_scores,
            "dimension_details": dimension_details,
            "strengths": all_strengths,
            "weaknesses": all_weaknesses,
            "errors": all_errors,
            "suggestions": all_suggestions,
            "comments": comments,
            "metadata": {
                "evaluator_results": all_results,
                "weights": self.weights,
                "reviewer": self.get_info(),
            },
            "timestamp": datetime.now().isoformat(),
            "evaluation_time_seconds": round(elapsed_time, 2),
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
        pass_status: bool,
    ) -> str:
        """
        生成综合评语

        Args:
            dimension_scores: 各维度分数
            overall_score: 总分
            pass_status: 是否通过

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
        if dimension_scores:
            comments.append("\n**各维度评分**:")
            for dimension, score in dimension_scores.items():
                comments.append(f"  - {dimension}: {score:.1f}/5.0")
                if score < 3.0:
                    comments.append(f"    ⚠️  需要提升 {dimension} 的表现")

        return "\n".join(comments)

    def check_availability(self) -> Dict[str, Any]:
        """
        检查所有评估器的可用性

        Returns:
            各评估器状态
        """
        availability = {
            "reviewer_available": True,
            "evaluators": {},
        }

        for evaluator in self.evaluators:
            evaluator_name = evaluator.name

            # 检查评估器是否有 check_availability 方法
            if hasattr(evaluator, 'check_availability'):
                availability["evaluators"][evaluator_name] = evaluator.check_availability()

                # 如果有评估器不可用，标记审查器为部分可用
                if not availability["evaluators"][evaluator_name].get("available", True):
                    availability["reviewer_available"] = False
            else:
                # 假设评估器可用
                availability["evaluators"][evaluator_name] = {"available": True}

        return availability


# 导出
__all__ = [
    "BaseReviewer",
    "EvaluatorBasedReviewer",
]
