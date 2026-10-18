"""L4.11 扩展 · Agent 轨迹测试 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/trajectory.py。实现 validate_trajectory，然后运行：

    python chapters/part8-ai-quality-optional/8.6-agent-trajectory-testing/gate/gate_check.py
"""

from __future__ import annotations


def validate_trajectory(steps: list[dict], policy: dict) -> list[str]:
    """返回全部违规（空列表=合规）。

    steps 每项 {"step","action","tool","approved"}；
    policy {"allowed_tools","max_steps","write_tools"}。
    规则：
    - 步数 > max_steps；
    - step 必须从 1 连续递增；
    - action=tool 时 tool 必须在白名单；写工具未审批；
    - action 只能是 tool/retrieve/respond/refuse。
    """
    raise NotImplementedError("实现轨迹校验")
