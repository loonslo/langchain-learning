"""L5.7 扩展 · CI 分层门禁 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/ci_gate.py。实现下面两个函数，然后运行：

    python chapters/part8-ai-quality-optional/8.9-ci-layered-gate/gate/gate_check.py
"""

from __future__ import annotations


def flaky_tests(history: dict[str, list[bool]]) -> tuple[str, ...]:
    """返回历史里既有 True 又有 False 的测试名，按名称排序。"""
    raise NotImplementedError("实现 flaky 检测")


def evaluate_gate(
    layers: list[dict],
    test_history: dict[str, list[bool]] | None = None,
    required_layers: tuple[str, ...] = (),
) -> dict:
    """失败关闭的分层门禁。

    layers 每项 {"name","passed","required"}。
    返回 {"passed","failed_layers","flaky_tests","missing_layers"}：
    - 必需层失败 -> failed_layers；
    - required_layers 有层没报告 -> missing_layers；
    - 有 flaky -> 阻断；
    - 可选层失败只记录在 failed_layers？不，failed_layers 只放必需层失败；
    - 三者都空才 passed=True。
    """
    raise NotImplementedError("实现门禁判定")
