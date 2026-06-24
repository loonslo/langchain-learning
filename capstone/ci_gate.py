"""
capstone/ci_gate.py · CI 评测门禁（Day58）★最硬的作品点
==========================================================
把"测试转 AI"讲得再多，不如一条 CI：改坏 prompt → 评测红 → PR 被挡住。

这个脚本在 CI 里跑：建库 → 跑评测 → 把质量指标和阈值比 →
达标 exit 0（绿灯，允许合并）；跌破阈值 exit 1（红灯，GitHub 拦 merge）。

阈值就是你的质量底线，写进代码、进 git、可回溯。谁想合并一个让幻觉率
飙升的改动，CI 第一个不答应——这正是评测从"跑一次出个数"变成"质量门禁"。
==========================================================
"""

import sys

import config as C
from knowledge_base import KnowledgeBase
from evaluation import run

# 质量门禁阈值（按你的评测集和业务容忍度定，进 git 可回溯）
THRESHOLDS = {
    "拒答正确率": 1.0,     # 该拒答的必须全拒答（防幻觉底线）
    "关键词命中率": 0.7,   # 事实题至少答对 70%
    "最多失败数": 3,       # 失败用例不超过 3 条
}


def _ratio(s: str) -> float:
    """把评测返回的 'a/b' 解析成比率；'n/a' 当作满分（该类无样本）。"""
    if s == "n/a":
        return 1.0
    a, b = s.split("/")
    return int(a) / int(b) if int(b) else 1.0


def gate() -> int:
    kb = KnowledgeBase().build()
    metrics = run(kb)
    print("评测指标：", metrics)

    failures = []
    refuse = _ratio(metrics["拒答正确率"])
    if refuse < THRESHOLDS["拒答正确率"]:
        failures.append(f"拒答正确率 {refuse:.2f} < {THRESHOLDS['拒答正确率']}")

    kw = _ratio(metrics["关键词命中率"])
    if kw < THRESHOLDS["关键词命中率"]:
        failures.append(f"关键词命中率 {kw:.2f} < {THRESHOLDS['关键词命中率']}")

    if metrics["失败数"] > THRESHOLDS["最多失败数"]:
        failures.append(f"失败数 {metrics['失败数']} > {THRESHOLDS['最多失败数']}")

    if failures:
        print("\n[FAIL] 评测门禁未通过：")
        for f in failures:
            print("  -", f)
        print("PR 应被拦截。修复后重跑。")
        return 1

    print("\n[PASS] 评测门禁通过，允许合并。")
    return 0


if __name__ == "__main__":
    sys.exit(gate())
