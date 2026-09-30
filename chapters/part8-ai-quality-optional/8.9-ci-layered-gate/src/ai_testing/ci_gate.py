"""分层 CI 门禁：把单元、契约、评测、安全和性能结果合并成一个发布判定。

判定规则（失败关闭）：
1. 必需层（required=True）未通过 → 不放行；
2. required_layers 里声明的层没有结果（报告没生成）→ 不放行，缺报告不等于通过；
3. 同一测试的历史结果既有成功又有失败（flaky）→ 不放行，要先查原因，不能重跑到绿了事。
可选层（required=False）失败只记录，不阻断。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LayerResult:
    """一层测试证据：层名、是否通过、说明，以及失败时是否阻断发布。"""

    name: str
    passed: bool
    details: str = ""
    required: bool = True


@dataclass(frozen=True)
class GateReport:
    """门禁结论：passed 为真才放行；其余字段说明不放行的原因。"""

    passed: bool
    failed_layers: tuple[str, ...]
    flaky_tests: tuple[str, ...]
    missing_layers: tuple[str, ...] = ()


def flaky_tests(history: dict[str, list[bool]]) -> tuple[str, ...]:
    """返回历史结果里既有 True 又有 False 的测试名，按名称排序。"""
    return tuple(sorted(name for name, runs in history.items() if True in runs and False in runs))


def evaluate_gate(
    layers: list[LayerResult],
    test_history: dict[str, list[bool]] | None = None,
    required_layers: tuple[str, ...] = (),
) -> GateReport:
    """汇总各层结果，给出发布判定。

    required_layers 是 CI 约定必须出现的层名；任何一层没有结果都算缺失并阻断，
    避免“某份报告没生成就当作全部通过”。
    """
    reported = {layer.name for layer in layers}
    missing = tuple(name for name in required_layers if name not in reported)
    failed = tuple(layer.name for layer in layers if layer.required and not layer.passed)
    flaky = flaky_tests(test_history or {})
    return GateReport(not failed and not missing and not flaky, failed, flaky, missing)
