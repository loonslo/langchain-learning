"""
端到端 smoke 与可审计改进闭环
==========================================================
当前驱动覆盖 build → ask → eval，不包含上传 API、权限、引用校验或 trace，不能把这次
smoke 描述成完整生产 E2E。生产闭环应固定评测集版本与基线，只改一个主要变量，
记录实验配置和置信区间，检查关键分群没有退化，再经灰度和线上监控决定是否推广。
==========================================================
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from _capstone_driver import (
    DEFAULT_TIMEOUT_SECONDS,
    DriverError,
    cli_error,
    configure_logging,
    positive_timeout,
    require_file,
    run_python,
)

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "capstone" / "main.py"
REPORT = ROOT / "capstone" / "data" / "eval_report.md"
FAILURES = ROOT / "capstone" / "data" / "failures.json"

IMPROVEMENT_LOOP = """
改进记录至少包含：
1. 基线：代码、数据、prompt、模型、检索配置版本及分群指标。
2. 失败：原始输入、预期、实际输出、检索证据和可复现的归因。
3. 假设：一个可证伪的主要原因；一次实验只改变一个主要变量。
4. 对照：重复运行并报告总体与关键分群变化，不能只看目标 case。
5. 发布：评审、灰度、监控阈值与自动回滚条件。
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default="知识库讲了什么？")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--timeout", type=positive_timeout, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    if not args.question.strip():
        parser.error("--question 不能为空")

    started_at = time.time()
    try:
        require_file(MAIN, "capstone CLI")
        steps = []
        if not args.skip_build:
            steps.append(("重建知识库", ["build"]))
        steps.extend(
            (
                ("知识库问答", ["ask", args.question.strip()]),
                ("RAG 评测", ["eval"]),
            )
        )
        for label, command_args in steps:
            run_python(
                ["-m", "capstone.main", *command_args],
                cwd=ROOT,
                label=label,
                timeout=args.timeout,
            )
        for output, label in ((REPORT, "评测报告"), (FAILURES, "失败样本")):
            require_file(output, label)
            if output.stat().st_mtime < started_at - 1:
                raise DriverError(f"{label}不是本次运行生成的：{output}")
    except DriverError as exc:
        return cli_error(exc)

    print(f"最小 smoke 通过。失败样本：{FAILURES}")
    print(IMPROVEMENT_LOOP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
