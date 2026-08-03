"""验证项目立项文档、统一契约和最小端到端业务路径。"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from capstone.cache import AnswerCache
from capstone.contracts import AssistRequest, Citation
from capstone.knowledge_base import AnswerResult
from capstone.permissions import User
from capstone.service import AssistantService

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ARTIFACTS = (
    "capstone/docs/project_brief.md",
    "capstone/docs/adr/001-modular-monolith.md",
    "capstone/docs/day51-78-roadmap.md",
    "capstone/docs/acceptance_matrix.md",
    "capstone/contracts.py",
    "capstone/daily_task.py",
    "capstone/service.py",
    "capstone/api_enterprise.py",
    "capstone/evaluation.py",
    "capstone/test_production.py",
    "day51/README.md",
    "day51/src/customer_support/assistant.py",
    "day51/data/knowledge/customer_faq.md",
    "day51/tests/test_assistant.py",
)

GIT_WORKFLOW = """
1. 从用户故事或事故单创建 feature 分支。
2. 先提交失败的验收测试，再提交最小实现。
3. PR 写明风险、验证证据、不包含内容和回滚方式。
4. PR 运行确定性离线门禁；真实模型评测进入 nightly/release。
5. 分支保护要求非作者审批和 required checks 后才能合并。
"""


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def _artifact_checks() -> list[Check]:
    return [
        Check(relative, (ROOT / relative).is_file(), str(ROOT / relative))
        for relative in REQUIRED_ARTIFACTS
    ]


def _walking_skeleton_check() -> Check:
    """不调用模型，证明 API/CLI/评测可复用的业务契约能够贯通。"""

    class FakeKnowledgeBase:
        version = "day51-v1"

        def answer_with_usage(self, question, **_kwargs):
            return AnswerResult(
                f"walking-skeleton：{question}【来源：brief.md】",
                citations=(Citation("brief.md", "brief-1"),),
            )

    class Registry:
        def get(self, tenant_id: str):
            if tenant_id != "acme":
                raise PermissionError("租户不匹配")
            return FakeKnowledgeBase()

    service = AssistantService(
        Registry(),
        cache=AnswerCache(max_entries=4, ttl_seconds=10),
        model_selector=lambda _: "fake-model",
    )
    result = service.assist(
        AssistRequest(
            question="退款规则是什么？",
            request_id="day51-smoke",
            mode="knowledge",
        ),
        User("learner", tenant_id="acme", roles=frozenset({"employee"})),
    )
    passed = (
        result.mode == "knowledge"
        and result.tenant_id == "acme"
        and result.citations == (Citation("brief.md", "brief-1"),)
    )
    return Check(
        "walking skeleton",
        passed,
        "可信身份 → AssistantService → fake knowledge → 结构化引用",
    )


def check_project_baseline() -> list[Check]:
    checks = _artifact_checks()
    try:
        checks.append(_walking_skeleton_check())
    except Exception as exc:
        checks.append(Check("walking skeleton", False, f"{type(exc).__name__}: {exc}"))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checks = check_project_baseline()
    if args.json:
        print(
            json.dumps(
                [asdict(check) for check in checks], ensure_ascii=False, indent=2
            )
        )
    else:
        print("===== Day51 项目基线 =====")
        for check in checks:
            print(
                f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}"
            )
        print("\n===== 协作与变更边界 =====")
        print(GIT_WORKFLOW)
        print("课程主线：capstone/docs/day51-78-roadmap.md")
    return 1 if any(not check.passed for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
