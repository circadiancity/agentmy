#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management
配置管理模块

提供统一的配置管理功能，支持从文件、环境变量、命令行参数加载配置。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod


class BaseConfig(ABC):
    """
    配置基类

    提供配置加载、验证、序列化等基础功能。
    """

    @classmethod
    @abstractmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BaseConfig":
        """
        从字典创建配置对象

        Args:
            config_dict: 配置字典

        Returns:
            配置对象
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            配置字典
        """
        if hasattr(self, '__dataclass_fields__'):
            return asdict(self)
        else:
            return self.__dict__

    def to_json(self, indent: int = 2) -> str:
        """
        转换为 JSON 字符串

        Args:
            indent: 缩进空格数

        Returns:
            JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save(self, file_path: str):
        """
        保存到文件

        Args:
            file_path: 文件路径
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, file_path: str) -> "BaseConfig":
        """
        从文件加载

        Args:
            file_path: 文件路径

        Returns:
            配置对象
        """
        with open(file_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        return cls.from_dict(config_dict)

    def validate(self) -> bool:
        """
        验证配置

        Returns:
            是否有效
        """
        return True

    def update(self, **kwargs):
        """
        更新配置

        Args:
            **kwargs: 配置键值对
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logging.warning(f"配置中不存在字段: {key}")


@dataclass
class LLMConfig(BaseConfig):
    """
    LLM 配置

    管理 LLM 相关的配置，包括模型选择、API 密钥、超参数等。
    """

    # 模型配置
    model: str = "gpt-4-turbo"
    provider: str = "openai"  # openai, anthropic, local

    # API 配置
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3

    # 生成参数
    max_tokens: int = 4096
    temperature: float = 0.2
    top_p: float = 1.0

    # 缓存配置
    cache_dir: Optional[str] = None
    use_cache: bool = True

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LLMConfig":
        """
        从字典创建配置对象

        Args:
            config_dict: 配置字典

        Returns:
            LLMConfig 对象
        """
        # 从环境变量获取 API 密钥（如果配置中没有）
        api_key = config_dict.get("api_key")
        if not api_key:
            provider = config_dict.get("provider", "openai")
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")

        # 设置默认的 base_url
        base_url = config_dict.get("base_url")
        if not base_url:
            provider = config_dict.get("provider", "openai")
            if provider == "openai":
                base_url = "https://api.openai.com/v1"
            elif provider == "local":
                base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:8000")

        return cls(
            model=config_dict.get("model", "gpt-4-turbo"),
            provider=config_dict.get("provider", "openai"),
            api_key=api_key,
            base_url=base_url,
            timeout=config_dict.get("timeout", 60),
            max_retries=config_dict.get("max_retries", 3),
            max_tokens=config_dict.get("max_tokens", 4096),
            temperature=config_dict.get("temperature", 0.2),
            top_p=config_dict.get("top_p", 1.0),
            cache_dir=config_dict.get("cache_dir"),
            use_cache=config_dict.get("use_cache", True),
        )

    def get_api_key(self) -> Optional[str]:
        """
        获取 API 密钥

        Returns:
            API 密钥
        """
        return self.api_key

    def check_availability(self) -> Dict[str, bool]:
        """
        检查 LLM 服务可用性

        Returns:
            可用性状态
        """
        status = {
            "api_key_configured": self.api_key is not None,
            "api_accessible": False,
            "model_available": False,
        }

        if self.provider == "local":
            status["api_key_configured"] = True  # 本地模型不需要 API 密钥

        return status


@dataclass
class EvaluationConfig(BaseConfig):
    """
    评估配置

    管理评估相关的配置，包括阈值、权重、并发等。
    """

    # 评分配置
    pass_threshold: float = 3.5
    score_range: tuple = (0.0, 5.0)

    # 维度权重
    dimension_weights: Dict[str, float] = field(default_factory=dict)

    # 并发配置
    max_workers: int = 4
    batch_size: int = 10

    # 输出配置
    save_intermediate: bool = True
    output_format: str = "json"  # json, markdown

    # 日志配置
    log_level: str = "INFO"
    show_progress: bool = True

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "EvaluationConfig":
        """
        从字典创建配置对象

        Args:
            config_dict: 配置字典

        Returns:
            EvaluationConfig 对象
        """
        return cls(
            pass_threshold=config_dict.get("pass_threshold", 3.5),
            score_range=tuple(config_dict.get("score_range", (0.0, 5.0))),
            dimension_weights=config_dict.get("dimension_weights", {}),
            max_workers=config_dict.get("max_workers", 4),
            batch_size=config_dict.get("batch_size", 10),
            save_intermediate=config_dict.get("save_intermediate", True),
            output_format=config_dict.get("output_format", "json"),
            log_level=config_dict.get("log_level", "INFO"),
            show_progress=config_dict.get("show_progress", True),
        )

    def validate(self) -> bool:
        """
        验证配置

        Returns:
            是否有效
        """
        # 检查阈值范围
        min_score, max_score = self.score_range
        if not (min_score <= self.pass_threshold <= max_score):
            logging.warning(
                f"通过阈值 {self.pass_threshold} 不在分数范围 {self.score_range} 内"
            )
            return False

        # 检查权重总和
        if self.dimension_weights:
            total_weight = sum(self.dimension_weights.values())
            if abs(total_weight - 1.0) > 0.01:  # 允许小的浮点误差
                logging.warning(
                    f"维度权重总和为 {total_weight}，建议为 1.0"
                )

        return True


@dataclass
class PipelineConfig(BaseConfig):
    """
    管道配置

    管理整个评估管道的配置。
    """

    # 子配置
    llm: LLMConfig = field(default_factory=LLMConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    # 输入输出配置
    input_path: Optional[str] = None
    output_dir: str = "./outputs"

    # 高级配置
    enable_calibraton: bool = False
    calibration_min_tasks: int = 3
    calibration_min_r: float = 0.5

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PipelineConfig":
        """
        从字典创建配置对象

        Args:
            config_dict: 配置字典

        Returns:
            PipelineConfig 对象
        """
        # 创建子配置
        llm_config = LLMConfig.from_dict(config_dict.get("llm", {}))
        evaluation_config = EvaluationConfig.from_dict(config_dict.get("evaluation", {}))

        return cls(
            llm=llm_config,
            evaluation=evaluation_config,
            input_path=config_dict.get("input_path"),
            output_dir=config_dict.get("output_dir", "./outputs"),
            enable_calibraton=config_dict.get("enable_calibration", False),
            calibration_min_tasks=config_dict.get("calibration_min_tasks", 3),
            calibration_min_r=config_dict.get("calibration_min_r", 0.5),
        )

    def setup_logging(self):
        """
        设置日志
        """
        log_level = self.evaluation.log_level
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def create_output_dir(self):
        """
        创建输出目录
        """
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """
        验证配置

        Returns:
            是否有效
        """
        valid = True

        # 验证子配置
        if not self.llm.validate():
            valid = False

        if not self.evaluation.validate():
            valid = False

        # 检查输入路径
        if self.input_path and not Path(self.input_path).exists():
            logging.error(f"输入路径不存在: {self.input_path}")
            valid = False

        return valid


class ConfigManager:
    """
    配置管理器

    提供配置加载、合并、验证等功能。
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def load_config(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        env_prefix: str = "DQF_",
    ) -> PipelineConfig:
        """
        加载配置

        优先级（从高到低）：
        1. 命令行参数（config_dict）
        2. 配置文件（config_path）
        3. 环境变量
        4. 默认值

        Args:
            config_path: 配置文件路径
            config_dict: 配置字典（通常来自命令行参数）
            env_prefix: 环境变量前缀

        Returns:
            PipelineConfig 对象
        """
        # 1. 从配置文件加载
        file_config = {}
        if config_path and Path(config_path).exists():
            self.logger.info(f"从文件加载配置: {config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)

        # 2. 从环境变量加载
        env_config = self._load_from_env(env_prefix)

        # 3. 合并配置（环境变量覆盖文件，命令行覆盖环境变量）
        merged_config = self._merge_configs(file_config, env_config, config_dict or {})

        # 4. 创建配置对象
        config = PipelineConfig.from_dict(merged_config)

        # 5. 验证配置
        if not config.validate():
            raise ValueError("配置验证失败")

        return config

    def _load_from_env(self, prefix: str) -> Dict[str, Any]:
        """
        从环境变量加载配置

        Args:
            prefix: 环境变量前缀

        Returns:
            配置字典
        """
        config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀，转换为配置键
                config_key = key[len(prefix):].lower()

                # 处理嵌套键（例如：llm_model -> llm.model）
                if "_" in config_key:
                    parts = config_key.split("_")
                    current = config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = self._parse_env_value(value)
                else:
                    config[config_key] = self._parse_env_value(value)

        return config

    def _parse_env_value(self, value: str) -> Any:
        """
        解析环境变量值

        Args:
            value: 环境变量值

        Returns:
            解析后的值
        """
        # 尝试解析为布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 尝试解析为数字
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # 返回字符串
        return value

    def _merge_configs(
        self,
        *configs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合并多个配置字典

        Args:
            *configs: 配置字典列表

        Returns:
            合并后的配置字典
        """
        merged = {}

        for config in configs:
            self._deep_merge(merged, config)

        return merged

    def _deep_merge(
        self,
        base: Dict[str, Any],
        update: Dict[str, Any],
    ):
        """
        深度合并字典

        Args:
            base: 基础字典（会被修改）
            update: 更新字典
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# 导出
__all__ = [
    "BaseConfig",
    "LLMConfig",
    "EvaluationConfig",
    "PipelineConfig",
    "ConfigManager",
]
