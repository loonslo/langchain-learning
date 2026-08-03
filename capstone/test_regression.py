"""
capstone/test_regression.py · pytest 回归（护城河：测试主场）
==========================================================
整合 day42：把评测集变成 pytest 用例，每次改完 RAG 一条命令跑回归。
RAG 输出有随机性，用宽松断言（含关键词 / 是否拒答），并靠 temperature=0 提升可复现。
运行：pytest capstone/test_regression.py -v
==========================================================
"""

import json
import pytest

from . import config as C
from .cache import AnswerCache
from .contracts import AssistRequest
from .evaluation import _refused
from .knowledge_base import KnowledgeBase
from .permissions import User
from .service import AssistantService

CASES = (
    json.loads(C.EVAL_SET.read_text(encoding="utf-8")) if C.EVAL_SET.exists() else []
)


@pytest.fixture(scope="module")
def service():
    kb = KnowledgeBase().build()

    class Registry:
        def get(self, tenant_id: str):
            assert tenant_id == kb.tenant_id
            return kb

    return AssistantService(
        Registry(),
        cache=AnswerCache(max_entries=1024, ttl_seconds=60),
    )


@pytest.mark.parametrize("case", CASES, ids=[c.get("id", c["question"]) for c in CASES])
def test_case(service, case):
    identity = User(
        case.get("user_id", "eval-reader"),
        tenant_id=case.get("tenant_id", "default"),
        dept=case.get("dept", ""),
        roles=frozenset(case.get("roles", ["public"])),
    )
    result = service.assist(
        AssistRequest(
            question=case["question"],
            request_id=f"regression-{case.get('id', 'case')}",
            mode=case.get("mode", "knowledge"),
        ),
        identity,
    )
    ans = result.answer
    if case.get("should_refuse"):
        assert _refused(ans), f"应拒答却答了：{ans[:60]}"
        assert not result.citations, "拒答不应附加无关引用"
    else:
        for kw in case.get("keywords", []):
            assert kw in ans, f"答案缺关键词「{kw}」：{ans[:60]}"
        expected_sources = set(case.get("expected_sources", []))
        actual_sources = {citation.source_id for citation in result.citations}
        assert expected_sources.issubset(actual_sources)


if __name__ == "__main__":
    print(
        f"共有 {len(CASES)} 条回归用例，用 "
        "`pytest capstone/test_regression.py -v` 跑统一 AssistantService 路径"
    )
