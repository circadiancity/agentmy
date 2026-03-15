#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Evaluator Base Class
LLM 评估器基类

提供统一的 LLM 调用接口，支持多种 LLM 提供商。
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib


class LLMEvaluator(ABC):
    """
    LLM 评估器基类

    支持多种 LLM 提供商：
    - OpenAI (GPT-4, GPT-4-turbo, GPT-3.5-turbo)
    - Anthropic (Claude 3 Opus, Claude 3 Sonnet)
    - 本地模型 (通过 API)
    """

    # 模型配置
    MODEL_CONFIGS = {
        # OpenAI 模型
        "gpt-4-turbo": {
            "provider": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "max_tokens": 4096,
            "temperature": 0.2,
        },
        "gpt-4": {
            "provider": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "max_tokens": 4096,
            "temperature": 0.2,
        },
        "gpt-3.5-turbo": {
            "provider": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "max_tokens": 4096,
            "temperature": 0.2,
        },
        # Anthropic 模型
        "claude-3-opus-20240229": {
            "provider": "anthropic",
            "api_key_env": "ANTHROPIC_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.2,
        },
        "claude-3-sonnet-20240229": {
            "provider": "anthropic",
            "api_key_env": "ANTHROPIC_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.2,
        },
        # 本地模型
        "local": {
            "provider": "local",
            "base_url": os.getenv("LOCAL_LLM_URL", "http://localhost:8000"),
            "max_tokens": 4096,
            "temperature": 0.2,
        },
    }

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        初始化 LLM 评估器

        Args:
            model: 模型名称（默认 gpt-4-turbo）
            cache_dir: 缓存目录（默认 ./cache/llm）
            use_cache: 是否使用缓存
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.model = model
        self.use_cache = use_cache
        self.timeout = timeout
        self.max_retries = max_retries

        # 设置 logger
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        # 获取模型配置
        if model not in self.MODEL_CONFIGS:
            self.logger.error(f"不支持的模型: {model}. 支持的模型: {list(self.MODEL_CONFIGS.keys())}")
            raise ValueError(f"不支持的模型: {model}. 支持的模型: {list(self.MODEL_CONFIGS.keys())}")

        self.model_config = self.MODEL_CONFIGS[model]
        self.provider = self.model_config["provider"]

        # 检查 API 密钥
        self.api_key = self._get_api_key()

        # 设置缓存
        self.cache_dir = cache_dir or "./cache/llm"
        if use_cache:
            os.makedirs(self.cache_dir, exist_ok=True)

        # 可用性标记
        self.available = self._check_initial_availability()

    def _check_initial_availability(self) -> bool:
        """
        检查初始可用性

        Returns:
            是否可用
        """
        # 如果是本地模型，总是认为可用
        if self.provider == "local":
            return True

        # 检查 API 密钥是否配置
        if not self.api_key:
            self.logger.warning(f"API 密钥未配置")
            return False

        return True

    def _get_api_key(self) -> Optional[str]:
        """
        获取 API 密钥

        Returns:
            API 密钥
        """
        if self.provider == "local":
            return None

        env_var = self.model_config.get("api_key_env")
        if not env_var:
            raise ValueError(f"模型 {self.model} 未配置 api_key_env")

        api_key = os.getenv(env_var)

        if not api_key or api_key.startswith("your_"):
            self.logger.warning(
                f"⚠️  API 密钥未配置: {env_var}\n"
                f"请在环境变量中设置: {env_var}=your_api_key_here"
            )
            return None

        return api_key

    def _get_cache_path(self, prompt: str, **kwargs) -> str:
        """
        生成缓存路径

        基于输入内容生成唯一的缓存文件名

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Returns:
            缓存文件路径
        """
        # 生成唯一键
        content = f"{self.model}{prompt}{json.dumps(kwargs, sort_keys=True)}"
        cache_key = hashlib.md5(content.encode()).hexdigest()

        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _load_from_cache(self, cache_path: str) -> Optional[Dict]:
        """
        从缓存加载结果

        Args:
            cache_path: 缓存文件路径

        Returns:
            缓存的结果，如果不存在则返回 None
        """
        if not self.use_cache:
            return None

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                self.logger.debug(f"从缓存加载: {cache_path}")
                return cached
            except Exception as e:
                self.logger.warning(f"缓存读取失败: {e}")

        return None

    def _save_to_cache(self, cache_path: str, result: Dict):
        """
        保存结果到缓存

        Args:
            cache_path: 缓存文件路径
            result: 结果字典
        """
        if not self.use_cache:
            return

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"保存到缓存: {cache_path}")
        except Exception as e:
            self.logger.warning(f"缓存保存失败: {e}")

    @abstractmethod
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """
        调用 LLM API（子类实现）

        Args:
            prompt: 提示词
            **kwargs: 额外参数

        Returns:
            LLM 响应文本
        """
        pass

    def evaluate(
        self,
        prompt: str,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        评估函数

        Args:
            prompt: 评估提示词
            use_cache: 是否使用缓存（覆盖实例设置）
            **kwargs: 额外参数

        Returns:
            评估结果字典 {
                "response": str,  # LLM 原始响应
                "parsed": Dict,   # 解析后的结果
                "model": str,     # 使用的模型
                "timestamp": str, # 评估时间
                "cached": bool,   # 是否来自缓存
            }
        """
        use_cache = use_cache if use_cache is not None else self.use_cache

        # 检查缓存
        cache_path = self._get_cache_path(prompt, **kwargs)
        if use_cache:
            cached_result = self._load_from_cache(cache_path)
            if cached_result:
                cached_result["cached"] = True
                return cached_result

        # 调用 LLM
        self.logger.info(f"调用 LLM: {self.model}")
        try:
            response = self._call_llm(prompt, **kwargs)

            # 尝试解析 JSON 响应
            parsed = self._parse_response(response)

            result = {
                "response": response,
                "parsed": parsed,
                "model": self.model,
                "provider": self.provider,
                "timestamp": datetime.now().isoformat(),
                "cached": False,
            }

            # 保存到缓存
            if use_cache:
                self._save_to_cache(cache_path, result)

            return result

        except Exception as e:
            self.logger.error(f"LLM 调用失败: {e}")
            raise

    def _parse_response(self, response: str) -> Dict:
        """
        解析 LLM 响应

        尝试从响应中提取 JSON 内容

        Args:
            response: LLM 响应文本

        Returns:
            解析后的字典
        """
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        import re

        # 查找 JSON 代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 查找花括号内容
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # 无法解析，返回原始文本
        return {
            "raw_text": response,
            "parsed": False,
        }

    def check_availability(self) -> Dict[str, bool]:
        """
        检查 LLM 服务可用性

        Returns:
            各服务状态 {
                "api_key_configured": bool,
                "api_accessible": bool,
                "model_available": bool,
            }
        """
        status = {
            "api_key_configured": self.api_key is not None,
            "api_accessible": False,
            "model_available": False,
            "available": False,
        }

        if not status["api_key_configured"] and self.provider != "local":
            return status

        try:
            # 发送简单测试请求
            test_response = self._call_llm("测试", max_tokens=10)
            status["api_accessible"] = True
            status["model_available"] = bool(test_response)
            status["available"] = True
        except Exception as e:
            self.logger.warning(f"服务不可用: {e}")

        return status


class OpenAIEvaluator(LLMEvaluator):
    """OpenAI GPT 评估器"""

    def _call_llm(self, prompt: str, **kwargs) -> str:
        """调用 OpenAI API"""
        try:
            import openai
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        client = openai.OpenAI(api_key=self.api_key)

        max_tokens = kwargs.get("max_tokens", self.model_config["max_tokens"])
        temperature = kwargs.get("temperature", self.model_config["temperature"])

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content


class AnthropicEvaluator(LLMEvaluator):
    """Anthropic Claude 评估器"""

    def _call_llm(self, prompt: str, **kwargs) -> str:
        """调用 Anthropic API"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        max_tokens = kwargs.get("max_tokens", self.model_config["max_tokens"])

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text


class LocalLLMEvaluator(LLMEvaluator):
    """本地 LLM 评估器"""

    def _call_llm(self, prompt: str, **kwargs) -> str:
        """调用本地 LLM API"""
        try:
            import requests
        except ImportError:
            raise ImportError("请安装 requests: pip install requests")

        base_url = self.model_config["base_url"]
        url = f"{base_url}/v1/chat/completions"

        payload = {
            "model": kwargs.get("local_model", "default"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.model_config["max_tokens"]),
            "temperature": kwargs.get("temperature", self.model_config["temperature"]),
        }

        response = requests.post(
            url,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()
        result = response.json()

        return result["choices"][0]["message"]["content"]


def create_llm_evaluator(
    model: str = "gpt-4-turbo",
    **kwargs
) -> LLMEvaluator:
    """
    工厂函数：创建 LLM 评估器

    Args:
        model: 模型名称
        **kwargs: 额外参数

    Returns:
        LLMEvaluator 实例

    Examples:
        >>> # 使用 GPT-4-turbo
        >>> evaluator = create_llm_evaluator("gpt-4-turbo")
        >>>
        >>> # 使用 Claude 3 Sonnet
        >>> evaluator = create_llm_evaluator("claude-3-sonnet-20240229")
        >>>
        >>> # 使用本地模型
        >>> evaluator = create_llm_evaluator("local", local_model="llama-3-70b")
    """
    model_configs = LLMEvaluator.MODEL_CONFIGS

    if model not in model_configs:
        raise ValueError(f"不支持的模型: {model}")

    provider = model_configs[model]["provider"]

    # 根据提供商创建对应的评估器
    if provider == "openai":
        return OpenAIEvaluator(model, **kwargs)
    elif provider == "anthropic":
        return AnthropicEvaluator(model, **kwargs)
    elif provider == "local":
        return LocalLLMEvaluator(model, **kwargs)
    else:
        raise ValueError(f"不支持的提供商: {provider}")


# 导出
__all__ = [
    "LLMEvaluator",
    "OpenAIEvaluator",
    "AnthropicEvaluator",
    "LocalLLMEvaluator",
    "create_llm_evaluator",
]
