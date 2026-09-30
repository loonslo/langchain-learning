"""可版本化的 AI 评测数据集：先校验数据，再交给评测器。"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class EvalCase:
    """一条评测用例。expected_keywords 是答案应包含的关键词，expected_sources 是应召回或引用的来源，
    should_refuse=True 表示知识库里没有答案、系统应拒答。
    """

    case_id: str
    question: str
    expected_keywords: tuple[str, ...] = ()
    expected_sources: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    should_refuse: bool = False
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """返回错误列表（空列表表示合法）；非拒答用例至少要有一个 expected_keywords。"""
        errors: list[str] = []
        if not self.case_id.strip():
            errors.append("case_id 不能为空")
        if not self.question.strip():
            errors.append(f"{self.case_id}: question 不能为空")
        if not self.should_refuse and not self.expected_keywords:
            errors.append(f"{self.case_id}: 非拒答用例至少需要一个 expected_keywords")
        return errors


class EvalDataset:
    """带版本号的用例集合；case_id 不能重复。"""

    def __init__(self, cases: list[EvalCase] | None = None, version: str = "v1"):
        self.version = version
        self._cases: dict[str, EvalCase] = {}
        for case in cases or []:
            self.add(case)

    def add(self, case: EvalCase) -> None:
        if case.case_id in self._cases:
            raise ValueError(f"重复 case_id：{case.case_id}")
        self._cases[case.case_id] = case

    def validate(self) -> dict[str, list[str]]:
        """返回 {case_id: 错误列表}，只包含有问题的用例；空字典表示全部合法。"""
        return {
            case.case_id: errors
            for case in self._cases.values()
            if (errors := case.validate())
        }

    def by_tag(self, tag: str) -> list[EvalCase]:
        """返回带指定标签的用例，按加入顺序。"""
        return [case for case in self._cases.values() if tag in case.tags]

    def __len__(self) -> int:
        return len(self._cases)

    def save(self, path: Path) -> None:
        """写成带 version 的 JSON；tuple 字段存为列表。"""
        payload = {
            "version": self.version,
            "cases": [
                {
                    **asdict(case),
                    "expected_keywords": list(case.expected_keywords),
                    "expected_sources": list(case.expected_sources),
                    "tags": list(case.tags),
                }
                for case in self._cases.values()
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "EvalDataset":
        """读取 save 写出的 JSON；可选字段缺失时用默认值，version 缺失时为 v1。"""
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases = [
            EvalCase(
                case_id=item["case_id"],
                question=item["question"],
                expected_keywords=tuple(item.get("expected_keywords", [])),
                expected_sources=tuple(item.get("expected_sources", [])),
                tags=tuple(item.get("tags", [])),
                should_refuse=bool(item.get("should_refuse", False)),
                metadata=dict(item.get("metadata", {})),
            )
            for item in payload.get("cases", [])
        ]
        return cls(cases, version=str(payload.get("version", "v1")))
