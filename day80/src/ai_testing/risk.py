"""把 AI 应用测试从“凭感觉”变成可排序的风险清单。"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Risk:
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
        return self.impact * self.likelihood

    @property
    def level(self) -> str:
        if self.score >= 16:
            return "critical"
        if self.score >= 9:
            return "high"
        if self.score >= 4:
            return "medium"
        return "low"


@dataclass
class RiskMatrix:
    items: list[Risk] = field(default_factory=list)

    def add(self, risk: Risk) -> None:
        if any(item.risk_id == risk.risk_id for item in self.items):
            raise ValueError(f"重复风险编号：{risk.risk_id}")
        self.items.append(risk)

    def prioritized(self) -> list[Risk]:
        return sorted(self.items, key=lambda item: (-item.score, item.risk_id))

    def uncovered_areas(self, required: set[str]) -> set[str]:
        return required - {item.area for item in self.items}
