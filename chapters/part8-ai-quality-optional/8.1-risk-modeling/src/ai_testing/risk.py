"""把 AI 应用测试从“凭感觉”变成可排序的风险清单。"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Risk:
    """一条测试风险：impact（影响）和 likelihood（可能性）各 1–5 分，control 写明用什么测试或机制控制它。"""

    risk_id: str
    area: str
    scenario: str
    impact: int
    likelihood: int
    control: str

    def __post_init__(self) -> None:
        if not self.risk_id.strip() or not self.area.strip():
            raise ValueError("risk_id 和 area 不能为空")
        if not 1 <= self.impact <= 5 or not 1 <= self.likelihood <= 5:
            raise ValueError("impact 和 likelihood 必须在 1–5 之间")

    @property
    def score(self) -> int:
        """风险分 = impact × likelihood，范围 1–25。"""
        return self.impact * self.likelihood

    @property
    def level(self) -> str:
        """按风险分分级：≥16 critical，≥9 high，≥4 medium，其余 low。"""
        if self.score >= 16:
            return "critical"
        if self.score >= 9:
            return "high"
        if self.score >= 4:
            return "medium"
        return "low"


@dataclass
class RiskMatrix:
    """风险清单；risk_id 不能重复。"""

    items: list[Risk] = field(default_factory=list)

    def add(self, risk: Risk) -> None:
        if any(item.risk_id == risk.risk_id for item in self.items):
            raise ValueError(f"重复风险编号：{risk.risk_id}")
        self.items.append(risk)

    def prioritized(self) -> list[Risk]:
        """按风险分从高到低排序，同分按 risk_id 排，保证输出稳定。"""
        return sorted(self.items, key=lambda item: (-item.score, item.risk_id))

    def uncovered_areas(self, required: set[str]) -> set[str]:
        """返回 required 中还没有任何风险条目的领域，用来发现风险分析的空白。"""
        return required - {item.area for item in self.items}
