"""Agent 工具轨迹测试：验证它做了什么，而不只看最后一句话。"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TraceStep:
    """轨迹里的一步：step 从 1 递增；action 是 tool / retrieve / respond / refuse；
    tool 动作带工具名和是否已审批。arguments 只做记录，本章不校验。
    """

    step: int
    action: str
    tool: str | None = None
    approved: bool = False
    arguments: dict[str, Any] | None = None


@dataclass(frozen=True)
class TrajectoryPolicy:
    """轨迹策略：允许的工具、最大步数、需要审批的写工具。"""

    allowed_tools: frozenset[str]
    max_steps: int = 6
    write_tools: frozenset[str] = frozenset()


def validate_trajectory(steps: list[TraceStep], policy: TrajectoryPolicy) -> list[str]:
    """返回全部违规描述（空列表表示合规）：步数超限、编号不连续、工具不在白名单、写工具未审批、未知动作。"""
    violations: list[str] = []
    if len(steps) > policy.max_steps:
        violations.append(f"超过最大步骤数：{len(steps)} > {policy.max_steps}")

    expected = 1
    for item in steps:
        if item.step != expected:
            violations.append(f"步骤编号不连续：期望 {expected}，收到 {item.step}")
        expected = item.step + 1
        if item.action == "tool":
            if not item.tool or item.tool not in policy.allowed_tools:
                violations.append(f"工具未授权：{item.tool}")
            if item.tool in policy.write_tools and not item.approved:
                violations.append(f"写操作缺少审批：{item.tool}")
        elif item.action not in {"retrieve", "respond", "refuse"}:
            violations.append(f"未知动作：{item.action}")
    return violations
