"""把单元、契约、评测、安全和性能结果合并成分层 CI 门禁。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LayerResult:
    name: str
    passed: bool
    details: str = ""
    required: bool = True


@dataclass(frozen=True)
class GateReport:
    passed: bool
    failed_layers: tuple[str, ...]
    flaky_tests: tuple[str, ...]


def flaky_tests(history: dict[str, list[bool]]) -> tuple[str, ...]:
    return tuple(sorted(name for name, runs in history.items() if True in runs and False in runs))


def evaluate_gate(
    layers: list[LayerResult],
    test_history: dict[str, list[bool]] | None = None,
) -> GateReport:
    failed = tuple(
        layer.name for layer in layers if layer.required and not layer.passed
    )
    flaky = flaky_tests(test_history or {})
    return GateReport(not failed and not flaky, failed, flaky)
