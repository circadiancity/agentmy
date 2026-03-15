#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refactoring Validation Test Script
验证重构后的系统是否能正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent  # tau2-bench
sys.path.insert(0, str(project_root))


def test_core_imports():
    """测试核心模块导入"""
    print("[Core] Testing core module imports...")

    try:
        from DataQualityFiltering.core import (
            LLMEvaluator,
            BaseEvaluator,
            BaseReviewer,
            BaseConfig,
            create_llm_evaluator,
        )
        print("  [OK] Core module imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Core module imports failed: {e}")
        return False


def test_data_quality_imports():
    """测试数据质量评估模块导入"""
    print("\n[Data Quality] Testing data quality module imports...")

    try:
        from DataQualityFiltering.data_quality import (
            DataQualityPipeline,
            QualityFilter,
            FilterConfig,
            MedicalDialogueValidator,
        )
        print("  [OK] Data quality module imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Data quality module imports failed: {e}")
        return False


def test_agent_evaluation_imports():
    """测试 Agent 评估模块导入"""
    print("\n[Agent Evaluation] Testing agent evaluation module imports...")

    try:
        from DataQualityFiltering.agent_evaluation import (
            AgentEvaluationPipeline,
            MedicalAgentReviewer,
            ClinicalAccuracyEvaluator,
            DialogueFluencyEvaluator,
            SafetyEmpathyEvaluator,
        )
        print("  [OK] Agent evaluation module imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Agent evaluation module imports failed: {e}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n[Compatibility] Testing backward compatibility...")

    try:
        # 测试旧的导入路径
        from DataQualityFiltering import DataQualityPipeline
        print("  [OK] Backward compatibility test passed (old import path works)")
        return True
    except Exception as e:
        print(f"  [WARN] Backward compatibility warning: {e}")
        return False


def test_documentation_exists():
    """测试文档文件是否存在"""
    print("\n[Documentation] Testing documentation files...")

    docs = [
        "README.md",
        "QUICKSTART.md",
        "REFACTORING_SUMMARY.md",
        "data_quality/README.md",
        "agent_evaluation/README.md",
        "examples/sample_agent_evaluation.json",
    ]

    all_exist = True
    for doc in docs:
        path = project_root / doc
        if path.exists():
            print(f"  [OK] {doc}")
        else:
            print(f"  [FAIL] {doc} does not exist")
            all_exist = False

    return all_exist


def main():
    """运行所有测试"""
    print("=" * 70)
    print("DataQualityFiltering 2.0.0 - Refactoring Validation Test")
    print("=" * 70)

    results = []

    # 运行测试
    results.append(test_core_imports())
    results.append(test_data_quality_imports())
    results.append(test_agent_evaluation_imports())
    results.append(test_backward_compatibility())
    results.append(test_documentation_exists())

    # 总结
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"[SUCCESS] All tests passed! ({passed}/{total})")
        print("\n[SUCCESS] DataQualityFiltering 2.0.0 refactoring completed!")
        return 0
    else:
        print(f"[WARN] Some tests failed: {passed}/{total} passed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
