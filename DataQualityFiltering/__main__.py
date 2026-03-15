#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataQualityFiltering - 统一的医学评估框架
主 CLI 入口点

使用示例:
    # 数据质量评估
    python -m DataQualityFiltering data-quality check --input data.json
    python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

    # Agent 性能评估
    python -m DataQualityFiltering agent-eval evaluate --input agent_results.json
    python -m DataQualityFiltering agent-eval batch --input results.json --max-workers 8

    # 查看帮助
    python -m DataQualityFiltering --help
    python -m DataQualityFiltering data-quality --help
    python -m DataQualityFiltering agent-eval --help
"""

import argparse
import sys
from pathlib import Path


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="DataQualityFiltering - 统一的医学评估框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 数据质量评估
  python -m DataQualityFiltering data-quality check --input data.json
  python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

  # Agent 性能评估
  python -m DataQualityFiltering agent-eval evaluate --input agent_results.json
  python -m DataQualityFiltering agent-eval batch --input results.json --max-workers 8

  # 查看版本
  python -m DataQualityFiltering --version
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )

    # 子命令
    subparsers = parser.add_subparsers(
        dest="subsystem",
        help="选择子系统",
        metavar="SUBSYSTEM"
    )

    # ============================================================================
    # 数据质量评估子系统
    # ============================================================================
    data_quality_parser = subparsers.add_parser(
        "data-quality",
        help="数据质量评估子系统",
        description="验证和过滤医学对话数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查医学对话
  python -m DataQualityFiltering data-quality check --input data.json

  # 过滤低质量数据
  python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

  # 运行完整管道
  python -m DataQualityFiltering data-quality pipeline --input data.json --mode semi_auto
        """
    )

    data_quality_subparsers = data_quality_parser.add_subparsers(
        dest="command",
        help="数据质量命令",
        metavar="COMMAND"
    )

    # check 命令
    check_parser = data_quality_subparsers.add_parser(
        "check",
        help="检查医学对话数据",
        description="检查数据是否符合医学对话格式要求"
    )
    check_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    check_parser.add_argument(
        "--output",
        help="输出报告文件路径（可选）"
    )

    # filter 命令
    filter_parser = data_quality_subparsers.add_parser(
        "filter",
        help="过滤低质量数据",
        description="根据质量分数过滤数据"
    )
    filter_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    filter_parser.add_argument(
        "--threshold",
        type=float,
        default=3.5,
        help="质量阈值（默认: 3.5）"
    )
    filter_parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )

    # pipeline 命令
    pipeline_parser = data_quality_subparsers.add_parser(
        "pipeline",
        help="运行完整的数据质量管道",
        description="运行完整的质量评估和过滤管道"
    )
    pipeline_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    pipeline_parser.add_argument(
        "--mode",
        choices=["human", "semi_auto", "both"],
        default="semi_auto",
        help="审查模式（默认: semi_auto）"
    )
    pipeline_parser.add_argument(
        "--threshold",
        type=float,
        default=3.5,
        help="质量阈值（默认: 3.5）"
    )
    pipeline_parser.add_argument(
        "--output-dir",
        help="输出目录（可选）"
    )

    # ============================================================================
    # Agent 性能评估子系统
    # ============================================================================
    agent_eval_parser = subparsers.add_parser(
        "agent-eval",
        help="Agent 性能评估子系统",
        description="评估 Agent 在医学任务上的表现",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 评估单个任务
  python -m DataQualityFiltering agent-eval evaluate --input task.json

  # 批量评估
  python -m DataQualityFiltering agent-eval batch --input tasks.json --max-workers 8

  # 生成报告
  python -m DataQualityFiltering agent-eval report --input results.json --output report.md
        """
    )

    agent_eval_subparsers = agent_eval_parser.add_subparsers(
        dest="command",
        help="Agent 评估命令",
        metavar="COMMAND"
    )

    # evaluate 命令
    ae_eval_parser = agent_eval_subparsers.add_parser(
        "evaluate",
        help="评估 Agent 回答",
        description="评估 Agent 在医学任务上的回答质量"
    )
    ae_eval_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    ae_eval_parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )
    ae_eval_parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="LLM 模型（默认: gpt-4-turbo）"
    )

    # batch 命令
    ae_batch_parser = agent_eval_subparsers.add_parser(
        "batch",
        help="批量评估",
        description="批量评估多个 Agent 回答"
    )
    ae_batch_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    ae_batch_parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )
    ae_batch_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="最大并发数（默认: 4）"
    )
    ae_batch_parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="LLM 模型（默认: gpt-4-turbo）"
    )

    # report 命令
    ae_report_parser = agent_eval_subparsers.add_parser(
        "report",
        help="生成评估报告",
        description="从评估结果生成 Markdown 报告"
    )
    ae_report_parser.add_argument(
        "--input",
        required=True,
        help="评估结果 JSON 文件路径"
    )
    ae_report_parser.add_argument(
        "--output",
        help="报告输出路径（可选）"
    )

    # 解析参数
    args = parser.parse_args()

    # 如果没有提供子命令，显示帮助
    if not args.subsystem:
        parser.print_help()
        return 0

    # 路由到对应的处理器
    if args.subsystem == "data-quality":
        return _handle_data_quality(args)
    elif args.subsystem == "agent-eval":
        return _handle_agent_eval(args)
    else:
        parser.print_help()
        return 1


def _handle_data_quality(args):
    """处理数据质量评估命令"""
    if not args.command:
        print("错误: 请指定数据质量命令（check, filter, pipeline）")
        print("使用 --help 查看帮助")
        return 1

    # 导入数据质量模块
    try:
        from .data_quality.cli import main as dq_main
        from .data_quality.check_medical_dialogue import main as check_main

        if args.command == "check":
            # 调用医学对话检查
            sys.argv = [
                "check_medical_dialogue",
                "--input", args.input,
            ]
            if args.output:
                sys.argv.extend(["--output", args.output])

            return check_main()

        elif args.command == "filter":
            # 调用过滤功能
            from .data_quality import QualityFilter, FilterConfig
            import json

            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = FilterConfig(min_quality_score=args.threshold)
            filter_engine = QualityFilter(config)

            # 过滤数据
            filtered = [task for task in data if filter_engine.calculate_quality_score(task) >= args.threshold]

            # 保存结果
            output_file = args.output or args.input.replace(".json", "_filtered.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(filtered, f, ensure_ascii=False, indent=2)

            print(f"✅ 过滤完成: {len(filtered)}/{len(data)} 个任务通过")
            print(f"📄 结果保存到: {output_file}")
            return 0

        elif args.command == "pipeline":
            # 调用完整管道
            sys.argv = [
                "cli",
                "--tasks-path", args.input,
                "--review-mode", args.mode,
                "--threshold", str(args.threshold),
            ]
            if args.output_dir:
                sys.argv.extend(["--output-dir", args.output_dir])

            return dq_main()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _handle_agent_eval(args):
    """处理 Agent 评估命令"""
    if not args.command:
        print("错误: 请指定 Agent 评估命令（evaluate, batch, report）")
        print("使用 --help 查看帮助")
        return 1

    # 导入 Agent 评估模块
    try:
        from .agent_evaluation.cli import main as ae_main

        # 构建命令行参数
        sys.argv = [
            "evaluate_agent",
            "--input", args.input,
        ]

        if args.command == "evaluate":
            if args.output:
                sys.argv.extend(["--output", args.output])
            sys.argv.extend(["--model", args.model])

        elif args.command == "batch":
            if args.output:
                sys.argv.extend(["--output", args.output])
            sys.argv.extend(["--max-workers", str(args.max_workers)])
            sys.argv.extend(["--model", args.model])

        elif args.command == "report":
            # TODO: 实现报告生成
            print("⚠️  报告生成功能即将推出")
            return 0

        return ae_main()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
